"""Command line interface for the Traffic Bot toolkit."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict

import yaml

from . import __version__
from .bot import TrafficBot
from .config import CampaignConfig
from .proxy import ProxyRotator
from .scheduler import ScheduledCampaign


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _load_config(args: argparse.Namespace) -> CampaignConfig:
    config = CampaignConfig.from_file(args.config)
    if args.concurrency:
        config.concurrency = args.concurrency
    if args.delay_between_visits is not None:
        config.delay_between_visits = args.delay_between_visits
    if args.dry_run:
        config.dry_run = True
    if args.no_rotate_user_agents:
        config.rotate_user_agents = False
    return config


def _run_command(args: argparse.Namespace) -> Dict[str, Any]:
    config = _load_config(args)
    proxies = ProxyRotator.from_source(args.proxies, strategy=args.proxy_strategy)
    bot = TrafficBot(config, proxies=proxies, request_timeout=args.timeout)
    metrics = asyncio.run(bot.run())
    return metrics.summary()


def _schedule_command(args: argparse.Namespace) -> None:
    campaign = ScheduledCampaign(
        config_path=Path(args.config),
        interval=args.interval,
        iterations=args.iterations,
        proxy_source=args.proxies,
    )
    asyncio.run(campaign.run())


_SAMPLE_CONFIG = {
    "name": "Demo Campaign",
    "concurrency": 5,
    "delay_between_visits": 0.5,
    "visit_profiles": [
        {
            "url": "https://example.com",
            "visits": 10,
            "min_duration": 5,
            "max_duration": 15,
            "referrers": ["https://google.com", "https://bing.com"],
            "keywords": ["buy traffic", "boost seo"],
        }
    ],
}


def _generate_command(args: argparse.Namespace) -> Path:
    output = Path(args.output)
    if output.exists() and not args.force:
        raise FileExistsError(f"Refusing to overwrite existing file: {output}")
    output.write_text(yaml.safe_dump(_SAMPLE_CONFIG, sort_keys=False), encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Traffic Bot Pro inspired automation toolkit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase logging output")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser("run", help="Run a campaign configuration once")
    run_parser.add_argument("config", help="Path to the campaign configuration (YAML/JSON)")
    run_parser.add_argument("--proxies", help="Comma separated proxies or path to file", default=None)
    run_parser.add_argument(
        "--proxy-strategy",
        choices=["round-robin", "sequential"],
        default="round-robin",
        help="Proxy rotation strategy",
    )
    run_parser.add_argument("--concurrency", type=int, help="Override concurrency from config")
    run_parser.add_argument(
        "--delay-between-visits",
        type=float,
        help="Override delay between visits (seconds)",
    )
    run_parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    run_parser.add_argument("--dry-run", action="store_true", help="Simulate visits without network calls")
    run_parser.add_argument(
        "--no-rotate-user-agents",
        action="store_true",
        help="Disable user agent rotation",
    )
    run_parser.set_defaults(handler=_run_command)

    schedule_parser = subcommands.add_parser("schedule", help="Run a campaign at a fixed interval")
    schedule_parser.add_argument("config", help="Configuration file to schedule")
    schedule_parser.add_argument("--interval", type=float, required=True, help="Interval between runs (seconds)")
    schedule_parser.add_argument("--iterations", type=int, help="Number of runs before exiting")
    schedule_parser.add_argument("--proxies", help="Proxy settings for each run", default=None)
    schedule_parser.set_defaults(handler=_schedule_command)

    generate_parser = subcommands.add_parser("generate-config", help="Create a starter configuration file")
    generate_parser.add_argument("output", help="Where to write the new configuration")
    generate_parser.add_argument("--force", action="store_true", help="Overwrite if the file exists")
    generate_parser.set_defaults(handler=_generate_command)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    handler = args.handler
    result = handler(args)
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
    elif isinstance(result, Path):
        print(f"Configuration written to {result}")


if __name__ == "__main__":  # pragma: no cover
    main()
