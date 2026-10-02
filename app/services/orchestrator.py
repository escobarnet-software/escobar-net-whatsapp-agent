"""Orchestrator: ingest user text -> memory -> Groq decide -> optional booking -> reply."""
from __future__ import annotations
import logging
from sqlalchemy.orm import Session
from app import models
from app.config import get_settings
from app.schemas import AgentDecision
from app.services import memory as mem
from app.services import booking as booking_svc
from app.services.booking import IncompleteBookingError
from app.services.groq_agent import GroqAgent
from app.services import whatsapp as wa

log = logging.getLogger(__name__)
CONFIRM_WORDS = {"si", "sí", "confirmo", "confirmar", "dale", "ok", "de acuerdo", "agendalo", "agéndalo"}


def extract_messages(payload: dict) -> list[tuple[str, str, str | None, str | None]]:
    """Extract ALL (phone, text, wa_msg_id, profile_name) from a Meta webhook payload.

    Real Meta shape:
      {"object": "whatsapp_business_account",
       "entry": [{"changes": [{"field": "messages", "value": {
         "contacts": [{"profile": {"name": ...}, "wa_id": ...}],
         "messages": [{"from": ..., "id": ..., "type": "text", "text": {"body": ...}}]}}]}]}
    Skips non-text messages and status-only deliveries (no 'messages' key).
    """
    out: list[tuple[str, str, str | None, str | None]] = []
    if not isinstance(payload, dict):
        return out
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue
            contacts = value.get("contacts") or []
            profile_name: str | None = None
            if contacts and isinstance(contacts[0], dict):
                prof = contacts[0].get("profile") or {}
                profile_name = prof.get("name") if isinstance(prof, dict) else None
            for msg in value.get("messages") or []:
                if not isinstance(msg, dict):
                    continue
                if msg.get("type") and msg.get("type") != "text":
                    continue  # ignore images/audio/reactions for now
                phone = msg.get("from") or ""
                body = msg.get("text") or {}
                text = (body.get("body") if isinstance(body, dict) else "") or ""
                text = text.strip()
                if phone and text:
                    out.append((phone, text, msg.get("id"), profile_name))
    return out


def _extract_incoming(payload: dict) -> tuple[str, str, str | None, str | None]:
    """Backwards-compatible single-message extractor (first text message)."""
    msgs = extract_messages(payload)
    if not msgs:
        return "", "", None, None
    return msgs[0]


def _slot_complete(dec: AgentDecision) -> bool:
    b = dec.booking
    return bool(b and b.customer_name and b.service and b.scheduled_at)


def handle_text(db: Session, phone: str, text: str, name: str | None = None, wa_id: str | None = None) -> str:
    s = get_settings()
    contact = mem.get_or_create_contact(db, phone, name)
    mem.save_message(db, contact, "user", text, wa_id)
    history = mem.load_history(db, contact)

    dec = GroqAgent().decide(history)
    reply = dec.reply

    # Persist if slot complete AND (model asks confirmation + user confirmed) or slot complete with explicit SI.
    user_said_yes = text.strip().lower() in CONFIRM_WORDS or text.strip().lower().startswith("si ")
    if dec.intent == "booking" and _slot_complete(dec):
        assert dec.booking is not None
        if dec.wants_confirmation and not user_said_yes:
            reply = (f"Perfecto {dec.booking.customer_name}: {dec.booking.service} el {dec.booking.scheduled_at}. "
                     f"Responde SI para confirmar el registro.")
        else:
            try:
                ap: models.Appointment = booking_svc.create_appointment(db, contact, dec.booking)
                reply = (f"Listo {ap.customer_name}, tu {ap.service} quedó registrada para el {ap.scheduled_at}. "
                         f"Te contactaremos al {phone}. ¡Gracias por preferir {s.BUSINESS_NAME}!")
            except IncompleteBookingError as e:
                reply = f"Me falta un dato para agendar: {', '.join(e.missing)}. ¿Me lo compartes?"
            except ValueError as e:
                reply = f"No pude registrar la cita: {e}. ¿Confirmamos otra fecha/hora?"
    elif dec.intent == "cancel_booking":
        reply = dec.reply or "Anotado. ¿Deseas cancelar o reprogramar tu cita? Indícame tu nombre y fecha."

    mem.save_message(db, contact, "assistant", reply)
    wa.send_text(phone, reply)
    return reply
