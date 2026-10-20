"""
Command-Line Interface (CLI) for PersonaPulse.
Provides modular subcommands for generating profiles, running behavioral simulations,
evaluating jitter statistics, and exporting data in headless Linux environments.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import ConfigManager, EngineConfig
from .generator import ProfileMetadataGenerator
from .behavior import HumanBehaviorEngine, ExponentialBackoffHandler
from .data_manager import DataManager
from .scheduler import TaskScheduler
from .logger import setup_logger


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="personapulse",
        description="PersonaPulse: Production Profile Automation & Behavioral Simulation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py generate --count 10 --download-avatars
  python main.py simulate --count 3 --dry-run
  python main.py simulate --count 2 --inject-rate-limit 0.25
  python main.py test-behavior --samples 100 --distribution gaussian
  python main.py list
  python main.py export --format csv --output exports/accounts.csv
        """
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default=None,
        help="Path to YAML or JSON config file (default: config.yaml)"
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Enable single-line structured JSON logging (ideal for CI/CD log forwarders)"
    )

    subparsers = parser.add_subparsers(dest="subcommand", title="Commands")

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Generate realistic human-like profile metadata")
    gen_parser.add_argument("-n", "--count", type=int, default=5, help="Number of profiles to generate")
    gen_parser.add_argument("--download-avatars", action="store_true", help="Download and verify avatar images")
    gen_parser.add_argument("--export-csv", type=str, default=None, help="Optional path to export to CSV")

    # Command: simulate
    sim_parser = subparsers.add_parser("simulate", help="Run multi-step profile setup simulation with human pacing")
    sim_parser.add_argument("-n", "--count", type=int, default=2, help="Number of profiles to schedule & setup")
    sim_parser.add_argument("--dry-run", action="store_true", help="Execute without real-time time.sleep waits")
    sim_parser.add_argument(
        "--inject-rate-limit",
        type=float,
        default=0.0,
        help="Simulate rate limit failure probability (e.g. 0.3 for 30%% chance) to test exponential backoff"
    )

    # Command: test-behavior
    beh_parser = subparsers.add_parser("test-behavior", help="Benchmark jitter models and exponential backoff curves")
    beh_parser.add_argument("-s", "--samples", type=int, default=50, help="Number of simulated action samples")
    beh_parser.add_argument(
        "--distribution",
        choices=["gaussian", "uniform", "pareto"],
        default="gaussian",
        help="Jitter distribution function"
    )
    beh_parser.add_argument("--test-backoff", action="store_true", help="Simulate a 5-step exponential backoff sequence")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List stored accounts from accounts.json")
    list_parser.add_argument("-l", "--limit", type=int, default=20, help="Max accounts to display")

    # Command: export
    exp_parser = subparsers.add_parser("export", help="Export stored accounts to CSV or JSON")
    exp_parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Export file format")
    exp_parser.add_argument("-o", "--output", type=str, required=True, help="Target file path")

    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.subcommand:
        parser.print_help()
        return 0

    # Load configuration
    config = ConfigManager.load_from_file(parsed.config)
    logger = setup_logger(
        log_file=config.storage.audit_log_file,
        json_logging=parsed.json_logs
    )

    if parsed.subcommand == "generate":
        generator = ProfileMetadataGenerator(config.profile_generator)
        dm = DataManager(config.storage)
        logger.info(f"Generating {parsed.count} profiles (download_avatars={parsed.download_avatars})...")

        profiles = generator.generate_batch(parsed.count, download_avatars=parsed.download_avatars)
        added = dm.add_profiles_batch(profiles)
        logger.info(f"Successfully generated and stored {added} profiles in {config.storage.accounts_file}")

        for p in profiles[:3]:
            print(f" • {p.full_name} (@{p.username}) - {p.persona} [{p.location}]")
            print(f"   Bio: {p.bio}")

        if parsed.export_csv:
            csv_path = dm.export_to_csv(parsed.export_csv)
            logger.info(f"Exported data to {csv_path}")

        return 0

    elif parsed.subcommand == "simulate":
        scheduler = TaskScheduler(config)
        logger.info(f"Queueing simulation for {parsed.count} profiles...")
        scheduler.schedule_profile_generation(count=parsed.count)

        logger.info(
            f"Executing tasks (dry_run={parsed.dry_run}, rate_limit_prob={parsed.inject_rate_limit})..."
        )
        tasks = scheduler.run_all(
            dry_run=parsed.dry_run,
            simulate_rate_limit_rate=parsed.inject_rate_limit
        )

        completed = sum(1 for t in tasks if t.status.value == "completed")
        failed = sum(1 for t in tasks if t.status.value == "failed")
        logger.info(f"Simulation Finished! Completed: {completed}, Failed: {failed}")
        return 0 if failed == 0 else 1

    elif parsed.subcommand == "test-behavior":
        config.behavior.jitter_distribution = parsed.distribution
        behavior = HumanBehaviorEngine(config.behavior)
        logger.info(f"Running behavior benchmark with distribution: '{parsed.distribution}' ({parsed.samples} samples)...")

        delays = [behavior.calculate_jitter_delay() for _ in range(parsed.samples)]
        avg = sum(delays) / len(delays)
        min_d = min(delays)
        max_d = max(delays)

        print("\n" + "=" * 55)
        print(" BEHAVIORAL JITTER BENCHMARK RESULTS")
        print("=" * 55)
        print(f" Distribution Model:     {parsed.distribution.upper()}")
        print(f" Base Delay Setting:     {config.behavior.base_delay_seconds:.2f}s")
        print(f" Observed Min Delay:     {min_d:.3f}s")
        print(f" Observed Max Delay:     {max_d:.3f}s")
        print(f" Observed Mean Delay:    {avg:.3f}s")
        print(f" Cooldown Frequency:     Every {config.behavior.cooldown_after_actions} actions")
        print(f" Cooldown Duration:      {config.behavior.cooldown_min_seconds}s - {config.behavior.cooldown_max_seconds}s")
        print("=" * 55)

        if parsed.test_backoff:
            print("\nSimulating 5 consecutive 429 Rate Limit Backoff steps (Full Jitter):")
            backoff_handler = ExponentialBackoffHandler()
            for attempt in range(1, 6):
                sleep_time = backoff_handler.calculate_backoff(attempt)
                max_possible = min(64.0, 2.0 * (2 ** attempt))
                print(f"  Attempt {attempt}: Slept {sleep_time:5.2f}s (Upper bound: {max_possible:5.1f}s)")
            print("=" * 55 + "\n")

        return 0

    elif parsed.subcommand == "list":
        dm = DataManager(config.storage)
        profiles = dm.load_all_profiles()
        summary = dm.get_summary()

        print(f"\nStored Profiles in {config.storage.accounts_file} (Total: {summary['total_profiles']}):")
        print("-" * 75)
        for p in profiles[:parsed.limit]:
            print(f"ID: {p.id[:8]} | {p.full_name:<20} | @{p.username:<16} | Status: {p.status:<10} | {p.location}")
        if len(profiles) > parsed.limit:
            print(f"... and {len(profiles) - parsed.limit} more.")
        print("-" * 75 + "\n")
        return 0

    elif parsed.subcommand == "export":
        dm = DataManager(config.storage)
        if parsed.format == "csv":
            path = dm.export_to_csv(parsed.output)
            logger.info(f"Exported to CSV: {path}")
        else:
            profiles = dm.load_all_profiles()
            out = Path(parsed.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            import json
            out.write_text(json.dumps([p.to_dict() for p in profiles], indent=2), encoding="utf-8")
            logger.info(f"Exported to JSON: {out}")
        return 0

    return 0
