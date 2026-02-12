from __future__ import annotations

from sqlalchemy import text


def _get_table_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def ensure_sqlite_schema_compatibility(engine) -> None:
    """
    Lightweight migration helper for local SQLite usage.
    Adds missing columns required by the current runtime models.
    """
    if engine.dialect.name != "sqlite":
        return

    required_lead_columns = {
        "segment": "TEXT",
        "stage": "TEXT DEFAULT 'NEW'",
        "outcome": "TEXT",
        "icp_score": "REAL DEFAULT 0.0",
        "heat_score": "REAL DEFAULT 0.0",
        "tier": "TEXT DEFAULT 'Tier D'",
        "heat_status": "TEXT DEFAULT 'Cold'",
        "next_best_action": "TEXT",
        "icp_breakdown": "TEXT DEFAULT '{}'",
        "heat_breakdown": "TEXT DEFAULT '{}'",
        "details": "TEXT DEFAULT '{}'",
    }
    required_project_columns = {
        "name": "TEXT",
        "description": "TEXT",
        "status": "TEXT DEFAULT 'Planning'",
        "lead_id": "TEXT",
        "due_date": "TIMESTAMP",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    }
    required_admin_settings_columns = {
        "key": "TEXT",
        "value_json": "TEXT NOT NULL DEFAULT '{}'",
        "updated_at": "TIMESTAMP",
    }

    with engine.begin() as connection:
        lead_columns = _get_table_columns(connection, "leads")
        if lead_columns:
            for column_name, column_type in required_lead_columns.items():
                if column_name not in lead_columns:
                    connection.execute(
                        text(f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}")
                    )

            # Copy legacy scores into the new columns when they are still empty.
            connection.execute(
                text(
                    """
                    UPDATE leads
                    SET icp_score = COALESCE(NULLIF(icp_score, 0), demographic_score),
                        heat_score = COALESCE(NULLIF(heat_score, 0), behavioral_score + intent_score),
                        tier = COALESCE(NULLIF(tier, ''), 'Tier D'),
                        heat_status = COALESCE(NULLIF(heat_status, ''), 'Cold'),
                        icp_breakdown = CASE
                            WHEN icp_breakdown IS NULL OR icp_breakdown = '' OR icp_breakdown = '{}' THEN score_breakdown
                            ELSE icp_breakdown
                        END
                    """
                )
            )

        project_columns = _get_table_columns(connection, "projects")
        if project_columns:
            for column_name, column_type in required_project_columns.items():
                if column_name not in project_columns:
                    connection.execute(
                        text(f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}")
                    )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status)")
            )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS ix_projects_due_date ON projects (due_date)")
            )

        settings_columns = _get_table_columns(connection, "admin_settings")
        if not settings_columns:
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS admin_settings (
                        id INTEGER PRIMARY KEY,
                        key TEXT UNIQUE NOT NULL,
                        value_json TEXT NOT NULL DEFAULT '{}',
                        updated_at TIMESTAMP
                    )
                    """
                )
            )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS ix_admin_settings_key ON admin_settings (key)")
            )
        else:
            for column_name, column_type in required_admin_settings_columns.items():
                if column_name not in settings_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE admin_settings ADD COLUMN {column_name} {column_type}"
                        )
                    )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_admin_settings_key ON admin_settings (key)"
                )
            )
