# Exception Handling

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## Severity

- **HIGH**: late by 7+ days, shipped past estimate with no delivery, stuck pre-ship past estimate.
- **MEDIUM**: shorter late delivery, missing delivery timestamp, missing payments, long duration.
- **LOW**: in-transit within estimate, undefined/zero payment flags.

## Escalation

- HIGH exceptions: create a simulated support ticket unless one is clearly unnecessary.
- MEDIUM: offer a ticket and explain the demo evidence.
- LOW: explain status; ticket only if the customer asks.

## Evidence

- Always ground the explanation in tool `evidence` fields (dates, status, payment types).
- Do not invent carrier names or tracking numbers; they are not in the dataset.
