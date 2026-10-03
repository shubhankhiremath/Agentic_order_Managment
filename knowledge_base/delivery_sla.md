# Delivery SLA (Demo)

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## How this demo system determines exceptions

Exception detection is **deterministic** and implemented in code (`backend/services/exception_service.py`). The LLM must not recalculate dates.

### Delivered late

- Status is `delivered`.
- `order_delivered_customer_date` (date) is after `order_estimated_delivery_date` (date).
- Severity is MEDIUM, or HIGH if the delay is 7 or more days.

### Missing delivery information

- Status is `delivered` but `order_delivered_customer_date` is null.

### Shipped but not delivered

- Status is `shipped`.
- If estimated delivery is before the dataset as-of date **2018-10-17**, severity is HIGH (`SHIPPED_NOT_DELIVERED`).
- Otherwise the order is flagged as in-transit (LOW).

### Approved / invoiced / processing but not shipped

- Status in `approved`, `invoiced`, `processing` and carrier date is null.

### Long delivery duration

- Delivered orders where actual delivery minus purchase date is 30 or more days.

## Customer communication

- Quote the estimated and actual timestamps from tools.
- State that these SLA rules are demo-only.
