# Shipping Policy

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

This document describes synthetic shipping rules used by the Agentic Order Management assistant.

## Standard delivery

- The promised arrival window is the order's `order_estimated_delivery_date` from the commerce database.
- Standard delivery is the default for all marketplace orders in this demo.
- Freight charged on each order item (`freight_value`) is treated as the shipping fee already paid.

## Express delivery

- This demo catalog does not contain a separate express SKU flag.
- If a user asks for express shipping, explain that express upgrades are **not available in this demo dataset**.

## Delayed delivery

- An order is treated as delayed when it is `delivered` and the actual customer delivery date is **after** the estimated delivery date (calendar-day comparison).
- Open orders (`shipped`, `approved`, `invoiced`, `processing`) are evaluated against the dataset as-of date documented in `docs/business_rules.md`.

## Seller ship-by date

- Each item has a `shipping_limit_date`. Missing that date after approval may be flagged as incomplete logistics data, not as a customer-facing SLA miss by itself.
