"""Deterministic demo exception rules. Not official Olist policy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database.models import Order, OrderPayment
from backend.services.order_service import get_order

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _date(value: datetime | None):
    return value.date() if value else None


def evaluate_order_exceptions(session: Session, order_id: str) -> dict:
    settings = get_settings()
    as_of = datetime.fromisoformat(settings.dataset_as_of_date).date()
    order = get_order(session, order_id)
    if not order:
        return {
            "found": False,
            "order_id": order_id,
            "has_exception": False,
            "exception_type": None,
            "severity": None,
            "message": "Order not found",
            "evidence": {},
            "exceptions": [],
        }

    exceptions: list[dict] = []
    status = order.order_status
    purchase = order.order_purchase_timestamp
    estimated = order.order_estimated_delivery_date
    actual = order.order_delivered_customer_date
    carrier = order.order_delivered_carrier_date
    approved = order.order_approved_at

    if status == "delivered" and actual and estimated and _date(actual) > _date(estimated):
        delay_days = (_date(actual) - _date(estimated)).days
        exceptions.append(
            {
                "exception_type": "DELIVERY_DELAY",
                "severity": "HIGH" if delay_days >= 7 else "MEDIUM",
                "message": (
                    f"Demo rule: delivered {delay_days} day(s) after the estimated delivery date."
                ),
                "evidence": {
                    "order_status": status,
                    "estimated_delivery_date": estimated.isoformat(),
                    "actual_delivery_date": actual.isoformat(),
                    "delay_days": delay_days,
                },
            }
        )

    if status == "delivered" and actual is None:
        exceptions.append(
            {
                "exception_type": "MISSING_DELIVERY_INFO",
                "severity": "MEDIUM",
                "message": "Demo rule: status is delivered but customer delivery timestamp is missing.",
                "evidence": {"order_status": status, "order_delivered_customer_date": None},
            }
        )

    if status == "shipped":
        if estimated and _date(estimated) < as_of:
            exceptions.append(
                {
                    "exception_type": "SHIPPED_NOT_DELIVERED",
                    "severity": "HIGH",
                    "message": (
                        "Demo rule: order is shipped, estimated delivery has passed the dataset "
                        f"as-of date ({as_of.isoformat()}), and no customer delivery date exists."
                    ),
                    "evidence": {
                        "order_status": status,
                        "estimated_delivery_date": estimated.isoformat() if estimated else None,
                        "order_delivered_carrier_date": carrier.isoformat() if carrier else None,
                        "dataset_as_of_date": as_of.isoformat(),
                    },
                }
            )
        else:
            exceptions.append(
                {
                    "exception_type": "IN_TRANSIT",
                    "severity": "LOW",
                    "message": "Demo rule: order is shipped and not yet delivered.",
                    "evidence": {
                        "order_status": status,
                        "order_delivered_carrier_date": carrier.isoformat() if carrier else None,
                    },
                }
            )

    if status in {"approved", "invoiced", "processing"} and carrier is None:
        severity = "HIGH" if estimated and _date(estimated) < as_of else "MEDIUM"
        exceptions.append(
            {
                "exception_type": "APPROVED_NOT_SHIPPED",
                "severity": severity,
                "message": (
                    f"Demo rule: order is '{status}' with no carrier handoff timestamp."
                ),
                "evidence": {
                    "order_status": status,
                    "order_approved_at": approved.isoformat() if approved else None,
                    "order_delivered_carrier_date": None,
                    "order_estimated_delivery_date": estimated.isoformat() if estimated else None,
                },
            }
        )

    if status == "delivered" and actual and purchase:
        duration = (_date(actual) - _date(purchase)).days
        if duration >= settings.long_delivery_days:
            exceptions.append(
                {
                    "exception_type": "LONG_DELIVERY_DURATION",
                    "severity": "MEDIUM",
                    "message": (
                        f"Demo rule: delivery took {duration} days, which exceeds the "
                        f"{settings.long_delivery_days}-day demo threshold."
                    ),
                    "evidence": {
                        "purchase_timestamp": purchase.isoformat(),
                        "actual_delivery_date": actual.isoformat(),
                        "duration_days": duration,
                    },
                }
            )

    payments = session.query(OrderPayment).filter(OrderPayment.order_id == order.order_id).all()
    if not payments:
        exceptions.append(
            {
                "exception_type": "PAYMENT_MISSING",
                "severity": "MEDIUM",
                "message": "Demo rule: no payment rows exist for this order.",
                "evidence": {"payment_count": 0},
            }
        )
    else:
        if any(p.payment_type == "not_defined" for p in payments):
            exceptions.append(
                {
                    "exception_type": "PAYMENT_UNDEFINED",
                    "severity": "LOW",
                    "message": "Demo rule: at least one payment has type 'not_defined'.",
                    "evidence": {
                        "payment_types": [p.payment_type for p in payments],
                    },
                }
            )
        if any(p.payment_value == 0 for p in payments):
            exceptions.append(
                {
                    "exception_type": "PAYMENT_ZERO_VALUE",
                    "severity": "LOW",
                    "message": "Demo rule: at least one payment has value 0.",
                    "evidence": {
                        "payment_values": [p.payment_value for p in payments],
                    },
                }
            )

    exceptions.sort(key=lambda e: SEVERITY_RANK.get(e["severity"], 0), reverse=True)
    primary = exceptions[0] if exceptions else None
    return {
        "found": True,
        "order_id": order.order_id,
        "has_exception": bool(exceptions),
        "exception_type": primary["exception_type"] if primary else None,
        "severity": primary["severity"] if primary else None,
        "message": primary["message"] if primary else "No demo exceptions detected.",
        "evidence": primary["evidence"] if primary else {},
        "exceptions": exceptions,
    }


def count_orders_with_exceptions(session: Session) -> int:
    """Lightweight dashboard count: late delivered + shipped past estimate + stuck pre-ship."""
    from sqlalchemy import func, select

    settings = get_settings()
    as_of = datetime.fromisoformat(settings.dataset_as_of_date)
    late = (
        select(func.count())
        .select_from(Order)
        .where(
            Order.order_status == "delivered",
            Order.order_delivered_customer_date.is_not(None),
            Order.order_estimated_delivery_date.is_not(None),
            Order.order_delivered_customer_date > Order.order_estimated_delivery_date,
        )
    )
    shipped_late = (
        select(func.count())
        .select_from(Order)
        .where(
            Order.order_status == "shipped",
            Order.order_estimated_delivery_date.is_not(None),
            Order.order_estimated_delivery_date < as_of,
        )
    )
    stuck = (
        select(func.count())
        .select_from(Order)
        .where(
            Order.order_status.in_(["approved", "invoiced", "processing"]),
            Order.order_delivered_carrier_date.is_(None),
        )
    )
    missing_delivery = (
        select(func.count())
        .select_from(Order)
        .where(
            Order.order_status == "delivered",
            Order.order_delivered_customer_date.is_(None),
        )
    )
    return int(
        (session.execute(late).scalar() or 0)
        + (session.execute(shipped_late).scalar() or 0)
        + (session.execute(stuck).scalar() or 0)
        + (session.execute(missing_delivery).scalar() or 0)
    )
