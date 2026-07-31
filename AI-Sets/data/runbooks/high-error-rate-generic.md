# Runbook: generic high error rate

## Symptom
Any service's `error_rate` metric crosses 5% for more than 2 minutes.

## Diagnosis steps
1. Identify which service and which error type dominates (`search_logs`).
2. Check whether the error rate correlates with a deploy in the last hour.
3. Check whether it correlates with an upstream dependency (see the specific
   runbook for that dependency if one exists, e.g. `payments-gateway-timeout.md`).

## Safe actions
- Gather logs and metrics for the affected window.
- Identify the top 3 error messages by frequency.

## Actions that need human approval
- Any rollback, restart, or scaling action.

## Escalation
If error rate exceeds 25% and affects a `critical` service (payments, checkout,
auth), page on-call immediately regardless of time of day.
