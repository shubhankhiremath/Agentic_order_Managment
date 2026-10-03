from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import Order
from backend.services.exception_service import count_orders_with_exceptions


def get_dashboard_metrics(session: Session) -> dict:
    def _count(status: str | None = None) -> int:
        stmt = select(func.count()).select_from(Order)
        if status:
            stmt = stmt.where(Order.order_status == status)
        return int(session.execute(stmt).scalar() or 0)

    by_status_rows = session.execute(
        select(Order.order_status, func.count()).group_by(Order.order_status)
    ).all()
    return {
        "total_orders": _count(),
        "delivered_orders": _count("delivered"),
        "shipped_orders": _count("shipped"),
        "cancelled_orders": _count("canceled"),
        "orders_with_exceptions": count_orders_with_exceptions(session),
        "status_counts": {status: int(n) for status, n in by_status_rows},
    }
