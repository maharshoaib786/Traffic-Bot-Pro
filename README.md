# Traffic Bot Pro Toolkit

Traffic Bot Pro Toolkit is a Python-based automation framework inspired by the feature set of [Traffic Bot Pro]. It enables you to simulate organic traffic visits, rotate proxies and user agents, schedule repeat campaigns and collect metrics for each run.

> **Disclaimer:** Use automated traffic responsibly. Many platforms prohibit artificial traffic generation. Ensure you comply with the terms of service and local regulations for any site you target.

## Features

- 🧭 Declarative campaign configuration (YAML or JSON) with per-URL visit quotas and dwell times
- 🔁 Automatic user-agent rotation with desktop and mobile fingerprints
- 🧂 Optional proxy rotation (round-robin or sequential)
- 🕒 Configurable delays between visits and between URL batches
- 📊 Built-in metrics aggregation for successes, failures and visit durations
- 🗓️ Scheduler for recurring campaigns
- 🛠️ CLI helpers to run campaigns, schedule them or scaffold starter configs

## Installation

This repository ships as a standard Python package. You can install it locally in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

The project requires Python 3.9 or newer.

## Quick start

1. Generate a starter configuration:

   ```bash
   trafficbot generate-config my-campaign.yaml
   ```

2. Adjust the generated `my-campaign.yaml` to match your URLs, visit counts and dwell times. A minimal example is included in [`examples/campaign.yaml`](examples/campaign.yaml).

3. Run the campaign:

   ```bash
   trafficbot run my-campaign.yaml --dry-run
   ```

   Remove `--dry-run` to perform real HTTP requests. The CLI outputs campaign metrics as JSON once the run completes.

## Configuration reference

Each campaign file supports the following keys:

```yaml
name: Demo Campaign
concurrency: 5
rotate_user_agents: true
delay_between_visits: 0.5
visit_profiles:
  - url: https://example.com
    visits: 10
    min_duration: 5   # Seconds to spend on page (randomised between min/max)
    max_duration: 15
    referrers:
      - https://google.com
    keywords:
      - boost seo
```

- **concurrency** – maximum simultaneous visits.
- **delay_between_visits** – pause inserted after queuing each visit.
- **delay_between_batches** – optional pause after finishing the visit quota for a URL.
- **rotate_user_agents** – toggle automatic user-agent selection.
- **visit_profiles** – list of URLs and behaviours to simulate.

## Proxy rotation

Provide proxies via a comma separated list or a file path:

```bash
trafficbot run my-campaign.yaml --proxies http://user:pass@1.2.3.4:8080,http://5.6.7.8:8080
trafficbot run my-campaign.yaml --proxies proxies.txt --proxy-strategy sequential
```

The toolkit will rotate through proxies for each request while preserving concurrency limits.

## Scheduling campaigns

Use the scheduler to repeat campaigns at fixed intervals:

```bash
trafficbot schedule my-campaign.yaml --interval 3600 --iterations 4
```

The example above re-loads the configuration every hour for four iterations. Omitting `--iterations` runs indefinitely.

## Development

- The package exposes a Python API via `trafficbot.TrafficBot` and friends for integration in custom workflows.
- Metrics are available programmatically through `VisitMetrics` objects and contain aggregated success/failure counts plus visit duration statistics.
- The codebase is fully asynchronous and uses `aiohttp` for networking.

Contributions and improvements are welcome!
