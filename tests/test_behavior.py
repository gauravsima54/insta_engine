"""
Unit tests for HumanBehaviorEngine and ExponentialBackoffHandler.
Verifies jitter bounds, cooldown milestone triggering, and full-jitter backoff math.
"""

import unittest
from automation_engine.config import BehaviorConfig
from automation_engine.behavior import HumanBehaviorEngine, ExponentialBackoffHandler, RateLimitError


class TestBehaviorEngine(unittest.TestCase):

    def setUp(self):
        self.config = BehaviorConfig(
            base_delay_seconds=2.0,
            jitter_min_seconds=0.5,
            jitter_max_seconds=4.0,
            cooldown_after_actions=3,
            cooldown_min_seconds=5.0,
            cooldown_max_seconds=10.0,
            max_backoff_retries=4
        )
        self.engine = HumanBehaviorEngine(self.config)

    def test_calculate_jitter_delay_gaussian(self):
        self.config.jitter_distribution = "gaussian"
        for _ in range(50):
            delay = self.engine.calculate_jitter_delay()
            self.assertGreaterEqual(delay, 0.1)
            self.assertLessEqual(delay, 10.0)

    def test_calculate_jitter_delay_pareto(self):
        self.config.jitter_distribution = "pareto"
        delays = [self.engine.calculate_jitter_delay() for _ in range(100)]
        self.assertTrue(any(d < 2.0 for d in delays))

    def test_cooldown_trigger(self):
        # 3 actions required to trigger cooldown
        d1, c1 = self.engine.pace("ACTION_1", dry_run=True)
        self.assertIsNone(c1)
        d2, c2 = self.engine.pace("ACTION_2", dry_run=True)
        self.assertIsNone(c2)
        d3, c3 = self.engine.pace("ACTION_3", dry_run=True)
        self.assertIsNotNone(c3)
        self.assertGreaterEqual(c3, 5.0)
        self.assertLessEqual(c3, 10.0)

    def test_exponential_backoff_growth(self):
        handler = ExponentialBackoffHandler(base_seconds=1.0, max_seconds=32.0)
        # Attempt 1: min 0.1, ceiling 2.0
        b1 = handler.calculate_backoff(1)
        self.assertGreaterEqual(b1, 0.1)
        self.assertLessEqual(b1, 2.0)

        # Attempt 5: ceiling min(32, 1 * 32) = 32.0
        b5 = handler.calculate_backoff(5)
        self.assertGreaterEqual(b5, 0.1)
        self.assertLessEqual(b5, 32.0)

    def test_respects_retry_after_header(self):
        handler = ExponentialBackoffHandler()
        backoff = handler.calculate_backoff(1, retry_after=15.0)
        self.assertGreaterEqual(backoff, 15.0)
        self.assertLessEqual(backoff, 18.0)


if __name__ == "__main__":
    unittest.main()
