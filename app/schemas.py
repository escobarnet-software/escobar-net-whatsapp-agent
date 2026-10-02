"""Pydantic schemas: WhatsApp webhook payloads + structured agent output."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class BookingSlot(BaseModel):
    customer_name: str | None = Field(default=None, max_length=120)
    service: str | None = Field(default=None, max_length=160)
    scheduled_at: str | None = Field(default=None, description="ISO datetime local, ej 2026-10-03T10:00:00")
    address: str | None = None
    notes: str | None = None


class AgentDecision(BaseModel):
    """Strict JSON the LLM must return."""
    intent: Literal["greeting", "question", "booking", "cancel_booking", "handoff", "other"] = "other"
    reply: str = Field(min_length=1, max_length=1000)
    booking: BookingSlot | None = None
    wants_confirmation: bool = False
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class AppointmentCreate(BaseModel):
    phone: str
    customer_name: str
    service: str
    scheduled_at: str
    address: str | None = None
    notes: str | None = None


class SimulateIn(BaseModel):
    phone: str = Field(examples=["573001112233"])
    text: str
    name: str | None = None
