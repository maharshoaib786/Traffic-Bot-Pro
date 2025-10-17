"""Configuration parsing for Traffic Bot campaigns."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List

import yaml


@dataclass(slots=True)
class VisitProfile:
    """Parameters that describe a single batch of visits to the same URL."""

    url: str
    visits: int = 1
    min_duration: float = 5.0
    max_duration: float = 15.0
    referrers: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError("VisitProfile requires a non-empty url")
        if self.visits < 1:
            raise ValueError("visits must be at least 1")
        if self.max_duration < self.min_duration:
            raise ValueError("max_duration must be >= min_duration")


@dataclass(slots=True)
class CampaignConfig:
    """High level settings for orchestrating a campaign."""

    name: str
    visit_profiles: List[VisitProfile]
    concurrency: int = 4
    delay_between_visits: float = 0.0
    delay_between_batches: float = 0.0
    rotate_user_agents: bool = True
    dry_run: bool = False

    def __post_init__(self) -> None:
        if self.concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        if not self.visit_profiles:
            raise ValueError("at least one visit profile is required")

    def iter_visits(self) -> Iterator[VisitProfile]:
        """Yield visit profiles according to their requested quantity."""

        for profile in self.visit_profiles:
            for _ in range(profile.visits):
                yield profile

    @classmethod
    def from_dict(cls, data: dict) -> "CampaignConfig":
        """Create a config from a mapping, performing validation."""

        if "visit_profiles" in data:
            raw_profiles: Iterable[dict] = data["visit_profiles"]
        elif "targets" in data:
            raw_profiles = data["targets"]
        else:
            raise ValueError("Configuration missing 'visit_profiles' or 'targets'")

        profiles = [VisitProfile(**profile) for profile in raw_profiles]
        name = data.get("name", "Unnamed Campaign")
        concurrency = int(data.get("concurrency", 4))
        delay_between_visits = float(data.get("delay_between_visits", 0))
        delay_between_batches = float(data.get("delay_between_batches", 0))
        rotate_user_agents = bool(data.get("rotate_user_agents", True))
        dry_run = bool(data.get("dry_run", False))

        return cls(
            name=name,
            visit_profiles=profiles,
            concurrency=concurrency,
            delay_between_visits=delay_between_visits,
            delay_between_batches=delay_between_batches,
            rotate_user_agents=rotate_user_agents,
            dry_run=dry_run,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "CampaignConfig":
        """Load configuration from a YAML or JSON file."""

        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Campaign configuration not found: {file_path}")

        text = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text) or {}
        elif file_path.suffix.lower() == ".json":
            data = json.loads(text or "{}")
        else:
            raise ValueError("Unsupported configuration format. Use YAML or JSON")

        if not isinstance(data, dict):
            raise ValueError("Configuration root must be a mapping/dictionary")

        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Convert the configuration back to a JSON-serializable dict."""

        return {
            "name": self.name,
            "concurrency": self.concurrency,
            "delay_between_visits": self.delay_between_visits,
            "delay_between_batches": self.delay_between_batches,
            "rotate_user_agents": self.rotate_user_agents,
            "dry_run": self.dry_run,
            "visit_profiles": [
                {
                    "url": profile.url,
                    "visits": profile.visits,
                    "min_duration": profile.min_duration,
                    "max_duration": profile.max_duration,
                    "referrers": list(profile.referrers),
                    "keywords": list(profile.keywords),
                }
                for profile in self.visit_profiles
            ],
        }


def load_config(path: str | Path) -> CampaignConfig:
    """Helper that mirrors the legacy API name from Traffic Bot Pro."""

    return CampaignConfig.from_file(path)
