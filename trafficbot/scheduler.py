"""Campaign scheduling helpers."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .bot import TrafficBot
from .config import CampaignConfig
from .proxy import ProxyRotator
from .metrics import VisitMetrics


@dataclass(slots=True)
class ScheduledCampaign:
    """Run a campaign repeatedly with a fixed interval."""

    config_path: Path
    interval: float
    iterations: Optional[int] = None
    proxy_source: str | Path | None = None

    async def run(self) -> None:
        iteration = 0
        while self.iterations is None or iteration < self.iterations:
            iteration += 1
            config = CampaignConfig.from_file(self.config_path)
            proxies = ProxyRotator.from_source(self.proxy_source) if self.proxy_source else None
            start = datetime.utcnow()
            bot = TrafficBot(config, proxies=proxies)
            await bot.run()
            if self.iterations is not None and iteration >= self.iterations:
                break
            elapsed = (datetime.utcnow() - start).total_seconds()
            wait_time = max(0.0, self.interval - elapsed)
            if wait_time:
                await asyncio.sleep(wait_time)


def run_now(config_path: str | Path, *, proxy_source: str | Path | None = None) -> VisitMetrics:
    """Convenience helper to run a single campaign synchronously."""

    config = CampaignConfig.from_file(config_path)
    proxies = ProxyRotator.from_source(proxy_source) if proxy_source else None
    return asyncio.run(TrafficBot(config, proxies=proxies).run())
