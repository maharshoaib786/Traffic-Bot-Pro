"""Proxy rotation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle
from pathlib import Path
from typing import Iterable, Iterator, List, Optional


@dataclass(slots=True)
class ProxyRotator:
    """Iterate over proxies according to a rotation strategy."""

    proxies: List[str]
    strategy: str = "sequential"

    def __post_init__(self) -> None:
        cleaned = [proxy.strip() for proxy in self.proxies if proxy and proxy.strip()]
        if not cleaned:
            raise ValueError("ProxyRotator requires at least one proxy")
        self.proxies = cleaned
        self._iterator: Iterator[str] = iter(self.proxies)
        if self.strategy not in {"sequential", "round-robin"}:
            raise ValueError("strategy must be 'sequential' or 'round-robin'")

    def __iter__(self) -> "ProxyRotator":
        return self

    def __next__(self) -> str:
        if self.strategy == "sequential":
            try:
                return next(self._iterator)
            except StopIteration:
                self._iterator = iter(self.proxies)
                raise
        # round-robin
        if not hasattr(self, "_cycle"):
            self._cycle = cycle(self.proxies)
        return next(self._cycle)

    def next(self) -> str:
        """Return the next proxy, respecting the strategy."""

        if self.strategy == "sequential":
            try:
                return next(self._iterator)
            except StopIteration:
                self._iterator = iter(self.proxies)
                return next(self._iterator)
        return next(self)

    @classmethod
    def from_source(
        cls, source: str | Path | Iterable[str] | None, *, strategy: str = "round-robin"
    ) -> Optional["ProxyRotator"]:
        """Create a rotator from a variety of input types."""

        if source is None:
            return None
        if isinstance(source, ProxyRotator):
            return source
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                proxies = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
            else:
                proxies = [proxy.strip() for proxy in str(source).split(",") if proxy.strip()]
        else:
            proxies = [proxy.strip() for proxy in source if proxy and proxy.strip()]

        if not proxies:
            return None
        return cls(proxies=proxies, strategy=strategy)


def load_proxies(path: str | Path) -> List[str]:
    """Load proxies from a file for compatibility with existing tooling."""

    text = Path(path).read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]
