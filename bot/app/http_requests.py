from __future__ import annotations

import logging
from typing import Optional

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, base_url: str = settings.BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def register_user(self, telegram_id: int, referal_id: Optional[int] = None) -> dict:
        session = await self._get_session()
        payload = {"telegram_id": telegram_id}
        if referal_id is not None:
            payload["referal_id"] = referal_id

        async with session.post(f"{self.base_url}/api/users/register", json=payload) as resp:
            data = await resp.json()
            if resp.status == 409:
                logger.info("User %d already registered", telegram_id)
                return await self.get_user(telegram_id)
            resp.raise_for_status()
            return data

    async def get_user(self, telegram_id: int) -> dict:
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/users/{telegram_id}") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_user(self, telegram_id: int, **kwargs) -> dict:
        session = await self._get_session()
        async with session.patch(
            f"{self.base_url}/api/users/{telegram_id}", json=kwargs
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def send_interaction(self, requester_id: int, responser_id: int, is_like: bool) -> dict:
        session = await self._get_session()
        payload = {
            "requester_telegram_id": requester_id,
            "responser_telegram_id": responser_id,
            "is_like": is_like,
        }
        async with session.post(f"{self.base_url}/api/interactions", json=payload) as resp:
            data = await resp.json()
            if resp.status == 409:
                logger.info("Interaction already exists between %d and %d", requester_id, responser_id)
                return data
            resp.raise_for_status()
            return data

    async def get_rating(self, telegram_id: int) -> dict:
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/users/{telegram_id}/rating") as resp:
            resp.raise_for_status()
            return await resp.json()


backend_client = BackendClient()
