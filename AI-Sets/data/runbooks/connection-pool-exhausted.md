# Runbook: connection pool exhausted

## Symptom
Logs show `connection pool exhausted: 0/N connections available`.

## Likely causes
1. Downstream dependency (DB or external API) is slow, so connections are
   held longer than usual and the pool never frees up.
2. Pool size is configured too small for current traffic.
3. A connection leak in application code (connections opened but not released).

## Diagnosis steps
1. Check if the downstream dependency (e.g. payment gateway, database) is
   itself slow or down — if so, this is a symptom, not the root cause.
2. Check whether pool exhaustion started right when a deploy happened
   (possible leak) or right when a downstream slowdown started (possible
   cascading failure).

## Safe actions
- Gather the timestamp pool exhaustion started and correlate with logs.

## Actions that need human approval
- Restarting the service to clear the pool (temporary relief only).
- Increasing pool size (config change, needs review).
