"""Repeatable CSV → SQLite import. Does not modify original CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from backend.config import get_settings
from backend.database.base import Base
from backend.database.models import (  # noqa: F401
    Customer,
    Order,
    OrderItem,
    OrderPayment,
    OrderReview,
    Product,
    ProductCategoryTranslation,
    Seller,
    SupportTicket,
)
from backend.database.session import init_db, make_engine
from backend.logging_setup import get_logger

logger = get_logger("import")

REQUIRED_FILES = {
    "olist_customers_dataset.csv": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "olist_orders_dataset.csv": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset.csv": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    "olist_products_dataset.csv": [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english",
    ],
}

ORDER_DATETIME_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def validate_dataset(dataset_dir: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (dataset_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing CSV files in {dataset_dir}: {missing}")
    for name, columns in REQUIRED_FILES.items():
        header = pd.read_csv(dataset_dir / name, nrows=0)
        absent = [c for c in columns if c not in header.columns]
        if absent:
            raise ValueError(f"{name} missing expected columns: {absent}")


def _read(dataset_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(dataset_dir / name, low_memory=False)


def _parse_dt(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _write_table(engine: Engine, df: pd.DataFrame, table: str) -> None:
    df.to_sql(table, engine, if_exists="append", index=False, chunksize=5000)


def import_dataset(
    dataset_dir: str | Path | None = None,
    database_url: str | None = None,
    order_ids: list[str] | None = None,
) -> dict[str, int]:
    settings = get_settings()
    dataset_path = Path(dataset_dir or settings.dataset_dir)
    validate_dataset(dataset_path)

    engine = make_engine(database_url or settings.database_url)
    if engine.url.drivername == "sqlite" and engine.url.database:
        db_path = Path(engine.url.database)
        if db_path.name != ":memory:":
            db_path.parent.mkdir(parents=True, exist_ok=True)
            if db_path.exists():
                engine.dispose()
                db_path.unlink()
                engine = make_engine(database_url or settings.database_url)

    Base.metadata.drop_all(engine)
    init_db(engine)

    customers = _read(dataset_path, "olist_customers_dataset.csv")
    orders = _read(dataset_path, "olist_orders_dataset.csv")
    items = _read(dataset_path, "olist_order_items_dataset.csv")
    payments = _read(dataset_path, "olist_order_payments_dataset.csv")
    reviews = _read(dataset_path, "olist_order_reviews_dataset.csv")
    products = _read(dataset_path, "olist_products_dataset.csv")
    sellers = _read(dataset_path, "olist_sellers_dataset.csv")
    translations = _read(dataset_path, "product_category_name_translation.csv")

    if order_ids:
        keep = set(order_ids)
        orders = orders[orders["order_id"].isin(keep)]
        items = items[items["order_id"].isin(keep)]
        payments = payments[payments["order_id"].isin(keep)]
        reviews = reviews[reviews["order_id"].isin(keep)]
        customers = customers[customers["customer_id"].isin(orders["customer_id"])]
        products = products[products["product_id"].isin(items["product_id"])]
        sellers = sellers[sellers["seller_id"].isin(items["seller_id"])]
        translations = translations[
            translations["product_category_name"].isin(products["product_category_name"].dropna())
        ]

    for col in ORDER_DATETIME_COLS:
        orders[col] = _parse_dt(orders[col])
    items["shipping_limit_date"] = _parse_dt(items["shipping_limit_date"])
    reviews["review_creation_date"] = _parse_dt(reviews["review_creation_date"])
    reviews["review_answer_timestamp"] = _parse_dt(reviews["review_answer_timestamp"])

    products = products.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )

    customers["customer_zip_code_prefix"] = customers["customer_zip_code_prefix"].astype(int)
    sellers["seller_zip_code_prefix"] = sellers["seller_zip_code_prefix"].astype(int)

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))

    _write_table(engine, customers, "customers")
    _write_table(engine, translations, "product_category_translations")
    _write_table(engine, products, "products")
    _write_table(engine, sellers, "sellers")
    _write_table(engine, orders, "orders")
    _write_table(engine, items, "order_items")
    _write_table(engine, payments, "order_payments")
    _write_table(engine, reviews, "order_reviews")

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))

    inspector = inspect(engine)
    counts = {table: conn_count(engine, table) for table in inspector.get_table_names()}
    logger.info("import_complete", extra={"tables": counts})
    engine.dispose()
    return counts


def conn_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)


def main() -> None:
    counts = import_dataset()
    for table, n in sorted(counts.items()):
        print(f"{table}: {n}")


if __name__ == "__main__":
    main()
