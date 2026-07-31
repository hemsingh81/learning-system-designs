# Runbook: payments service — upstream gateway timeout

## Symptom
`payments` service logs show repeated `upstream call to payment-gateway timed out`
and/or `circuit breaker OPEN for payment-gateway`. Error rate on the `payments`
service rises sharply; p99 latency spikes above 1500ms.

## Likely causes
1. The third-party payment gateway is having an outage or degraded performance.
2. Our connection pool to the gateway is exhausted (too few connections configured).
3. A recent deploy changed the gateway timeout/retry settings.

## Diagnosis steps
1. Check `metrics.json` / your dashboard for `payments` error_rate and latency_ms_p99.
2. Search `app.log` for `circuit breaker OPEN` — if present, the breaker is already protecting you.
3. Check the payment gateway's public status page (if reachable) for a known outage.

## Safe actions (read-only, always OK)
- Pull recent orders with `status=failed AND fail_reason=payment_gateway_timeout`.
- Summarize the time window and blast radius (how many customers affected).

## Actions that need human approval
- Restarting the `payments` service (`restart_service`) — only helps if the pool
  is exhausted, not if the upstream gateway itself is down. Restarting during a
  genuine upstream outage does nothing and adds risk.
- Scaling `payments` up (`scale_service`) — only helps for load-related timeouts,
  not upstream outages.

## Escalation
If the gateway's own status page confirms an outage, this is NOT fixable on our
side. Post a customer-facing status update and page the payments team lead —
do not keep retrying automated fixes.
