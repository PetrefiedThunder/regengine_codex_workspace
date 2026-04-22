from __future__ import annotations

import asyncio
from typing import Any

from .engine import LegitFlowEngine
from .mock_service import MockRegEngineService
from .models import (
    DestinationMode,
    IngestPayload,
    SimulationConfig,
    StepResponse,
    StoredEventRecord,
)
from .regengine_client import LiveRegEngineClient
from .store import EventStore


class SimulationController:
    def __init__(
        self,
        engine: LegitFlowEngine,
        store: EventStore,
        mock_service: MockRegEngineService,
        live_client: LiveRegEngineClient,
    ) -> None:
        self.engine = engine
        self.store = store
        self.mock_service = mock_service
        self.live_client = live_client
        self.config = SimulationConfig()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self, config: SimulationConfig) -> None:
        self.config = config
        if self.running:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if not self.running:
            return
        self._stop_event.set()
        assert self._task is not None
        await self._task
        self._task = None

    async def shutdown(self) -> None:
        await self.stop()

    async def reset(self, config: SimulationConfig | None = None) -> None:
        await self.stop()
        if config is not None:
            self.config = config
        self.engine.reset(self.config.seed)
        self.store.reset()
        self.mock_service.reset()

    async def step(self, batch_size: int | None = None) -> StepResponse:
        async with self._lock:
            size = batch_size or self.config.batch_size
            events = []
            lineages = []
            for _ in range(size):
                event, parent_lot_codes = self.engine.next_event()
                events.append(event)
                lineages.append(parent_lot_codes)

            payload = IngestPayload(source=self.config.source, events=events)
            response: dict[str, Any] | None = None
            delivery_status = "generated"
            error_message: str | None = None
            posted = 0
            failed = 0

            try:
                if self.config.delivery.mode == DestinationMode.MOCK:
                    response = self.mock_service.ingest(payload).model_dump(mode="json")
                    delivery_status = "posted"
                    posted = len(events)
                elif self.config.delivery.mode == DestinationMode.LIVE:
                    response = await self.live_client.ingest(payload, self.config)
                    delivery_status = "posted"
                    posted = len(events)
                else:
                    posted = 0
            except Exception as exc:  # pragma: no cover - exercised by live integration, not unit tests
                delivery_status = "failed"
                error_message = str(exc)
                failed = len(events)

            stored_records: list[StoredEventRecord] = []
            response_events = (response or {}).get("events", []) if response else []
            for index, event in enumerate(events):
                event_response = response_events[index] if index < len(response_events) else None
                stored_records.append(
                    StoredEventRecord(
                        payload_source=self.config.source,
                        event=event,
                        parent_lot_codes=lineages[index],
                        destination_mode=self.config.delivery.mode,
                        delivery_status=delivery_status,
                        delivery_response=event_response,
                        error=error_message,
                    )
                )
            self.store.add_many(stored_records)

            if delivery_status == "generated":
                posted = 0
                failed = 0
            elif delivery_status == "failed":
                posted = 0
            return StepResponse(
                generated=len(events),
                posted=posted,
                failed=failed,
                lot_codes=[event.traceability_lot_code for event in events],
                response=response,
            )

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            await self.step(self.config.batch_size)
            if self.config.interval_seconds <= 0:
                await asyncio.sleep(0)
            else:
                await asyncio.sleep(self.config.interval_seconds)

    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "config": self.config.model_dump(mode="json"),
            "stats": {
                **self.store.stats(),
                "engine": self.engine.snapshot(),
            },
        }
