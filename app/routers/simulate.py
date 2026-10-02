"""Local simulator + health (no Meta needed)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SimulateIn
from app.services.orchestrator import handle_text

router = APIRouter(tags=["dev"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/simulate")
def simulate(body: SimulateIn, db: Session = Depends(get_db)) -> dict:
    reply = handle_text(db, body.phone, body.text, body.name)
    return {"from": "assistant", "to": body.phone, "reply": reply}
