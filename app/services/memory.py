"""Conversation memory: persist + load recent window per phone."""
from __future__ import annotations
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app import models
from app.config import get_settings


def get_or_create_contact(db: Session, phone: str, name: str | None = None) -> models.Contact:
    c = db.scalar(select(models.Contact).where(models.Contact.phone == phone))
    if c:
        if name and not c.name:
            c.name = name
            db.commit()
        return c
    c = models.Contact(phone=phone, name=name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def save_message(db: Session, contact: models.Contact, role: str, content: str, wa_id: str | None = None) -> None:
    db.add(models.Message(contact_id=contact.id, role=role, content=content, wa_message_id=wa_id))
    db.commit()


def load_history(db: Session, contact: models.Contact, limit: int | None = None) -> list[dict[str, str]]:
    n = limit or get_settings().MEMORY_WINDOW
    rows = db.scalars(select(models.Message).where(models.Message.contact_id == contact.id)
        .order_by(desc(models.Message.id)).limit(n)).all()
    rows = list(reversed(rows))
    return [{"role": m.role if m.role in ("user", "assistant") else "user", "content": m.content} for m in rows]
