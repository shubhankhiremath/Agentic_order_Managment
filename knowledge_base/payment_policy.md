# Payment Policy

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## Accepted methods in this dataset

- `credit_card` — may include installments (`payment_installments`).
- `boleto` — Brazilian bank slip.
- `debit_card`
- `voucher` — may appear with other methods on the same order (`payment_sequential`).

## Multiple payments

- An order may have several payment rows. Sum `payment_value` for the total recorded tender.

## Anomalies

- Missing payment rows, `payment_type = not_defined`, or `payment_value = 0` are demo payment exceptions. Escalate with a support ticket rather than guessing.

## Security

- The dataset does not include card numbers, PIX keys, or bank accounts. Never fabricate them.
