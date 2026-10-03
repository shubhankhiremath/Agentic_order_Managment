from sqlalchemy import inspect, text

from backend.database.models import Order, SupportTicket
from backend.database.session import configure_engine, engine, init_db
from backend.services.exception_service import evaluate_order_exceptions
from backend.services.order_service import (
    get_order_details,
    get_order_items,
    get_order_status,
    get_payment_details,
)
from backend.services.ticket_service import create_support_ticket
from tests.conftest import SAMPLE_ORDER_IDS


def test_database_initialization(tmp_path):
    url = f"sqlite:///{(tmp_path / 'init.db').as_posix()}"
    bind = configure_engine(url)
    init_db(bind)
    names = inspect(bind).get_table_names()
    for table in [
        "orders",
        "order_items",
        "customers",
        "products",
        "sellers",
        "order_payments",
        "order_reviews",
        "support_tickets",
    ]:
        assert table in names


def test_data_loading_row_counts(db_session):
    count = db_session.scalar(text("SELECT COUNT(*) FROM orders"))
    assert count == len(SAMPLE_ORDER_IDS)
    assert db_session.get(Order, SAMPLE_ORDER_IDS[0]) is not None


def test_order_status(db_session):
    result = get_order_status(db_session, SAMPLE_ORDER_IDS[0])
    assert result["found"] is True
    assert result["order_status"] == "delivered"


def test_order_lookup_missing(db_session):
    result = get_order_status(db_session, "does-not-exist-order-id")
    assert result["found"] is False


def test_order_details_and_items(db_session):
    details = get_order_details(db_session, SAMPLE_ORDER_IDS[0])
    assert details["found"] is True
    assert details["customer"]["state"]
    items = get_order_items(db_session, SAMPLE_ORDER_IDS[0])
    assert items["item_count"] >= 1
    payments = get_payment_details(db_session, SAMPLE_ORDER_IDS[0])
    assert payments["payment_count"] >= 1


def test_late_delivery_exception(db_session):
    result = evaluate_order_exceptions(db_session, "203096f03d82e0dffbc41ebc2e2bcfb7")
    assert result["found"] is True
    assert result["has_exception"] is True
    assert result["exception_type"] == "DELIVERY_DELAY"
    assert result["evidence"]["delay_days"] >= 1


def test_on_time_delivered_no_delay_exception(db_session):
    result = evaluate_order_exceptions(db_session, "e481f51cbdc54678b7cc49136f2d6af7")
    types = {e["exception_type"] for e in result["exceptions"]}
    assert "DELIVERY_DELAY" not in types


def test_shipped_exception(db_session):
    result = evaluate_order_exceptions(db_session, "ee64d42b8cf066f35eac1cf57de1aa85")
    assert result["has_exception"] is True
    assert result["exception_type"] in {"SHIPPED_NOT_DELIVERED", "IN_TRANSIT"}


def test_missing_payment_exception(db_session):
    result = evaluate_order_exceptions(db_session, "bfbd0f9bdef84302105ad712db648a6c")
    types = {e["exception_type"] for e in result["exceptions"]}
    assert "PAYMENT_MISSING" in types


def test_approved_not_shipped(db_session):
    result = evaluate_order_exceptions(db_session, "a2e4c44360b4a57bdff22f3a4630c173")
    types = {e["exception_type"] for e in result["exceptions"]}
    assert "APPROVED_NOT_SHIPPED" in types


def test_create_support_ticket(db_session):
    result = create_support_ticket(
        db_session,
        SAMPLE_ORDER_IDS[0],
        "delivery_delay",
        "Customer reported a late delivery.",
    )
    assert result["created"] is True
    assert result["ticket_id"].startswith("TKT-")
    ticket = db_session.get(SupportTicket, result["ticket_id"])
    assert ticket is not None
    assert ticket.order_id == SAMPLE_ORDER_IDS[0]


def test_create_ticket_missing_order(db_session):
    result = create_support_ticket(db_session, "missing-order-id-xx", "delay", "desc")
    assert result["created"] is False
