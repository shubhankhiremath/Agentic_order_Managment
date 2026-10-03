from __future__ import annotations

import json
from contextvars import ContextVar

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.database import session as db_session
from backend.logging_setup import get_logger
from backend.rag.retriever import search_business_policies_tool
from backend.services.exception_service import evaluate_order_exceptions
from backend.services.order_service import (
    get_customer_orders,
    get_delivery_information,
    get_order_details,
    get_order_items,
    get_order_reviews,
    get_order_status,
    get_payment_details,
    search_order_by_customer,
)
from backend.services.ticket_service import create_support_ticket as create_ticket

logger = get_logger("tools")

trace_var: ContextVar[list | None] = ContextVar("agent_trace", default=None)


def reset_trace() -> list:
    bucket: list = []
    trace_var.set(bucket)
    return bucket


def get_trace() -> list:
    return trace_var.get() or []


def _record(name: str, purpose: str, status: str, extra: dict | None = None) -> None:
    event = {"tool": name, "purpose": purpose, "status": status}
    if extra:
        event.update(extra)
    bucket = trace_var.get()
    if bucket is not None:
        bucket.append(event)
    logger.info("tool_call tool=%s status=%s", name, status)


def _dumps(payload: dict) -> str:
    return json.dumps(payload, default=str)


class OrderIdInput(BaseModel):
    order_id: str = Field(..., min_length=8, max_length=64, description="Olist order_id")


class CustomerIdInput(BaseModel):
    customer_id: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="customer_id or customer_unique_id",
    )


class TicketInput(BaseModel):
    order_id: str = Field(..., min_length=8, max_length=64)
    issue: str = Field(..., min_length=3, max_length=128)
    description: str = Field(..., min_length=3, max_length=2000)


@tool("get_order_status", args_schema=OrderIdInput)
def get_order_status_tool(order_id: str) -> str:
    """Get the current status and key dates for an order."""
    session = db_session.SessionLocal()
    try:
        result = get_order_status(session, order_id)
        _record(
            "get_order_status",
            "Look up order status",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_order_status", "Look up order status", "error")
        logger.exception("get_order_status failed")
        return _dumps({"found": False, "error": "Unable to look up order status"})
    finally:
        session.close()


@tool("get_order_details", args_schema=OrderIdInput)
def get_order_details_tool(order_id: str) -> str:
    """Get complete order details including customer, items, payments, and reviews."""
    session = db_session.SessionLocal()
    try:
        result = get_order_details(session, order_id)
        _record(
            "get_order_details",
            "Load full order details",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_order_details", "Load full order details", "error")
        logger.exception("get_order_details failed")
        return _dumps({"found": False, "error": "Unable to load order details"})
    finally:
        session.close()


@tool("get_customer_orders", args_schema=CustomerIdInput)
def get_customer_orders_tool(customer_id: str) -> str:
    """List orders for a customer_id, including other orders that share customer_unique_id."""
    session = db_session.SessionLocal()
    try:
        result = get_customer_orders(session, customer_id)
        _record(
            "get_customer_orders",
            "List orders for a customer",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_customer_orders", "List orders for a customer", "error")
        logger.exception("get_customer_orders failed")
        return _dumps({"found": False, "error": "Unable to list customer orders"})
    finally:
        session.close()


@tool("search_order_by_customer", args_schema=CustomerIdInput)
def search_order_by_customer_tool(customer_id: str) -> str:
    """Search order IDs and statuses for a customer_id or customer_unique_id."""
    session = db_session.SessionLocal()
    try:
        result = search_order_by_customer(session, customer_id)
        _record(
            "search_order_by_customer",
            "Search orders by customer",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("search_order_by_customer", "Search orders by customer", "error")
        logger.exception("search_order_by_customer failed")
        return _dumps({"found": False, "error": "Unable to search orders"})
    finally:
        session.close()


@tool("get_order_items", args_schema=OrderIdInput)
def get_order_items_tool(order_id: str) -> str:
    """Get products and sellers on an order. Product titles are not in the dataset."""
    session = db_session.SessionLocal()
    try:
        result = get_order_items(session, order_id)
        _record(
            "get_order_items",
            "Load order line items",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_order_items", "Load order line items", "error")
        logger.exception("get_order_items failed")
        return _dumps({"found": False, "error": "Unable to load order items"})
    finally:
        session.close()


@tool("get_payment_details", args_schema=OrderIdInput)
def get_payment_details_tool(order_id: str) -> str:
    """Get payment method, installments, and amounts for an order."""
    session = db_session.SessionLocal()
    try:
        result = get_payment_details(session, order_id)
        _record(
            "get_payment_details",
            "Load payment details",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_payment_details", "Load payment details", "error")
        logger.exception("get_payment_details failed")
        return _dumps({"found": False, "error": "Unable to load payments"})
    finally:
        session.close()


@tool("get_delivery_information", args_schema=OrderIdInput)
def get_delivery_information_tool(order_id: str) -> str:
    """Get purchase, approval, carrier, estimated, and actual delivery timestamps."""
    session = db_session.SessionLocal()
    try:
        result = get_delivery_information(session, order_id)
        _record(
            "get_delivery_information",
            "Load delivery timeline",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_delivery_information", "Load delivery timeline", "error")
        logger.exception("get_delivery_information failed")
        return _dumps({"found": False, "error": "Unable to load delivery information"})
    finally:
        session.close()


@tool("check_delivery_exception", args_schema=OrderIdInput)
def check_delivery_exception_tool(order_id: str) -> str:
    """Run deterministic demo exception rules for an order. Not official Olist policy."""
    session = db_session.SessionLocal()
    try:
        result = evaluate_order_exceptions(session, order_id)
        _record(
            "check_delivery_exception",
            "Evaluate demo delivery/payment exceptions",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("check_delivery_exception", "Evaluate demo exceptions", "error")
        logger.exception("check_delivery_exception failed")
        return _dumps({"found": False, "has_exception": False, "error": "Unable to evaluate exceptions"})
    finally:
        session.close()


@tool("get_order_reviews", args_schema=OrderIdInput)
def get_order_reviews_tool(order_id: str) -> str:
    """Get review scores and comments for an order."""
    session = db_session.SessionLocal()
    try:
        result = get_order_reviews(session, order_id)
        _record(
            "get_order_reviews",
            "Load order reviews",
            "ok" if result.get("found") else "not_found",
        )
        return _dumps(result)
    except Exception:
        _record("get_order_reviews", "Load order reviews", "error")
        logger.exception("get_order_reviews failed")
        return _dumps({"found": False, "error": "Unable to load reviews"})
    finally:
        session.close()


@tool("create_support_ticket", args_schema=TicketInput)
def create_support_ticket_tool(order_id: str, issue: str, description: str) -> str:
    """Create a simulated local support ticket for an existing order."""
    session = db_session.SessionLocal()
    try:
        result = create_ticket(session, order_id, issue, description)
        _record(
            "create_support_ticket",
            "Create simulated support ticket",
            "ok" if result.get("created") else "error",
            extra={"action": "create_support_ticket", "ticket_id": result.get("ticket_id")},
        )
        return _dumps(result)
    except Exception:
        _record("create_support_ticket", "Create simulated support ticket", "error")
        logger.exception("create_support_ticket failed")
        return _dumps({"created": False, "error": "Unable to create support ticket"})
    finally:
        session.close()


ORDER_TOOLS = [
    get_order_status_tool,
    get_order_details_tool,
    get_customer_orders_tool,
    search_order_by_customer_tool,
    get_order_items_tool,
    get_payment_details_tool,
    get_delivery_information_tool,
    check_delivery_exception_tool,
    get_order_reviews_tool,
    create_support_ticket_tool,
    search_business_policies_tool,
]
