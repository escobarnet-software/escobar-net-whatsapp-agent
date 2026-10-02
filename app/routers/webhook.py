"""Meta webhook: GET verify + POST ingest."""
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.services.orchestrator import extract_messages, handle_text

log = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])


@router.get("/webhook")
def verify(hub_mode: str | None = Query(default=None, alias="hub.mode"),
           hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
           hub_challenge: str | None = Query(default=None, alias="hub.challenge")) -> Response:
    s = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == s.WHATSAPP_VERIFY_TOKEN and hub_challenge:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


@router.post("/webhook")
async def ingest(request: Request, db: Session = Depends(get_db)) -> dict:
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "invalid-json"}
    log.info("webhook payload keys=%s", list(payload.keys()) if isinstance(payload, dict) else type(payload))
    msgs = extract_messages(payload)
    if not msgs:
        # statuses / delivery receipts / non-text: ack 200 so Meta stops retrying
        return {"status": "ignored", "reason": "no-text-message"}
    results: list[dict] = []
    for phone, text, wa_id, name in msgs:
        try:
            reply = handle_text(db, phone, text, name, wa_id)
            results.append({"to": phone, "reply_preview": reply[:120]})
        except Exception as e:
            log.exception("ingest failed for %s", phone)
            results.append({"to": phone, "error": str(e)})
    return {"status": "ok", "processed": len(results), "results": results}
