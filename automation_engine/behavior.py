"""
Human-Like Behavior Engine.
Simulates natural human interaction pacing with randomized jitter (Gaussian/Uniform/Pareto),
session cooldown intervals, burst patterns, and full-jitter exponential backoff for rate limits.
"""

from __future__ import annotations
import math
import random
import time
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Dict, Any, TypeVar, Tuple
from .config import BehaviorConfig

T = TypeVar("T")


class JitterDistribution(str, Enum):
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    PARETO = "pareto"


class RateLimitError(Exception):
    """Raised when an external service or simulation hits an HTTP 429 rate limit."""
    def __init__(self, message: str = "Rate limit encountered (429)", retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ExponentialBackoffHandler:
    """
    Implements production-grade Exponential Backoff with Full Jitter.
    Formula: Sleep = Uniform(0, Min(MaxBackoff, BaseBackoff * 2^attempt))
    Prevents thundering herd problems when operating concurrent workers.
    """

    def __init__(self, base_seconds: float = 2.0, max_seconds: float = 64.0, max_retries: int = 5):
        self.base_seconds = max(0.1, base_seconds)
        self.max_seconds = max(self.base_seconds, max_seconds)
        self.max_retries = max(1, max_retries)

    def calculate_backoff(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """
        Calculates sleep duration for a given retry attempt.
        If a server supplied a Retry-After header, respects it with a small jitter cushion.
        """
        if retry_after is not None and retry_after > 0:
            # Respect server Retry-After plus a slight randomized cushion
            return retry_after + random.uniform(0.5, 2.0)

        # Truncated exponential backoff upper bound
        temp_ceiling = min(self.max_seconds, self.base_seconds * math.pow(2, attempt))
        # Full jitter: random value between 0 and ceiling
        sleep_duration = random.uniform(0.1, temp_ceiling)
        return round(sleep_duration, 3)

    def execute_with_retry(
        self,
        func: Callable[[], T],
        on_retry: Optional[Callable[[int, float, Exception], None]] = None,
        dry_run: bool = False
    ) -> T:
        """
        Executes a callable with automatic backoff retry on RateLimitError or connection errors.
        """
        attempt = 0
        while True:
            try:
                return func()
            except RateLimitError as exc:
                attempt += 1
                if attempt > self.max_retries:
                    raise RuntimeError(
                        f"Max retries ({self.max_retries}) exceeded due to persistent rate limiting."
                    ) from exc

                backoff_time = self.calculate_backoff(attempt, exc.retry_after)
                if on_retry:
                    on_retry(attempt, backoff_time, exc)

                if not dry_run:
                    time.sleep(backoff_time)


class HumanBehaviorEngine:
    """
    Core behavioral engine orchestrating action timing, jitter calculations,
    fatigue/cooldown cycles, and action history.
    """

    def __init__(self, config: Optional[BehaviorConfig] = None):
        self.config = config or BehaviorConfig()
        self.backoff_handler = ExponentialBackoffHandler(
            base_seconds=self.config.backoff_base_seconds,
            max_seconds=self.config.backoff_max_seconds,
            max_retries=self.config.max_backoff_retries
        )
        self.action_count: int = 0
        self.total_sleep_time: float = 0.0
        self.history: list[Dict[str, Any]] = []

    def calculate_jitter_delay(self, action_type: str = "default") -> float:
        """
        Calculates a natural human pacing delay with randomized jitter.
        Uses configured distribution (Gaussian, Uniform, or Pareto bursts).
        """
        base = self.config.base_delay_seconds
        min_j = self.config.jitter_min_seconds
        max_j = self.config.jitter_max_seconds
        dist = self.config.jitter_distribution.lower()

        # Action-specific scaling factors to emulate different physical motions
        action_multipliers = {
            "mouse_click": 0.4,
            "keystroke_burst": 0.3,
            "read_content": 1.4,
            "fill_form_field": 0.8,
            "page_navigation": 1.2,
            "avatar_upload": 1.5,
            "default": 1.0
        }
        multiplier = action_multipliers.get(action_type, 1.0)
        scaled_base = base * multiplier

        if dist == JitterDistribution.GAUSSIAN.value:
            # Gaussian distribution centered at base delay
            mu = scaled_base
            sigma = self.config.gaussian_std_dev
            sample = random.gauss(mu, sigma)
            # Clamp between min and max jitter
            delay = max(min_j, min(max_j * multiplier, sample))

        elif dist == JitterDistribution.PARETO.value:
            # Pareto 80/20 rule: 80% micro-delays (quick clicks), 20% cognitive pauses (reading/thinking)
            if random.random() < 0.80:
                delay = random.uniform(min_j * 0.5, scaled_base * 0.7)
            else:
                delay = random.uniform(scaled_base, max_j * 1.3)

        else:
            # Uniform distribution
            delay = random.uniform(min_j, max_j * multiplier)

        # Optional circadian rhythm modifier (simulates slower cognitive speed at night)
        if self.config.enable_circadian_pacing:
            hour = datetime.now().hour
            if 0 <= hour <= 6:
                delay *= 1.35  # Slower late at night
            elif 9 <= hour <= 18:
                delay *= 0.95  # Active during working hours

        return round(max(0.1, delay), 3)

    def calculate_cooldown(self) -> float:
        """Generates a random cooldown duration to simulate user stepping away or resting."""
        c_min = self.config.cooldown_min_seconds
        c_max = self.config.cooldown_max_seconds
        return round(random.uniform(c_min, c_max), 2)

    def pace(
        self,
        action_name: str,
        dry_run: bool = False,
        action_type: str = "default"
    ) -> Tuple[float, Optional[float]]:
        """
        Enforces human pacing before or after an action.
        Returns: (action_delay_applied, cooldown_applied_if_triggered)
        """
        delay = self.calculate_jitter_delay(action_type)
        cooldown_applied = None

        if not dry_run:
            time.sleep(delay)

        self.total_sleep_time += delay
        self.action_count += 1

        # Check if cooldown milestone reached
        if self.action_count >= self.config.cooldown_after_actions:
            cooldown_applied = self.calculate_cooldown()
            if not dry_run:
                time.sleep(cooldown_applied)
            self.total_sleep_time += cooldown_applied
            self.action_count = 0  # Reset session counter

        # Record event in timeline history (up to last 100 events)
        record = {
            "timestamp": datetime.now().isoformat(),
            "action": action_name,
            "action_type": action_type,
            "delay_seconds": delay,
            "cooldown_seconds": cooldown_applied,
            "cumulative_sleep_seconds": round(self.total_sleep_time, 2),
        }
        self.history.append(record)
        if len(self.history) > 100:
            self.history.pop(0)

        return delay, cooldown_applied

    def handle_rate_limit(self, retry_count: int, retry_after: Optional[float] = None) -> float:
        """Calculates and applies exponential backoff when a 429 response is received."""
        backoff_sleep = self.backoff_handler.calculate_backoff(retry_count, retry_after)
        self.total_sleep_time += backoff_sleep
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "RATE_LIMIT_BACKOFF",
            "action_type": "backoff",
            "delay_seconds": backoff_sleep,
            "cooldown_seconds": None,
            "cumulative_sleep_seconds": round(self.total_sleep_time, 2),
            "retry_count": retry_count
        })
        return backoff_sleep

    def get_metrics(self) -> Dict[str, Any]:
        """Returns behavior engine telemetry."""
        avg_delay = (
            sum(h["delay_seconds"] for h in self.history) / len(self.history)
            if self.history else 0.0
        )
        return {
            "total_actions": len(self.history),
            "active_streak": self.action_count,
            "total_sleep_seconds": round(self.total_sleep_time, 2),
            "average_delay_seconds": round(avg_delay, 2),
            "distribution": self.config.jitter_distribution,
            "recent_events": self.history[-15:],
        }
