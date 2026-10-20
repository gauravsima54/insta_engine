"""
Execution Logging Module for PersonaPulse.
Provides clean ANSI-colored console logs for local terminals,
plain-text / JSON-lines output for headless CI runners and GitHub Actions,
and thread-safe in-memory timeline tracking.
"""

from __future__ import annotations
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


class ANSIColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"


class HeadlessConsoleFormatter(logging.Formatter):
    """
    Format logs with clean timestamps.
    Automatically strips ANSI escape codes if running inside GitHub Actions,
    headless containers, or piped stdout.
    """

    def __init__(self, use_color: Optional[bool] = None):
        super().__init__()
        # Determine if stdout is interactive
        if use_color is None:
            is_ci = bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS"))
            is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
            self.use_color = is_tty and not is_ci
        else:
            self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        if self.use_color:
            level_colors = {
                "DEBUG": ANSIColors.DIM,
                "INFO": ANSIColors.GREEN,
                "WARNING": ANSIColors.YELLOW,
                "ERROR": ANSIColors.RED,
                "CRITICAL": ANSIColors.BOLD + ANSIColors.RED,
            }
            color = level_colors.get(level, ANSIColors.RESET)
            level_str = f"{color}{level:<7}{ANSIColors.RESET}"
            name_str = f"{ANSIColors.CYAN}{record.name}{ANSIColors.RESET}"
            return f"[{timestamp}] {level_str} [{name_str}] {record.getMessage()}"
        else:
            return f"[{timestamp}] {level:<7} [{record.name}] {record.getMessage()}"


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for ELK/CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "action_data"):
            payload["action_data"] = record.action_data  # type: ignore
        return json.dumps(payload)


class MemoryLogHandler(logging.Handler):
    """Keeps the last N log entries in memory for inspection and web telemetry."""

    def __init__(self, max_entries: int = 200):
        super().__init__()
        self.max_entries = max_entries
        self.entries: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "iso_timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def get_entries(self) -> List[Dict[str, Any]]:
        return list(self.entries)


# Global memory handler instance
memory_log_handler = MemoryLogHandler()


def setup_logger(
    name: str = "PersonaPulse",
    log_file: Optional[str] = "logs/execution.log",
    level: int = logging.INFO,
    json_logging: bool = False
) -> logging.Logger:
    """Configures and returns a centralized execution logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid adding duplicate handlers on multiple imports
    if logger.handlers:
        return logger

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_logging:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(HeadlessConsoleFormatter())
    logger.addHandler(console_handler)

    # 2. File Handler (if log_file specified)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("[%(asctime)s] %(levelname)-7s [%(name)s] %(message)s")
            )
            logger.addHandler(file_handler)
        except OSError:
            pass  # Read-only filesystem in some sandboxes

    # 3. Memory Handler
    logger.addHandler(memory_log_handler)

    return logger


class ExecutionLogger:
    """Helper wrapper for domain-specific logging."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_action_start(self, action: str, profile_id: str, details: str = "") -> None:
        self.logger.info(f"▶ START ACTION: {action} | Profile: {profile_id[:8]} | {details}")

    def log_action_delay(self, action: str, delay: float, jitter_type: str) -> None:
        self.logger.info(f"⏳ JITTER PAUSE: {delay:.2f}s ({jitter_type}) for '{action}'")

    def log_cooldown(self, duration: float, after_actions: int) -> None:
        self.logger.warning(f"☕ COOLDOWN ACTIVATED: Resting for {duration:.2f}s after {after_actions} actions.")

    def log_rate_limit_retry(self, attempt: int, backoff_seconds: float) -> None:
        self.logger.warning(
            f"⚠️ RATE LIMIT 429 DETECTED: Backing off for {backoff_seconds:.2f}s (Attempt {attempt})"
        )

    def log_action_success(self, action: str, profile_id: str, elapsed: float) -> None:
        self.logger.info(f"✔ ACTION COMPLETE: {action} | Profile: {profile_id[:8]} in {elapsed:.2f}s")
