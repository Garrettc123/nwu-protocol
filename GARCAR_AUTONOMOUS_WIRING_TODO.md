# Garcar Autonomous Wiring TODO for nwu-protocol

Role: `blockchain_protocol`

_Live fan-out: 2026-09-12 (wet / CASH_LOCK)_

## Required Garcar Base Contract
- [x] `/health` — present (aligned with system/version/timestamp)
- [x] `/meta` — **added** (role blockchain_protocol, contract_version 1.0.0)
- [x] `/metrics` — **added** (JSON counters)
- [x] `/events` — **added** (in-memory ring)

## Event Bus Wiring
- [ ] Emit required events for this role (`garcar.nwu-protocol.{event_type}`).
- [ ] Consume required arbitrage/control-plane events.
- Remaining: NATS/Redis Streams client; Zeus/Atlas dashboard visibility; contract+event tests.

## Current Full-Stack Components
- backend_api: FastAPI (`app.py`)
- frontend_ui: Present
- payment_hook: Present
- event_bus_connected: False
- observability_connected: False

## Wiring Tasks
1. ~~Add or verify Garcar Base Contract endpoints.~~ **DONE**
2. Add NATS/Redis Streams client and emit/consume required topics.
3. Ensure metrics/events appear in Zeus/Atlas dashboards.
4. Add tests for contract + event wiring.

## Safety
- Draft PR only. Do not auto-merge.
- Respect CASH_LOCK: no live spend / no silent outbound.
