"""
PersonaPulse - Production Profile Automation & Behavioral Simulation Engine.
Modular, robust architecture designed for testing, synthetic account orchestration,
and human-like action pacing in headless environments.
"""

__version__ = "1.0.0"
__author__ = "Senior Automation Engineer"

from .config import EngineConfig, ConfigManager
from .behavior import HumanBehaviorEngine, JitterDistribution, ExponentialBackoffHandler
from .generator import ProfileMetadataGenerator, GeneratedProfile
from .data_manager import DataManager
from .scheduler import TaskScheduler, SimulationTask
from .logger import setup_logger, ExecutionLogger

__all__ = [
    "EngineConfig",
    "ConfigManager",
    "HumanBehaviorEngine",
    "JitterDistribution",
    "ExponentialBackoffHandler",
    "ProfileMetadataGenerator",
    "GeneratedProfile",
    "DataManager",
    "TaskScheduler",
    "SimulationTask",
    "setup_logger",
    "ExecutionLogger",
]
