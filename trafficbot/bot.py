"""Core traffic generation logic."""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Iterable, Optional

import aiohttp

from .config import CampaignConfig, VisitProfile
from .metrics import VisitMetrics
from .proxy import ProxyRotator
from .user_agents import choose_user_agent

_LOGGER = logging.getLogger(__name__)


class TrafficBot:
    """High level runner that coordinates visits according to a campaign."""

    def __init__(
        self,
        config: CampaignConfig,
        *,
        proxies: ProxyRotator | None = None,
        user_agents: Iterable[str] | None = None,
        request_timeout: float = 30.0,
    ) -> None:
        self.config = config
        self.proxies = proxies
        self.user_agents = list(user_agents) if user_agents else []
        self.request_timeout = request_timeout
        self.metrics = VisitMetrics()

    async def run(self) -> VisitMetrics:
        """Execute the configured campaign and return metrics."""

        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        connector = aiohttp.TCPConnector(limit=self.config.concurrency)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            semaphore = asyncio.Semaphore(self.config.concurrency)
            tasks = []
            visit_index = 0
            for profile in self.config.visit_profiles:
                for _ in range(profile.visits):
                    visit_index += 1
                    tasks.append(
                        asyncio.create_task(
                            self._bounded_visit(
                                semaphore,
                                session,
                                profile,
                                visit_index,
                            )
                        )
                    )
                    if self.config.delay_between_visits:
                        await asyncio.sleep(self.config.delay_between_visits)
                if self.config.delay_between_batches:
                    await asyncio.sleep(self.config.delay_between_batches)

            if tasks:
                await asyncio.gather(*tasks)

        _LOGGER.info("Campaign %s finished. %s", self.config.name, self.metrics.as_text())
        return self.metrics

    async def _bounded_visit(
        self,
        semaphore: asyncio.Semaphore,
        session: aiohttp.ClientSession,
        profile: VisitProfile,
        visit_index: int,
    ) -> None:
        async with semaphore:
            await self._perform_visit(session, profile, visit_index)

    async def _perform_visit(
        self,
        session: aiohttp.ClientSession,
        profile: VisitProfile,
        visit_index: int,
    ) -> None:
        headers = self._build_headers(profile)
        params = self._build_params(profile)
        proxy = self._get_proxy()
        duration = 0.0
        start_time = time.perf_counter()
        try:
            if self.config.dry_run:
                simulated = random.uniform(profile.min_duration, profile.max_duration)
                await asyncio.sleep(min(simulated, 1.0))
                _LOGGER.info("[Dry-Run] Visit %s -> %s", visit_index, profile.url)
                self.metrics.record_success(simulated)
                return

            async with session.get(profile.url, headers=headers, params=params, proxy=proxy) as response:
                await response.read()
                duration = time.perf_counter() - start_time
                wait_time = max(0.0, random.uniform(profile.min_duration, profile.max_duration) - duration)
                if wait_time:
                    await asyncio.sleep(wait_time)
                _LOGGER.debug(
                    "Visit %s -> %s [%s] via %s", visit_index, profile.url, response.status, proxy or "direct"
                )
                self.metrics.record_success(duration)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            duration = time.perf_counter() - start_time
            reason = exc.__class__.__name__
            _LOGGER.warning("Visit %s failed: %s", visit_index, exc)
            self.metrics.record_failure(reason)
            if profile.min_duration > 0:
                await asyncio.sleep(random.uniform(0, profile.min_duration))

    def _build_headers(self, profile: VisitProfile) -> dict[str, str]:
        if self.config.rotate_user_agents:
            user_agent = choose_user_agent(self.user_agents or None)
        else:
            user_agent = (self.user_agents or [choose_user_agent()])[0]
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }
        if profile.referrers:
            headers["Referer"] = random.choice(profile.referrers)
        return headers

    def _build_params(self, profile: VisitProfile) -> Optional[dict[str, str]]:
        if profile.keywords:
            return {"q": random.choice(profile.keywords)}
        return None

    def _get_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        try:
            return self.proxies.next()
        except StopIteration:
            return None
