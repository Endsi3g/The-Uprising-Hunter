from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.db_models import DBContentGeneration, DBLead
from ..core.logging import get_logger
from .ollama_service import chat_completion, parse_json_from_text


ALLOWED_CHANNELS = {"email", "call", "dm"}
logger = get_logger(__name__)


def _render_email(lead: DBLead | None, step: int, context: dict[str, Any]) -> tuple[str, str]:
    first_name = (lead.first_name if lead and lead.first_name else "").strip()
    company = ""
    if lead and isinstance(lead.details, dict):
        company = str(lead.details.get("company_name") or "").strip()
    if not company:
        company = str(context.get("company_name") or "votre entreprise").strip()
    pain = str(context.get("pain_point") or "l'optimisation de votre prospection").strip()
    greeting = f"Bonjour {first_name}," if first_name else "Bonjour,"

    if step <= 1:
        subject = f"{first_name}, 15 min pour accelerer {company}" if first_name else f"15 min pour accelerer {company}"
        body = (
            f"{greeting}\n\n"
            f"J'ai identifie une opportunite concrete autour de {pain}.\n"
            "Je peux vous partager un plan actionnable en 15 minutes.\n"
            "Ouvert a un echange cette semaine ?"
        )
    else:
        subject = f"Relance rapide sur {pain}"
        body = (
            f"{greeting}\n\n"
            "Je me permets une relance rapide.\n"
            "Je peux vous envoyer un mini plan personnalise et 2 actions prioritaires.\n"
            "Souhaitez-vous que je vous le partage ?"
        )
    return subject, body


def _render_call_script(lead: DBLead | None, context: dict[str, Any]) -> str:
    first_name = (lead.first_name if lead and lead.first_name else "").strip()
    company = ""
    if lead and isinstance(lead.details, dict):
        company = str(lead.details.get("company_name") or "").strip()
    if not company:
        company = str(context.get("company_name") or "votre structure").strip()
    goal = str(context.get("goal") or "reduire le temps de suivi commercial").strip()
    intro = f"Intro: Bonjour {first_name}, ici [Votre Nom]." if first_name else "Intro: Bonjour, ici [Votre Nom]."
    return (
        f"{intro}\n"
        f"Contexte: J'aide des equipes comme {company} a {goal}.\n"
        "Question de qualification: Comment gerez-vous ce sujet aujourd'hui ?\n"
        "Proposition: Je peux vous montrer un plan en 15 minutes.\n"
        "CTA: Avez-vous un creneau mardi ou mercredi ?"
    )


def _render_dm(lead: DBLead | None, context: dict[str, Any]) -> str:
    first_name = (lead.first_name if lead and lead.first_name else "").strip()
    hook = str(context.get("hook") or "votre activite").strip()
    if first_name:
        return (
            f"Bonjour {first_name}, j'ai remarque {hook}. "
            "On a un playbook concret pour augmenter les RDV qualifies rapidement. "
            "Ouvert a un echange de 10 minutes ?"
        )
    return (
        f"Bonjour, j'ai remarque {hook}. "
        "On a un playbook concret pour augmenter les RDV qualifies rapidement. "
        "Ouvert a un echange de 10 minutes ?"
    )


def _extract_variables(lead: DBLead | None, context: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    if lead:
        keys.extend(["first_name", "last_name", "email"])
    keys.extend(sorted(context.keys()))
    unique: list[str] = []
    for item in keys:
        if item not in unique:
            unique.append(item)
    return unique


def _build_ollama_prompt(
    *,
    channel: str,
    lead: DBLead | None,
    step: int,
    context: dict[str, Any],
) -> str:
    first_name = (lead.first_name if lead and lead.first_name else "").strip()
    last_name = (lead.last_name if lead and lead.last_name else "").strip()
    email = (lead.email if lead and lead.email else "").strip()
    company = ""
    if lead and isinstance(lead.details, dict):
        company = str(lead.details.get("company_name") or "").strip()
    if not company:
        company = str(context.get("company_name") or "").strip()

    base_context = {
        "channel": channel,
        "step": max(1, int(step)),
        "lead": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "company_name": company,
        },
        "context": context,
    }

    if channel == "email":
        schema = '{"subject":"...","body":"..."}'
    elif channel == "call":
        schema = '{"call_script":"..."}'
    else:
        schema = '{"body":"..."}'

    return (
        "Tu es un assistant commercial B2B. Reponds uniquement en JSON valide sans markdown.\n"
        f"Schema attendu: {schema}\n"
        "Ton: professionnel, direct, empathique. Langue: francais.\n"
        "N'invente pas de donnees non presentes dans le contexte.\n"
        f"Contexte: {base_context}"
    )


def _generate_with_ollama(
    *,
    channel: str,
    lead: DBLead | None,
    step: int,
    context: dict[str, Any],
    provider_config: dict[str, Any] | None,
) -> dict[str, Any]:
    config = provider_config or {}
    try:
        max_tokens = int(config.get("max_tokens", 700))
    except (TypeError, ValueError):
        max_tokens = 700
    max_tokens = max(150, min(max_tokens, 2048))
    try:
        temperature = float(config.get("temperature", 0.2))
    except (TypeError, ValueError):
        temperature = 0.2

    content = chat_completion(
        messages=[
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": _build_ollama_prompt(channel=channel, lead=lead, step=step, context=context)},
        ],
        config=config,
        config_model_key="model_content",
        env_model_key="OLLAMA_MODEL_CONTENT",
        temperature=temperature,
        max_tokens=max_tokens,
    )
    parsed = parse_json_from_text(content)
    if isinstance(parsed, dict):
        if channel == "email":
            subject = str(parsed.get("subject") or "").strip()
            body = str(parsed.get("body") or "").strip()
            if subject or body:
                return {
                    "subject": subject or "Message de prospection",
                    "body": body or content.strip(),
                }
        elif channel == "call":
            script = str(parsed.get("call_script") or parsed.get("body") or "").strip()
            if script:
                return {"call_script": script}
        else:
            body = str(parsed.get("body") or "").strip()
            if body:
                return {"body": body}

    if channel == "email":
        return {"subject": "Message de prospection", "body": content.strip()}
    if channel == "call":
        return {"call_script": content.strip()}
    return {"body": content.strip()}


def serialize_content_generation(row: DBContentGeneration) -> dict[str, Any]:
    output = row.output_json or {}
    return {
        "id": row.id,
        "lead_id": row.lead_id,
        "channel": row.channel,
        "step": row.step,
        "template_key": row.template_key,
        "provider": row.provider,
        "subject": output.get("subject"),
        "body": output.get("body"),
        "call_script": output.get("call_script"),
        "variables_used": row.variables_used_json or [],
        "confidence": row.confidence,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def generate_content(
    db: Session,
    *,
    lead_id: str | None,
    channel: str,
    step: int = 1,
    template_key: str | None = None,
    context: dict[str, Any] | None = None,
    provider: str = "deterministic",
    provider_config: dict[str, Any] | None = None,
) -> DBContentGeneration:
    normalized_channel = (channel or "").strip().lower()
    if normalized_channel not in ALLOWED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported channel '{channel}'.",
        )

    lead: DBLead | None = None
    if lead_id:
        lead = db.query(DBLead).filter(DBLead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

    payload = context or {}
    requested_provider = (provider or "deterministic").strip().lower() or "deterministic"
    used_provider = requested_provider

    output: dict[str, Any]
    if requested_provider == "ollama":
        try:
            output = _generate_with_ollama(
                channel=normalized_channel,
                lead=lead,
                step=max(1, step),
                context=payload,
                provider_config=provider_config,
            )
        except Exception as exc:  # pragma: no cover - provider/network variation
            logger.warning("Ollama content generation failed, using deterministic fallback.", extra={"error": str(exc)})
            used_provider = "deterministic"
            if normalized_channel == "email":
                subject, body = _render_email(lead, max(1, step), payload)
                output = {"subject": subject, "body": body}
            elif normalized_channel == "call":
                output = {"call_script": _render_call_script(lead, payload)}
            else:
                output = {"body": _render_dm(lead, payload)}
    elif normalized_channel == "email":
        subject, body = _render_email(lead, max(1, step), payload)
        output = {"subject": subject, "body": body}
    elif normalized_channel == "call":
        output = {"call_script": _render_call_script(lead, payload)}
    else:
        output = {"body": _render_dm(lead, payload)}

    confidence = 0.62
    if lead:
        confidence += 0.18
    if payload:
        confidence += 0.12
    confidence = min(confidence, 0.95)

    row = DBContentGeneration(
        id=str(uuid.uuid4()),
        lead_id=lead.id if lead else None,
        channel=normalized_channel,
        step=max(1, int(step)),
        template_key=(template_key or "").strip() or None,
        provider=used_provider,
        prompt_context_json=payload,
        output_json=output,
        variables_used_json=_extract_variables(lead, payload),
        confidence=round(confidence, 2),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
