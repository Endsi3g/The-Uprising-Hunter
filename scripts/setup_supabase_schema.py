import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure src is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.core.database import Base, engine, DATABASE_URL

print(f"Applying schema to: {DATABASE_URL.split('@')[-1]}")

def setup_schema():
    try:
        # Create all tables defined in models
        print("Creating tables...")
        # This will create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Tables created/verified successfully.")

        tables_to_secure = ["leads", "tasks", "opportunities", "projects", "appointments"]
        
        with engine.begin() as conn:
            for table in tables_to_secure:
                print(f"Configuring RLS on {table}...")
                
                # 1. Enable RLS
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
                
                # 2. Create Policy for Anon (Public Access)
                # Drop existing policies to avoid conflicts during re-runs
                conn.execute(text(f"DROP POLICY IF EXISTS \"Enable access for anon\" ON {table};"))
                conn.execute(text(f"DROP POLICY IF EXISTS \"Enable access for service_role\" ON {table};"))
                
                # Create Anon Policy (Allow All for now, as frontend uses anon key)
                conn.execute(text(f"""
                    CREATE POLICY "Enable access for anon"
                    ON {table}
                    FOR ALL
                    TO anon
                    USING (true)
                    WITH CHECK (true);
                """))
                
                # Create Service Role Policy (Explicit allow)
                conn.execute(text(f"""
                    CREATE POLICY "Enable access for service_role"
                    ON {table}
                    FOR ALL
                    TO service_role
                    USING (true)
                    WITH CHECK (true);
                """))

        print("RLS policies applied successfully.")
        
    except Exception as e:
        print(f"Error during schema setup: {e}")
        # sys.exit(1) # Don't exit on error to allow partial success inspect

if __name__ == "__main__":
    setup_schema()
