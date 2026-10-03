from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.database.models import SupportTicket
from backend.services.order_service import get_order


def create_support_ticket(
    session: Session, order_id: str, issue: str, description: str
) -> dict:
    order = get_order(session, order_id)
    if not order:
        return {"created": False, "error": "Order not found", "order_id": order_id}
    issue_clean = (issue or "").strip()
    description_clean = (description or "").strip()
    if not issue_clean or not description_clean:
        return {
            "created": False,
            "error": "Issue and description are required",
            "order_id": order_id,
        }
    ticket = SupportTicket(
        ticket_id=f"TKT-{uuid4().hex[:12].upper()}",
        order_id=order.order_id,
        issue=issue_clean[:128],
        description=description_clean,
        status="open",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return {
        "created": True,
        "simulated": True,
        "note": "Demo support ticket stored locally. Not connected to a live commerce system.",
        "ticket_id": ticket.ticket_id,
        "order_id": ticket.order_id,
        "issue": ticket.issue,
        "description": ticket.description,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
    }
