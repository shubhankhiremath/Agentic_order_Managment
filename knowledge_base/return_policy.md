# Return Policy

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## Eligibility period

- A return request may be considered only for orders with status `delivered`.
- The demo eligibility window is **7 calendar days** after `order_delivered_customer_date`.
- If the actual delivery date is missing, the assistant cannot confirm eligibility and should say so.

## Condition

- Items should be unused and in original packaging when a return is requested.
- Damaged or defective items may be returned within the same 7-day window; the customer should describe the damage in a support ticket.

## Exclusions (demo)

- Orders with status `canceled` or `unavailable` are not returnable (there is no fulfilled shipment).
- Orders that were never delivered (`created`, `approved`, `invoiced`, `processing`, `shipped`) are not in the return window; use cancellation or delivery-exception handling instead.
- This dataset has **no product titles**. Category-only information cannot prove a category exclusion; do not invent product-specific exclusions.

## How to request

- Create a simulated support ticket with issue `return_request` and a description of the reason.
