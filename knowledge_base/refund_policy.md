# Refund Policy

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## Payment refund process

- Refunds in this demo are **simulated only**. No payment provider is charged or credited.
- A refund discussion may start after a valid return request or a confirmed delivery exception.
- Original payment method is taken from `order_payments.payment_type` (`credit_card`, `boleto`, `voucher`, `debit_card`).

## Timing (demo)

- After a demo refund is approved in support, communicate a **5 to 10 business day** status window.
- Split payments (multiple `payment_sequential` rows) should be mentioned; each method would be reversed separately in a real system.

## Refund status

- Ticket statuses used locally: `open`, `in_review`, `resolved`.
- There is no live refund ledger. Never claim money has been returned to the customer's bank.

## Not eligible

- `payment_type` of `not_defined` or missing payment rows should be escalated; do not invent a refund path.
