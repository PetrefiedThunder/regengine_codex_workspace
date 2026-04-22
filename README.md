# RegEngine Inflow Lab

A mock-first FSMA 204 traceability simulator that emits **RegEngine-compatible ingest payloads** into a realistic supply-chain lifecycle. Ships with a FastAPI backend, a lightweight dashboard, and a built-in mock RegEngine endpoint for safe local testing.

## Table of contents

- [What it does](#what-it-does)
- [Project layout](#project-layout)
- [Quick start (local dev)](#quick-start-local-dev)
- [Running tests](#running-tests)
- [Delivery modes](#delivery-modes)
- [API reference](#api-reference)
- [RegEngine payload contract](#regengine-payload-contract)
- [Deployment](#deployment)
  - [macOS LaunchAgent (auto-start on login)](#macos-launchagent-auto-start-on-login)
  - [Linux systemd unit](#linux-systemd-unit)
  - [Docker (optional)](#docker-optional)
- [Logs and troubleshooting](#logs-and-troubleshooting)
- [Contributing](#contributing)

## What it does

The generator walks lots through a realistic supply-chain lifecycle so the resulting trace feels legitimate rather than random:

1. **Harvesting** originates at farms
2. **Cooling** moves harvested lots through cooler facilities
3. **Initial packing** creates downstream packed lots
4. **Shipping** creates a believable destination and reference document
5. **Receiving** corresponds to an actual prior shipment
6. **Transformation** consumes input lots and emits a new output lot
7. **Downstream shipping + receiving** moves transformed lots to DCs and retail

Each event is persisted with `event_id`, `sha256_hash`, and `chain_hash` so the flow feels production-like, and you can trace lot lineage forward and backward through the dashboard or API.

## Project layout

```text
app/
  controller.py          # Simulator lifecycle (start/stop/step/reset)
  engine.py              # CTE generation and lot lineage logic
  main.py                # FastAPI app and route wiring
  mock_service.py        # Built-in mock RegEngine ingest endpoint
  models.py              # Pydantic models for config, events, payloads
  regengine_client.py    # HTTP client for live RegEngine delivery
  store.py               # Event persistence (JSONL)
  static/                # Dashboard (vanilla JS, HTML, CSS)
.agents/skills/regengine-api-contract/
.github/
  codex/prompts/autobuild.md
  workflows/ci.yml
  workflows/codex-autopilot.yml
tests/
AGENTS.md                # Repository instructions for Codex-style agents
AUTOPILOT_TASKS.md       # Standing backlog for unattended runs
PROMPT_FOR_CODEX.md      # Paste-ready Codex task prompt
pyproject.toml
requirements.txt
```

## Quick start (local dev)

Requires **Python 3.11+**.

```bash
# From the project root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the dev server (auto-reload)
uvicorn app.main:app --reload
```

Then open:

```
http://127.0.0.1:8000
```

The dashboard lets you start/stop/step/reset the simulator, inspect recent events, trace lot lineage, and export a mock FDA request CSV. Delivery mode defaults to **`mock`** so no credentials are required.

## Running tests

```bash
pytest
```

The suite covers payload shape, engine determinism, and the HTTP API contract.

## Delivery modes

The simulator supports three delivery modes, configured via the `delivery.mode` field:

### `mock` (default)
No credentials required. Events are accepted by the built-in mock ingest service and returned with a synthetic `event_id`, `sha256_hash`, and `chain_hash`. Safe for demos and design-partner testing.

### `live`
Sends real traffic to a RegEngine workspace. Configure from the dashboard or via the API with:

- `api_key`
- `tenant_id`
- Optional `endpoint` override (defaults to `https://www.regengine.co/api/v1/webhooks/ingest`)

### `none`
Generates and persists events locally without delivering them anywhere. Useful for seeding fixtures.

## API reference

### Simulator control

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Liveness probe + current config snapshot |
| `GET` | `/api/simulate/status` | Running state, config, and aggregate stats |
| `POST` | `/api/simulate/start` | Start the loop (accepts a `config` body) |
| `POST` | `/api/simulate/stop` | Stop the loop |
| `POST` | `/api/simulate/step` | Emit one batch synchronously |
| `POST` | `/api/simulate/reset` | Clear state and persisted events |

### Inspection

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/events` | List persisted events |
| `GET` | `/api/lineage/{traceability_lot_code}` | Full lineage graph for a lot |

### Mock RegEngine

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/mock/regengine/ingest` | Accepts RegEngine-shaped payloads |
| `GET` | `/api/mock/regengine/export/fda-request` | Mock 11-column FDA request CSV |

### Example: start the simulator in live mode

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

### Example: step once and inspect events

```bash
curl -X POST http://127.0.0.1:8000/api/simulate/step
curl http://127.0.0.1:8000/api/events
```

### Example: trace a lot

```bash
curl http://127.0.0.1:8000/api/lineage/TLC-20260421-000003
```

## RegEngine payload contract

The live delivery client targets the current RegEngine webhook shape:

- **Endpoint:** `https://www.regengine.co/api/v1/webhooks/ingest`
- **Headers:** `X-RegEngine-API-Key`, `X-Tenant-ID`, `Content-Type: application/json`
- **Payload:**

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

The mock FDA export mirrors RegEngine's documented 11-column request export shape.

## Deployment

### macOS LaunchAgent (auto-start on login)

A LaunchAgent is the simplest way to keep the server running on a developer Mac. The agent starts the server on login and restarts it if it crashes.

1. Install dependencies as described in [Quick start](#quick-start-local-dev).
2. Create `~/Library/LaunchAgents/com.regengine.uvicorn.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.regengine.uvicorn</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOU/regengine_codex_workspace/.venv/bin/uvicorn</string>
    <string>app.main:app</string>
    <string>--host</string><string>127.0.0.1</string>
    <string>--port</string><string>8000</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/YOU/regengine_codex_workspace</string>

  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>

  <key>StandardOutPath</key>
  <string>/Users/YOU/regengine_codex_workspace/uvicorn.out.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOU/regengine_codex_workspace/uvicorn.err.log</string>
</dict>
</plist>
```

Replace `/Users/YOU` with your home directory. **Note:** keep the project outside of `~/Desktop`, `~/Documents`, or `~/Downloads`; macOS privacy (TCC) blocks launchd from reading those folders without Full Disk Access.

3. Load and verify:

```bash
launchctl load -w ~/Library/LaunchAgents/com.regengine.uvicorn.plist
launchctl list | grep com.regengine.uvicorn     # should show a numeric PID
curl http://127.0.0.1:8000/api/health
```

4. To stop or restart:

```bash
launchctl unload ~/Library/LaunchAgents/com.regengine.uvicorn.plist
launchctl load   ~/Library/LaunchAgents/com.regengine.uvicorn.plist
```

### Linux systemd unit

Create `/etc/systemd/system/regengine.service`:

```ini
[Unit]
Description=RegEngine Inflow Lab
After=network.target

[Service]
Type=simple
User=YOU
WorkingDirectory=/home/YOU/regengine_codex_workspace
ExecStart=/home/YOU/regengine_codex_workspace/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now regengine
sudo systemctl status regengine
journalctl -u regengine -f    # live logs
```

### Docker (optional)

A minimal image is straightforward:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t regengine-inflow-lab .
docker run --rm -p 8000:8000 regengine-inflow-lab
```

## Logs and troubleshooting

| Location | What it contains |
|---|---|
| `uvicorn.out.log` | Server stdout (request logs, lifecycle messages) |
| `uvicorn.err.log` | Server stderr (Python tracebacks, startup errors) |
| `data/events.jsonl` | Persisted simulator events |

Common checks:

```bash
# Is the service running?
launchctl list | grep com.regengine.uvicorn   # macOS
systemctl status regengine                    # Linux

# Health probe
curl http://127.0.0.1:8000/api/health

# Tail logs (macOS)
tail -f ~/regengine_codex_workspace/uvicorn.err.log
```

If the health check fails, the first place to look is `uvicorn.err.log` for a Python traceback.

## Contributing

Before touching code, read:

- `AGENTS.md` — repository operating agreements
- `.agents/skills/regengine-api-contract/SKILL.md` — payload contract details
- `AUTOPILOT_TASKS.md` — prioritized backlog

House rules in short:

- Keep the live ingest payload compatible with the RegEngine contract.
- Preserve **mock mode** as the default.
- Maintain lot lineage across CTEs.
- Run `pytest` after any Python change.
- Prefer small, composable modules and deterministic tests.
