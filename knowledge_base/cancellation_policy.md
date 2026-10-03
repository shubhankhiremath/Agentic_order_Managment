# Cancellation Policy

> **Demo policy created for this portfolio project. This is not an official Olist policy.**

## When cancellation may be requested

- Cancellation **requests** may be discussed when `order_status` is one of: `created`, `approved`, `invoiced`, `processing`.
- Once `shipped` or `delivered`, cancellation is not offered; use return or exception handling instead.
- Orders already `canceled` or `unavailable` should be described as closed.

## Demo limitation

- This assistant **does not** execute cancellations against a commerce platform.
- If a user asks to cancel, explain the demo rule, check current status with tools, and offer a simulated support ticket (`issue`: `cancellation_request`).

## Payment

- For unpaid or pre-ship statuses, tell the user that a real marketplace would typically stop capture or reverse authorization. Do not state that a refund already occurred.
