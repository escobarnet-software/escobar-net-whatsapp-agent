"""WhatsApp Cloud API sender (httpx). Dry-run safe."""
from __future__ import annotations
import logging
import httpx
from app.config import get_settings

log = logging.getLogger(__name__)


def send_text(to_phone: str, body: str) -> dict:
    s = get_settings()
    if s.WHATSAPP_DRY_RUN or not s.WHATSAPP_ACCESS_TOKEN or not s.WHATSAPP_PHONE_NUMBER_ID:
        log.info("[DRY_RUN] -> %s: %s", to_phone, body[:200])
        return {"dry_run": True, "to": to_phone}
    url = f"https://graph.facebook.com/{s.WHATSAPP_API_VERSION}/{s.WHATSAPP_PHONE_NUMBER_ID}/messages"
    try:
        r = httpx.post(url, headers={"Authorization": f"Bearer {s.WHATSAPP_ACCESS_TOKEN}"},
            json={"messaging_product": "whatsapp", "to": to_phone,
                  "type": "text", "text": {"body": body[:4096]}}, timeout=15.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error("WhatsApp send failed: %s", e)
        return {"error": str(e), "to": to_phone}
