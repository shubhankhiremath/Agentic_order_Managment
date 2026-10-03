from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database.models import (
    Customer,
    Order,
    OrderItem,
    OrderPayment,
    OrderReview,
    Product,
    ProductCategoryTranslation,
    Seller,
)

ISO = "%Y-%m-%dT%H:%M:%S"


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def get_order(session: Session, order_id: str) -> Order | None:
    return session.get(Order, order_id.strip())


def get_order_status(session: Session, order_id: str) -> dict:
    order = get_order(session, order_id)
    if not order:
        return {"found": False, "order_id": order_id, "error": "Order not found"}
    return {
        "found": True,
        "order_id": order.order_id,
        "order_status": order.order_status,
        "order_purchase_timestamp": _iso(order.order_purchase_timestamp),
        "order_estimated_delivery_date": _iso(order.order_estimated_delivery_date),
        "order_delivered_customer_date": _iso(order.order_delivered_customer_date),
    }


def get_delivery_information(session: Session, order_id: str) -> dict:
    order = get_order(session, order_id)
    if not order:
        return {"found": False, "order_id": order_id, "error": "Order not found"}
    items = session.scalars(select(OrderItem).where(OrderItem.order_id == order.order_id)).all()
    shipping_limits = [_iso(i.shipping_limit_date) for i in items if i.shipping_limit_date]
    return {
        "found": True,
        "order_id": order.order_id,
        "order_status": order.order_status,
        "order_purchase_timestamp": _iso(order.order_purchase_timestamp),
        "order_approved_at": _iso(order.order_approved_at),
        "order_delivered_carrier_date": _iso(order.order_delivered_carrier_date),
        "order_delivered_customer_date": _iso(order.order_delivered_customer_date),
        "order_estimated_delivery_date": _iso(order.order_estimated_delivery_date),
        "shipping_limit_dates": shipping_limits,
    }


def get_order_items(session: Session, order_id: str) -> dict:
    order = get_order(session, order_id)
    if not order:
        return {"found": False, "order_id": order_id, "error": "Order not found", "items": []}
    stmt = (
        select(OrderItem, Product, Seller, ProductCategoryTranslation)
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Seller, Seller.seller_id == OrderItem.seller_id)
        .outerjoin(
            ProductCategoryTranslation,
            ProductCategoryTranslation.product_category_name == Product.product_category_name,
        )
        .where(OrderItem.order_id == order.order_id)
        .order_by(OrderItem.order_item_id)
    )
    rows = session.execute(stmt).all()
    items = []
    for item, product, seller, translation in rows:
        items.append(
            {
                "order_item_id": item.order_item_id,
                "product_id": item.product_id,
                "product_category": product.product_category_name,
                "product_category_english": (
                    translation.product_category_name_english if translation else None
                ),
                "seller_id": item.seller_id,
                "seller_city": seller.seller_city,
                "seller_state": seller.seller_state,
                "price": item.price,
                "freight_value": item.freight_value,
                "shipping_limit_date": _iso(item.shipping_limit_date),
            }
        )
    return {
        "found": True,
        "order_id": order.order_id,
        "item_count": len(items),
        "items": items,
    }


def get_payment_details(session: Session, order_id: str) -> dict:
    order = get_order(session, order_id)
    if not order:
        return {"found": False, "order_id": order_id, "error": "Order not found", "payments": []}
    payments = session.scalars(
        select(OrderPayment)
        .where(OrderPayment.order_id == order.order_id)
        .order_by(OrderPayment.payment_sequential)
    ).all()
    payload = [
        {
            "payment_sequential": p.payment_sequential,
            "payment_type": p.payment_type,
            "payment_installments": p.payment_installments,
            "payment_value": p.payment_value,
        }
        for p in payments
    ]
    return {
        "found": True,
        "order_id": order.order_id,
        "payment_count": len(payload),
        "total_payment_value": round(sum(p["payment_value"] for p in payload), 2),
        "payments": payload,
    }


def get_order_reviews(session: Session, order_id: str) -> dict:
    order = get_order(session, order_id)
    if not order:
        return {"found": False, "order_id": order_id, "error": "Order not found", "reviews": []}
    reviews = session.scalars(
        select(OrderReview).where(OrderReview.order_id == order.order_id)
    ).all()
    return {
        "found": True,
        "order_id": order.order_id,
        "review_count": len(reviews),
        "reviews": [
            {
                "review_id": r.review_id,
                "review_score": r.review_score,
                "review_comment_title": r.review_comment_title,
                "review_comment_message": r.review_comment_message,
                "review_creation_date": _iso(r.review_creation_date),
            }
            for r in reviews
        ],
    }


def _customer_ids_for_lookup(session: Session, customer_id: str) -> list[str]:
    customer = session.get(Customer, customer_id.strip())
    if customer:
        ids = session.scalars(
            select(Customer.customer_id).where(
                Customer.customer_unique_id == customer.customer_unique_id
            )
        ).all()
        return list(ids)
    # Also allow lookup by customer_unique_id
    ids = session.scalars(
        select(Customer.customer_id).where(Customer.customer_unique_id == customer_id.strip())
    ).all()
    return list(ids)


def search_order_by_customer(session: Session, customer_id: str) -> dict:
    ids = _customer_ids_for_lookup(session, customer_id)
    if not ids:
        return {"found": False, "customer_id": customer_id, "error": "Customer not found", "orders": []}
    orders = session.scalars(
        select(Order)
        .where(Order.customer_id.in_(ids))
        .order_by(Order.order_purchase_timestamp.desc())
    ).all()
    return {
        "found": True,
        "query": customer_id,
        "order_count": len(orders),
        "orders": [
            {
                "order_id": o.order_id,
                "order_status": o.order_status,
                "order_purchase_timestamp": _iso(o.order_purchase_timestamp),
            }
            for o in orders
        ],
    }


def get_customer_orders(session: Session, customer_id: str) -> dict:
    result = search_order_by_customer(session, customer_id)
    if not result["found"]:
        return result
    detailed = []
    for row in result["orders"]:
        detailed.append(get_order_status(session, row["order_id"]))
    result["orders"] = detailed
    return result


def get_order_details(session: Session, order_id: str) -> dict:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.reviews),
        )
        .where(Order.order_id == order_id.strip())
    )
    order = session.scalars(stmt).first()
    if not order:
        return {"found": False, "order_id": order_id, "error": "Order not found"}
    customer = order.customer
    return {
        "found": True,
        "order_id": order.order_id,
        "order_status": order.order_status,
        "purchase_timestamp": _iso(order.order_purchase_timestamp),
        "approved_at": _iso(order.order_approved_at),
        "delivered_carrier_date": _iso(order.order_delivered_carrier_date),
        "delivered_customer_date": _iso(order.order_delivered_customer_date),
        "estimated_delivery_date": _iso(order.order_estimated_delivery_date),
        "customer": {
            "customer_id": customer.customer_id,
            "customer_unique_id": customer.customer_unique_id,
            "city": customer.customer_city,
            "state": customer.customer_state,
            "zip_code_prefix": customer.customer_zip_code_prefix,
        },
        "items": get_order_items(session, order.order_id)["items"],
        "payments": get_payment_details(session, order.order_id)["payments"],
        "reviews": get_order_reviews(session, order.order_id)["reviews"],
    }
