# Postmortem 001 — Price unit mismatch simulation

> Это запланированная simulation. Заполнить фактическими временем, impact и evidence только после запуска.

## Incident

| Field | Value |
|---|---|
| Date/time (UTC) | TBD |
| Severity | TBD |
| Detected by | TBD |
| Duration | TBD |
| Affected version | TBD |

## Impact

Какие requests/models/features затронуты? Привести измеримые значения: error/fallback rate, score distribution, quality proxy и latency. Не заполнять оценками без данных.

## Detection

Какой alert/dashboard обнаружил отклонение, какой порог сработал, сколько заняло обнаружение?

## Root cause

Training интерпретировал `item_price` в EUR, тогда как replay/online producer отправил цену в cents без обновления schema/`currency_unit`. Описать фактическую цепочку после simulation и почему существующая validation не остановила её раньше.

## Resolution

1. Mitigation/rollback: TBD.
2. Исправление producer/normalizer: TBD.
3. Backfill/invalidation затронутых online features/index: TBD.
4. Verification и время восстановления: TBD.

## Prevention

- Explicit `currency` и `price_unit` в event schema.
- Range/unit validation до materialization.
- Contract compatibility test producer → consumer → feature store.
- Alert на price and prediction drift.
- Regression test с EUR/cents fixture.

## Lessons and follow-ups

| Action | Owner | Due date | Status |
|---|---|---|---|
| TBD | TBD | TBD | open |
