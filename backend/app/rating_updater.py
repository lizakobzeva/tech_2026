import asyncio
import logging

from app.database import async_session_factory
from app.rating_service import recalculate_all_ratings

logger = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 300


class RatingUpdater:
    def __init__(self, interval_seconds: int = UPDATE_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                async with async_session_factory() as session:
                    updated = await recalculate_all_ratings(session)
                logger.info("Background rating update finished, users=%d", updated)
            except Exception:
                logger.exception("Background rating update failed")

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                continue

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Rating updater started (interval=%ss)", self.interval_seconds)

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None
        logger.info("Rating updater stopped")


rating_updater = RatingUpdater()
