# RegEngine Inflow Lab

A Codex-ready starter app for simulating realistic FSMA 204 traceability traffic into RegEngine.

This project does four useful things out of the box:

1. Generates linked **Critical Tracking Events (CTEs)** instead of random disconnected rows.
2. Emits **RegEngine-compatible ingest payloads** that follow the current `POST /api/v1/webhooks/ingest` shape from the RegEngine integration guide.
3. Runs in **mock mode** by default so you can validate the full flow without touching production.
4. Exposes a simple **web dashboard** for starting, stopping, stepping, tracing lot lineage, and exporting a mock FDA request CSV.

## What this app simulates

The generator walks lots through a realistic supply-chain lifecycle:

- harvesting
- cooling
- initial packing
- shipping
- receiving
- transformation
- downstream shipping + receiving

That gives you lineage you can actually demo:

- a harvested lot becomes a packed lot
- a packed lot gets shipped to a processor or distribution center
- received processor lots can be transformed into a new output lot
- transformed lots move downstream to a DC and then retail

## RegEngine contract this app targets

The live delivery client is aligned with the current RegEngine integration docs:

- Endpoint: `https://www.regengine.co/api/v1/webhooks/ingest`
- Headers:
  - `X-RegEngine-API-Key`
  - `X-Tenant-ID`
  - `Content-Type: application/json`
- Payload shape:

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

The mock FDA export in this repo mirrors RegEngine's documented 11-column request export shape.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```bash
http://127.0.0.1:8000
```

## Running tests

```bash
pytest
```

## Delivery modes

### 1. Mock RegEngine

Default mode.

- No credentials required.
- Events are accepted by the built-in mock ingest service.
- Response objects include `event_id`, `sha256_hash`, and `chain_hash` so the flow feels real.

### 2. Live RegEngine

Use this when you want to send traffic to a real RegEngine workspace.

In the dashboard set:

- Delivery mode = `live`
- API key
- Tenant ID
- Optional endpoint override

Or call the API directly with:

```bash
curl -X POST http://127.0.0.1:8000/api/simulate/start \
  -H 'Content-Type: application/json' \
  -d '{
    "config": {
      "source": "codex-simulator",
      "interval_seconds": 1.0,
      "batch_size": 3,
      "seed": 204,
      "persist_path": "data/events.jsonl",
      "delivery": {
        "mode": "live",
        "endpoint": "https://www.regengine.co/api/v1/webhooks/ingest",
        "api_key": "YOUR_API_KEY",
        "tenant_id": "YOUR_TENANT_UUID"
      }
    }
  }'
```

### 3. Generate only

Use `none` when you just want to create and persist events locally.

## API endpoints in this repo

### Simulator control

- `GET /api/health`
- `GET /api/simulate/status`
- `POST /api/simulate/start`
- `POST /api/simulate/stop`
- `POST /api/simulate/step`
- `POST /api/simulate/reset`

### Inspection

- `GET /api/events`
- `GET /api/lineage/{traceability_lot_code}`

### Mock RegEngine

- `POST /api/mock/regengine/ingest`
- `GET /api/mock/regengine/export/fda-request`

## Why this repo is Codex-ready

Codex works best when the repo tells it exactly how to behave. This project includes:

- `AGENTS.md` for repository instructions
- `.agents/skills/regengine-api-contract/` for a focused RegEngine skill
- `PROMPT_FOR_CODEX.md` with a paste-ready task prompt
- tests so Codex can verify changes before it stops


## Codex autopilot via GitHub Actions

This repo now includes an unattended Codex workflow at `.github/workflows/codex-autopilot.yml`.

What it does:

- runs on a weekday schedule plus manual dispatch
- installs the repo dependencies and runs `pytest` before Codex touches code
- runs Codex against `.github/codex/prompts/autobuild.md`
- runs `pytest` again after Codex changes
- uploads the Codex transcript and patch as workflow artifacts
- opens or updates a pull request on `codex/autopilot` when there is a passing diff
- can optionally auto-merge that PR when you explicitly enable it

### Required secret

- `OPENAI_API_KEY`

### Optional secret

- `CODEX_PR_TOKEN`

Use `CODEX_PR_TOKEN` when you want Codex-created PRs to trigger downstream workflows or when your repository rules require a token beyond the default `GITHUB_TOKEN`.

### Optional repository variable

- `CODEX_AUTO_MERGE=true`

Keep this off until you trust the backlog and branch-protection setup. You can also enable auto-merge per run from the manual `workflow_dispatch` input.

### Standing backlog for unattended runs

The scheduled workflow does not rely on a human-written prompt each time. Instead it reads:

- `AGENTS.md`
- `.agents/skills/regengine-api-contract/SKILL.md`
- `AUTOPILOT_TASKS.md`
- `.github/codex/prompts/autobuild.md`

That gives Codex a stable operating playbook and a prioritized task queue.

### Recommended GitHub settings

- allow GitHub Actions to create pull requests
- enable auto-merge only after branch protection is configured the way you want
- add branch protection for `main` if you want Codex PRs gated by CI

## Suggested next upgrades

These are the highest-leverage improvements to hand Codex next:

1. Add server-sent events or WebSockets for live event streaming.
2. Add CSV/XLSX import so simulated suppliers can replay bulk onboarding files.
3. Add scenario presets by retailer, commodity, and facility count.
4. Add authentication and per-tenant storage.
5. Add a real FDA sortable spreadsheet validator.
6. Add EPCIS 2.0 export and import adapters.

## Project layout

```text
app/
  controller.py
  engine.py
  main.py
  mock_service.py
  models.py
  regengine_client.py
  store.py
  static/
    app.js
    index.html
    styles.css
.agents/skills/regengine-api-contract/
AGENTS.md
AUTOPILOT_TASKS.md
PROMPT_FOR_CODEX.md
.github/
  codex/
    prompts/
      autobuild.md
  workflows/
    ci.yml
    codex-autopilot.yml
tests/
```
