"""
Task Scheduling & Profile Setup Simulation Engine.
Orchestrates sequential or priority-based execution of profile automation workflows,
integrating behavioral jitter, cooldown intervals, and rate-limit recovery.
"""

from __future__ import annotations
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Callable, Dict, Any
from uuid import uuid4

from .config import EngineConfig
from .generator import ProfileMetadataGenerator, GeneratedProfile
from .behavior import HumanBehaviorEngine, RateLimitError
from .data_manager import DataManager
from .logger import setup_logger, ExecutionLogger


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COOLDOWN = "cooldown"


@dataclass
class SimulationTask:
    """Individual workflow step scheduled for execution."""
    task_id: str
    action_type: str
    profile_id: str
    status: TaskStatus = TaskStatus.QUEUED
    retry_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    applied_delay_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "action_type": self.action_type,
            "profile_id": self.profile_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "applied_delay_seconds": self.applied_delay_seconds,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class TaskScheduler:
    """
    Manages scheduling, queueing, and headless execution of profile automation tasks.
    Adheres strictly to human-like pacing guidelines and handles rate limiting.
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        on_step_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.config = config or EngineConfig()
        self.generator = ProfileMetadataGenerator(self.config.profile_generator)
        self.behavior = HumanBehaviorEngine(self.config.behavior)
        self.data_manager = DataManager(self.config.storage)
        self.logger = setup_logger(
            name="PersonaPulse.Scheduler",
            log_file=self.config.storage.audit_log_file
        )
        self.exec_logger = ExecutionLogger(self.logger)
        self.on_step_callback = on_step_callback

        self.queue: List[SimulationTask] = []
        self.completed_tasks: List[SimulationTask] = []
        self.is_interrupted = False

        # Register signal handlers for clean headless terminations
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Gracefully handle Ctrl+C or Linux termination signals in Docker/CI."""
        try:
            signal.signal(signal.SIGINT, self._handle_interrupt)
            signal.signal(signal.SIGTERM, self._handle_interrupt)
        except (ValueError, AttributeError):
            # Not in main thread or unsupported platform
            pass

    def _handle_interrupt(self, signum: int, frame: Any) -> None:
        self.logger.warning("Received termination signal! Gracefully finishing active task...")
        self.is_interrupted = True

    def schedule_profile_generation(self, count: int = 1) -> List[SimulationTask]:
        """Queues creation and setup tasks for a batch of profiles."""
        tasks: List[SimulationTask] = []
        for _ in range(count):
            profile = self.generator.generate_single_profile(download_avatar=False)
            self.data_manager.add_profile(profile)

            # Sequence of human actions for profile setup
            actions = [
                ("ACCOUNT_REGISTRATION", "fill_form_field"),
                ("DOWNLOAD_AVATAR", "avatar_upload"),
                ("UPDATE_BIO_AND_TAGS", "keystroke_burst"),
                ("VERIFY_CREDENTIALS", "page_navigation")
            ]

            for act, act_type in actions:
                task = SimulationTask(
                    task_id=str(uuid4()),
                    action_type=act,
                    profile_id=profile.id,
                    metadata={"action_category": act_type, "profile_name": profile.full_name}
                )
                self.queue.append(task)
                tasks.append(task)

        self.logger.info(f"Scheduled {len(tasks)} tasks across {count} profiles.")
        return tasks

    def run_next_task(
        self,
        dry_run: bool = False,
        simulate_rate_limit_rate: float = 0.0
    ) -> Optional[SimulationTask]:
        """
        Executes the next task in the queue with human-like jitter, cooldown checks,
        and exponential backoff retry.
        """
        if not self.queue or self.is_interrupted:
            return None

        task = self.queue.pop(0)
        task.status = TaskStatus.RUNNING
        start_time = time.time()
        act_type = task.metadata.get("action_category", "default")

        self.exec_logger.log_action_start(task.action_type, task.profile_id)

        try:
            # 1. Human behavioral delay with jitter
            delay, cooldown = self.behavior.pace(
                action_name=task.action_type,
                dry_run=dry_run,
                action_type=act_type
            )
            task.applied_delay_seconds = delay

            self.exec_logger.log_action_delay(
                task.action_type,
                delay,
                self.config.behavior.jitter_distribution
            )

            if cooldown:
                self.exec_logger.log_cooldown(
                    cooldown,
                    self.config.behavior.cooldown_after_actions
                )

            # 2. Simulate 429 Rate-Limit Injection (for testing resilience)
            if simulate_rate_limit_rate > 0:
                import random
                if random.random() < simulate_rate_limit_rate:
                    raise RateLimitError("429 Too Many Requests (Simulated)", retry_after=None)

            # 3. Execute domain action logic
            self._execute_action_logic(task)

            # Mark task success
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc).isoformat()
            elapsed = time.time() - start_time
            self.exec_logger.log_action_success(task.action_type, task.profile_id, elapsed)

        except RateLimitError as rle:
            # Apply Exponential Backoff with full jitter
            task.retry_count += 1
            backoff_sleep = self.behavior.handle_rate_limit(task.retry_count, rle.retry_after)
            self.exec_logger.log_rate_limit_retry(task.retry_count, backoff_sleep)

            if not dry_run:
                time.sleep(backoff_sleep)

            # Re-queue task to front of line if under max retries
            if task.retry_count <= self.config.behavior.max_backoff_retries:
                task.status = TaskStatus.QUEUED
                self.queue.insert(0, task)
            else:
                task.status = TaskStatus.FAILED
                task.error_message = f"Exceeded max retries: {str(rle)}"

        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            self.logger.error(f"Task {task.task_id} failed: {exc}", exc_info=True)

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self.completed_tasks.append(task)

        if self.on_step_callback:
            self.on_step_callback(task.to_dict())

        return task

    def _execute_action_logic(self, task: SimulationTask) -> None:
        """Executes actual task effect on the profile record."""
        profile = self.data_manager.get_profile(task.profile_id)
        if not profile:
            return

        if task.action_type == "ACCOUNT_REGISTRATION":
            self.data_manager.update_status(profile.id, "registered")

        elif task.action_type == "DOWNLOAD_AVATAR":
            local_path = self.generator.download_and_verify_avatar(
                profile.avatar_url,
                profile.id
            )
            profile.local_avatar_path = local_path
            self.data_manager.update_status(profile.id, "avatar_linked", {"local_avatar_path": local_path})

        elif task.action_type == "UPDATE_BIO_AND_TAGS":
            # Refresh bio with rich persona flair
            fresh_bio = self.generator.generate_bio(profile.persona)
            self.data_manager.update_status(profile.id, "profile_configured", {"bio": fresh_bio})

        elif task.action_type == "VERIFY_CREDENTIALS":
            self.data_manager.update_status(
                profile.id,
                "verified",
                {"verified_at": datetime.now(timezone.utc).isoformat(), "is_test_ready": True}
            )

    def run_all(
        self,
        dry_run: bool = False,
        simulate_rate_limit_rate: float = 0.0,
        max_tasks: Optional[int] = None
    ) -> List[SimulationTask]:
        """Runs queued tasks until empty or interrupted."""
        processed: List[SimulationTask] = []
        count = 0

        while self.queue and not self.is_interrupted:
            if max_tasks and count >= max_tasks:
                break
            task = self.run_next_task(
                dry_run=dry_run,
                simulate_rate_limit_rate=simulate_rate_limit_rate
            )
            if task:
                processed.append(task)
                count += 1

        self.logger.info(f"Execution batch completed. Total processed: {len(processed)} tasks.")
        return processed

    def get_queue_status(self) -> Dict[str, Any]:
        """Returns scheduler state for monitoring."""
        return {
            "pending_count": len(self.queue),
            "completed_count": len(self.completed_tasks),
            "is_interrupted": self.is_interrupted,
            "behavior_metrics": self.behavior.get_metrics(),
            "recent_tasks": [t.to_dict() for t in self.completed_tasks[-10:]]
        }
