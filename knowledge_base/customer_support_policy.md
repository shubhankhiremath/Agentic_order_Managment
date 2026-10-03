# Customer Support Policy

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## When a support ticket should be created

Create a **simulated** local ticket when:

- The customer reports a delay and demo rules confirm `DELIVERY_DELAY` or `SHIPPED_NOT_DELIVERED`.
- The customer requests a return, refund discussion, or cancellation and the order exists.
- Payment data is missing or `not_defined`.

## Ticket contents

- `order_id` must exist in SQLite.
- `issue` should be a short code such as `delivery_delay`, `return_request`, `cancellation_request`, `payment_issue`.
- `description` should summarize customer intent in plain language.

## Limitations

- Tickets are stored only in local SQLite (`support_tickets`).
- Creating a ticket does **not** notify sellers, carriers, or Olist.
- Do not promise callback times or human agent names.
