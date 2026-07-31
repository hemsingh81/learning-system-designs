# Runbook: auth service degraded

## Symptom
`auth` service latency or error rate rises; users report failed logins.

## Diagnosis steps
1. Check `auth` service metrics for latency_ms_p99 and error_rate.
2. Search logs for `auth` ERROR lines in the affected window.
3. Check whether `payments` or `checkout` are also affected (auth is a
   shared dependency — a cascading failure is common).

## Safe actions
- Gather the error breakdown by type (expired token vs. DB error vs. timeout).

## Actions that need human approval
- Restarting `auth` — this logs out active sessions; treat as high impact.

## Escalation
Auth outages are always `critical` — escalate immediately, do not wait to
gather more evidence first. Gather evidence WHILE escalating, not before.
