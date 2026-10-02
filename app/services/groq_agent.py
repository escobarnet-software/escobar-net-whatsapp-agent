"""Groq agent: single chat call -> strict AgentDecision JSON (intent + reply + booking slot)."""
from __future__ import annotations
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from groq import Groq
from app.config import get_settings
from app.prompts import build_system_prompt
from app.schemas import AgentDecision

log = logging.getLogger(__name__)

_JSON_INSTRUCTION = """
Responde UNICAMENTE con este JSON (sin markdown, sin texto extra):
{"intent": "greeting|question|booking|cancel_booking|handoff|other", "reply": "<mensaje al cliente>",
 "booking": {"customer_name": "..."|null, "service": "..."|null, "scheduled_at": "ISO"|null, "address": null, "notes": null},
 "wants_confirmation": false, "confidence": 0.9}
intents: booking = quiere agendar/reservar; cancel_booking = cancelar; handoff = pide humano.
"""


class GroqAgent:
    def __init__(self) -> None:
        self.s = get_settings()
        self.client = Groq(api_key=self.s.GROQ_API_KEY) if self.s.GROQ_API_KEY else None

    def _now(self) -> str:
        try:
            return datetime.now(ZoneInfo(self.s.AGENT_TIMEZONE)).isoformat(timespec="minutes")
        except Exception:
            return datetime.now().isoformat(timespec="minutes")

    def decide(self, history: list[dict[str, str]]) -> AgentDecision:
        """history: [{'role':'user'|'assistant','content':...}] oldest->newest. Fallback heuristic if no key."""
        if self.client is None:
            return self._fallback(history)
        try:
            sys = build_system_prompt(self._now()) + _JSON_INSTRUCTION
            msgs = [{"role": "system", "content": sys}, *history[-self.s.MEMORY_WINDOW:]]
            r = self.client.chat.completions.create(
                model=self.s.GROQ_MODEL, messages=msgs,  # type: ignore[arg-type]
                temperature=self.s.GROQ_TEMPERATURE, max_tokens=self.s.GROQ_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            raw = (r.choices[0].message.content or "{}").strip()
            data = json.loads(raw)
            return AgentDecision.model_validate(data)
        except Exception as e:
            log.warning("Groq decide failed, fallback: %s", e)
            return self._fallback(history)

    def _fallback(self, history: list[dict[str, str]]) -> AgentDecision:
        last = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        t = last.lower()
        booking_kw = ("agendar", "agenda", "cita", "reserv", "instala", "visita", "soporte", "tecnico")
        if any(k in t for k in booking_kw):
            return AgentDecision(intent="booking", wants_confirmation=False,
                reply="Con gusto te agendo. ¿Me confirmas tu nombre, el servicio que necesitas y la fecha/hora ideal?")
        if any(k in t for k in ("hola", "buenas", "buenos dias", "buenas tardes")):
            s = get_settings()
            return AgentDecision(intent="greeting",
                reply=f"Hola, soy el asistente de {s.BUSINESS_NAME}. ¿Buscas internet, soporte o agendar una visita?")
        return AgentDecision(intent="other", reply="Gracias por tu mensaje. ¿Te ayudo a agendar un servicio o resolver una duda?")
