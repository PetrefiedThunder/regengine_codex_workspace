# Prompt for Codex

Use this prompt in the Codex app, CLI, or IDE extension from the repository root.

---

Read `AGENTS.md` and the RegEngine skill before touching code.

I need you to harden this repository into a design-partner-ready RegEngine inflow simulator.

Goals:

1. Keep the current RegEngine webhook contract intact.
2. Preserve mock-first safety.
3. Make the lot lineage more believable, not more random.
4. Improve observability so I can demo the flow clearly.

Work plan:

- Run the existing test suite first.
- Audit the current simulator architecture and list the highest-risk gaps.
- Implement server-sent events so the dashboard updates in real time without polling.
- Add scenario presets for:
  - leafy greens supplier
  - fresh-cut processor
  - retailer readiness demo
- Add CSV bulk import support for seed lots or scheduled events.
- Add a replay mode that can send previously persisted JSONL events back through mock or live ingest.
- Add tests for every new feature.
- Update the README with exact run instructions and examples.

Constraints:

- Do not introduce React, Vue, or another frontend framework unless absolutely necessary.
- Keep the code understandable for a solo founder.
- Keep delivery mode defaulted to `mock`.
- Do not remove current endpoints unless you replace them cleanly and update tests.

At the end:

- summarize what changed
- list any open risks
- show the commands you ran

---
