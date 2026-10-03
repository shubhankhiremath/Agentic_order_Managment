from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agent.graph import run_agent
from backend.database.session import get_session
from backend.logging_setup import get_logger
from backend.schemas.api import ChatRequest, ChatResponse, SupportTicketRequest
from backend.services.dashboard_service import get_dashboard_metrics
from backend.services.exception_service import evaluate_order_exceptions
from backend.services.order_service import get_order_details, get_order_items, get_order_status
from backend.services.ticket_service import create_support_ticket

logger = get_logger("api")
router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    logger.info("chat_request session_id=%s", payload.session_id)
    result = run_agent(payload.message, payload.session_id)
    return result


@router.get("/api/orders/{order_id}")
def order_details(order_id: str, session: Session = Depends(get_session)):
    result = get_order_details(session, order_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.get("/api/orders/{order_id}/status")
def order_status(order_id: str, session: Session = Depends(get_session)):
    result = get_order_status(session, order_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.get("/api/orders/{order_id}/exceptions")
def order_exceptions(order_id: str, session: Session = Depends(get_session)):
    result = evaluate_order_exceptions(session, order_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.get("/api/orders/{order_id}/items")
def order_items(order_id: str, session: Session = Depends(get_session)):
    result = get_order_items(session, order_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.post("/api/support-tickets")
def support_tickets(payload: SupportTicketRequest, session: Session = Depends(get_session)):
    result = create_support_ticket(
        session, payload.order_id, payload.issue, payload.description
    )
    if not result.get("created"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unable to create ticket"))
    return result


@router.get("/api/dashboard")
def dashboard(session: Session = Depends(get_session)):
    return get_dashboard_metrics(session)
