"""Booking service: validates slot and persists Appointment."""
from __future__ import annotations
from dateutil import parser as date_parser
from sqlalchemy.orm import Session
from app import models
from app.schemas import BookingSlot


class IncompleteBookingError(ValueError):
    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"Faltan datos: {', '.join(missing)}")
        self.missing = missing


def validate_slot(slot: BookingSlot) -> tuple[str, str, str]:
    missing = [f for f in ("customer_name", "service", "scheduled_at") if not getattr(slot, f)]
    if missing:
        raise IncompleteBookingError(missing)
    try:
        dt = date_parser.parse(slot.scheduled_at or "")
        iso = dt.isoformat(timespec="minutes")
    except Exception as e:
        raise ValueError(f"Fecha/hora invalida '{slot.scheduled_at}': {e}") from e
    return slot.customer_name.strip(), slot.service.strip(), iso  # type: ignore[union-attr]


def create_appointment(db: Session, contact: models.Contact, slot: BookingSlot) -> models.Appointment:
    name, service, iso = validate_slot(slot)
    ap = models.Appointment(contact_id=contact.id, customer_name=name, service=service,
        scheduled_at=iso, address=slot.address, notes=slot.notes, status="pending")
    db.add(ap)
    if not contact.name:
        contact.name = name
    db.commit()
    db.refresh(ap)
    return ap
