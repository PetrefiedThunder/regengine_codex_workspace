# Design-Partner Demo Script

Use this script for a 15-25 minute RegEngine Inflow Lab walkthrough with a design partner. It is written for mock-first demos where no live workspace traffic is sent unless everyone explicitly agrees to switch modes.

## Demo Goal

Show that the simulator can produce realistic FSMA 204 CTE flow data, preserve lot lineage through transformation, and derive FDA-request and EPCIS exports from stored records while keeping the RegEngine ingest contract stable.

## Pre-Demo Setup

Run these checks before the call:

```bash
pytest
python3 scripts/smoke_regression.py
node --check app/static/app.js
python3 -m compileall app scripts
git diff --check
```

Start the local server:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` and keep a terminal ready for quick API checks.

## Opening Talk Track

- "This is a mock-first FSMA 204 inflow simulator for RegEngine-compatible webhooks."
- "The live ingest contract stays intentionally small: top-level `source`, top-level `events[]`, and the documented per-event CTE fields."
- "By default everything posts to the built-in mock endpoint, so a demo cannot accidentally send live traffic."
- "The event log is the source of truth for lineage, FDA CSV exports, and EPCIS JSON-LD scaffolding."

## Happy-Path Walkthrough

1. Confirm operator context.
   - Dashboard action: point to the stats cards for `Tenant`, `Auth`, `Storage scope`, `Loop status`, and `Persist path`.
   - Expected result: local demos show tenant `local-demo`, auth `Off`, storage `Local`, loop `Stopped`.
   - Talking point: "A shared demo can use Basic Auth and tenant headers, but local mock mode stays frictionless."

2. Load the fresh-cut fixture.
   - Dashboard action: set delivery mode to `Mock RegEngine`, choose fixture `Fresh-cut transformation`, click `Load fixture`.
   - Expected result: scenario changes to `Fresh-cut processor`, total records becomes `13`, delivery monitor shows posted records, recent events include harvesting, cooling, packing, shipping, receiving, and transformation.
   - Talking point: "The fixture is deterministic so every partner sees the same batch, documents, and lot codes."

3. Inspect transformation lineage.
   - Dashboard action: paste `TLC-DEMO-FC-OUT-001` in lot lineage lookup and click `Trace lot`.
   - Expected result: lineage includes `TLC-DEMO-FC-HARVEST-001`, `TLC-DEMO-FC-HARVEST-002`, `TLC-DEMO-FC-PACK-001`, `TLC-DEMO-FC-PACK-002`, and `TLC-DEMO-FC-OUT-001`.
   - Talking point: "Transformation consumes packed ingredient lots and emits a new output lot. The trace can move backward to harvest and forward to shipment and receipt."

4. Show FDA-request export.
   - Dashboard action: set export preset to `Lot trace`, set Traceability Lot Code to `TLC-DEMO-FC-OUT-001`, click `Download CSV`.
   - Expected result: downloaded CSV includes `BATCH-DEMO-FC-001` and the transitive lot history.
   - API check:

```bash
curl "http://127.0.0.1:8000/api/mock/regengine/export/fda-request?preset=lot_trace&traceability_lot_code=TLC-DEMO-FC-OUT-001" | head
```

5. Show EPCIS export.
   - Dashboard action: with the same lot filter, click `Download EPCIS`.
   - Expected result: JSON-LD export includes an `EPCISDocument` with `ObjectEvent` and `TransformationEvent` entries.
   - API check:

```bash
curl "http://127.0.0.1:8000/api/mock/regengine/export/epcis?traceability_lot_code=TLC-DEMO-FC-OUT-001" | python3 -m json.tool | head -40
```

6. Demonstrate operator controls.
   - Dashboard action: click `Save scenario`, switch the scenario preset, click `Reset state`, then `Load saved`.
   - Expected result: the fresh-cut scenario and all 13 records return.
   - Talking point: "Design partners can rehearse the same story without rebuilding data by hand."

7. Optional live-ingest explanation.
   - Do not switch to live during a first demo unless a real workspace, API key, tenant id, and consent are ready.
   - Talking point: "Live mode targets `https://www.regengine.co/api/v1/webhooks/ingest`, requires API key and tenant id, and uses the same payload shape we just inspected."

## Reset Steps

Use this before each design-partner call:

```bash
curl -X POST http://127.0.0.1:8000/api/simulate/stop
curl -X POST http://127.0.0.1:8000/api/simulate/reset \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"fresh_cut_processor","batch_size":3,"seed":204,"delivery":{"mode":"mock"}}'
curl -X POST http://127.0.0.1:8000/api/demo-fixtures/fresh_cut_transformation/load \
  -H 'Content-Type: application/json' \
  -d '{"reset":true,"delivery":{"mode":"mock"}}'
```

Use this after a call if you want a blank local state:

```bash
curl -X POST http://127.0.0.1:8000/api/simulate/stop
curl -X POST http://127.0.0.1:8000/api/simulate/reset
```

For a shared demo tenant, add the tenant header to every reset command:

```bash
-H 'X-RegEngine-Tenant: partner-acme'
```

If Basic Auth is enabled, also add:

```bash
-u "$REGENGINE_BASIC_AUTH_USERNAME:$REGENGINE_BASIC_AUTH_PASSWORD"
```

## Recovery Notes

- If the dashboard looks stale, click `Refresh` or reload the browser tab.
- If the loop is still running, click `Stop` before loading fixtures or resetting.
- If live delivery fails, switch delivery mode to `Mock RegEngine` and use `Retry failed deliveries` to prove recovery behavior.
- If lineage for `TLC-DEMO-FC-OUT-001` is empty, reload the `Fresh-cut transformation` fixture.
- If downloaded exports are empty, confirm the event count is nonzero and the lot filter has no extra spaces.

## Questions To Capture

- Which CTEs or KDEs are missing from the partner's real workflow?
- Which identifiers matter most for their operators: lot code, GLN, reference document, PO, BOL, batch, or shipment id?
- Do they need tenant isolation by business unit, facility, customer, or demo workspace?
- Would they prefer FDA CSV, EPCIS JSON-LD, or both as the first export handoff?
- What dashboard status would make a failed live ingest easiest to understand?
