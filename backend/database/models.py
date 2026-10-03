from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_unique_id: Mapped[str] = mapped_column(String(64), index=True)
    customer_zip_code_prefix: Mapped[int] = mapped_column(Integer)
    customer_city: Mapped[str] = mapped_column(String(128))
    customer_state: Mapped[str] = mapped_column(String(8))

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class ProductCategoryTranslation(Base):
    __tablename__ = "product_category_translations"

    product_category_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    product_category_name_english: Mapped[str] = mapped_column(String(128))


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_category_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product_name_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_description_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_photos_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_weight_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_width_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="product")


class Seller(Base):
    __tablename__ = "sellers"

    seller_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    seller_zip_code_prefix: Mapped[int] = mapped_column(Integer)
    seller_city: Mapped[str] = mapped_column(String(128))
    seller_state: Mapped[str] = mapped_column(String(8))

    items: Mapped[list["OrderItem"]] = relationship(back_populates="seller")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("customers.customer_id"), index=True
    )
    order_status: Mapped[str] = mapped_column(String(32), index=True)
    order_purchase_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_delivered_carrier_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    order_delivered_customer_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    order_estimated_delivery_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    customer: Mapped[Customer] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    payments: Mapped[list["OrderPayment"]] = relationship(back_populates="order")
    reviews: Mapped[list["OrderReview"]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("orders.order_id"), primary_key=True
    )
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("products.product_id"), index=True
    )
    seller_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sellers.seller_id"), index=True
    )
    shipping_limit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    price: Mapped[float] = mapped_column(Float)
    freight_value: Mapped[float] = mapped_column(Float)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="items")
    seller: Mapped[Seller] = relationship(back_populates="items")


class OrderPayment(Base):
    __tablename__ = "order_payments"

    order_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("orders.order_id"), primary_key=True
    )
    payment_sequential: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_type: Mapped[str] = mapped_column(String(32), index=True)
    payment_installments: Mapped[int] = mapped_column(Integer)
    payment_value: Mapped[float] = mapped_column(Float)

    order: Mapped[Order] = relationship(back_populates="payments")


class OrderReview(Base):
    __tablename__ = "order_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    order_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("orders.order_id"), index=True
    )
    review_score: Mapped[int] = mapped_column(Integer)
    review_comment_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_comment_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_creation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_answer_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    order: Mapped[Order] = relationship(back_populates="reviews")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    ticket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    issue: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("ix_orders_status_purchase", Order.order_status, Order.order_purchase_timestamp)
