---
name: regengine-api-contract
description: Use this skill when working on RegEngine ingest payloads, FSMA 204 CTE/KDE simulation, lineage tracing, FDA-request export features, or anything that must preserve the current RegEngine webhook contract.
---

# RegEngine API contract skill

## Use this skill when

- the task mentions RegEngine
- the task mentions FSMA 204, CTEs, KDEs, traceability lots, or FDA-request exports
- you are changing ingest payload fields, simulator outputs, or lineage behavior
- you are adding a new delivery target or export path

## Core contract

Live delivery targets the documented RegEngine ingest webhook:

- endpoint: `https://www.regengine.co/api/v1/webhooks/ingest`
- required headers:
  - `X-RegEngine-API-Key`
  - `X-Tenant-ID`
  - `Content-Type: application/json`

Expected top-level payload:

```json
{
  "source": "erp",
  "events": [
    {
      "cte_type": "receiving",
      "traceability_lot_code": "00012345678901-LOT-2026-001",
      "product_description": "Romaine Lettuce",
      "quantity": 500,
      "unit_of_measure": "cases",
      "location_name": "Distribution Center #4",
      "timestamp": "2026-02-05T08:30:00Z",
      "kdes": {
        "receive_date": "2026-02-05",
        "receiving_location": "Distribution Center #4",
        "ship_from_location": "Valley Fresh Farms"
      }
    }
  ]
}
```

## Supported CTEs in this repo

- `harvesting`
- `cooling`
- `initial_packing`
- `shipping`
- `receiving`
- `transformation`

## Guardrails

- Never break the public ingest shape without updating the mock service, tests, README, and frontend.
- If you add new KDEs, keep them additive and preserve existing keys.
- When extending the engine, maintain valid lineage between upstream and downstream lots.
- Prefer mock-first development. Live delivery should stay opt-in.

## Checklist before you stop

1. Run `pytest`.
2. Confirm new payload fields serialize cleanly.
3. Confirm the dashboard still renders the latest events.
4. Confirm lineage lookup still works for transformed lots.
