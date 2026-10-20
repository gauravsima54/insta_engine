"""
Configuration Manager for PersonaPulse.
Provides strongly-typed configuration dataclasses, YAML/JSON loading,
environment variable overrides, and validation.
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List


@dataclass
class BehaviorConfig:
    """Configures human-like behavior, delays, jitter, and cooldowns."""
    base_delay_seconds: float = 3.5
    jitter_min_seconds: float = 1.0
    jitter_max_seconds: float = 7.0
    jitter_distribution: str = "gaussian"  # "gaussian", "uniform", "pareto"
    gaussian_std_dev: float = 1.2
    cooldown_after_actions: int = 4
    cooldown_min_seconds: float = 15.0
    cooldown_max_seconds: float = 45.0
    enable_circadian_pacing: bool = False  # Slow down during simulated night hours
    max_backoff_retries: int = 5
    backoff_base_seconds: float = 2.0
    backoff_max_seconds: float = 64.0
    backoff_jitter_factor: float = 1.0  # Full jitter (0 to 1)


@dataclass
class ProfileGenConfig:
    """Configures profile generation, bio pools, and public avatar sources."""
    default_locale: str = "en_US"
    avatar_sources: List[str] = field(default_factory=lambda: [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&auto=format&fit=crop&q=80"
    ])
    avatar_download_dir: str = "data/avatars"
    validate_image_headers: bool = True
    max_avatar_size_bytes: int = 5 * 1024 * 1024  # 5 MB
    include_personas: bool = True
    personas_pool: List[str] = field(default_factory=lambda: [
        "tech_enthusiast",
        "digital_nomad",
        "creative_designer",
        "coffee_devotee",
        "fitness_runner",
        "open_source_builder",
        "photographer"
    ])


@dataclass
class StorageConfig:
    """Configures storage destination and file persistence."""
    data_directory: str = "data"
    accounts_file: str = "data/accounts.json"
    audit_log_file: str = "logs/execution.log"
    atomic_writes: bool = True
    backup_on_save: bool = True


@dataclass
class NetworkConfig:
    """Configures HTTP client, timeout, and proxy settings."""
    timeout_seconds: float = 12.0
    user_agent: str = "PersonaPulseAutomation/1.0 (+headless; testing suite)"
    simulate_network_jitter: bool = True
    max_concurrent_tasks: int = 3


@dataclass
class EngineConfig:
    """Master configuration encapsulating all subsystems."""
    app_name: str = "PersonaPulse"
    environment: str = "development"  # "development", "ci", "headless_production"
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    profile_generator: ProfileGenConfig = field(default_factory=ProfileGenConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class ConfigManager:
    """Loads, merges, and validates configuration from YAML, JSON, and Env."""

    @classmethod
    def load_from_file(cls, config_path: str | Path | None = None) -> EngineConfig:
        """Loads configuration from YAML or JSON path, falling back to defaults."""
        config = EngineConfig()

        if config_path is None:
            # Look in standard locations
            candidates = [
                Path("config.yaml"),
                Path("config.yml"),
                Path("config.json"),
                Path("sample_config.yaml"),
            ]
            for candidate in candidates:
                if candidate.exists():
                    config_path = candidate
                    break

        if config_path and Path(config_path).exists():
            path_obj = Path(config_path)
            raw_data: Dict[str, Any] = {}
            content = path_obj.read_text(encoding="utf-8")

            if path_obj.suffix in [".yaml", ".yml"]:
                try:
                    import yaml
                    raw_data = yaml.safe_load(content) or {}
                except ImportError:
                    # Fallback lightweight parser if yaml is not installed yet
                    raw_data = cls._parse_simple_yaml_or_json(content)
            elif path_obj.suffix == ".json":
                raw_data = json.loads(content)

            config = cls._merge_dict_into_config(config, raw_data)

        # Apply environment variable overrides
        cls._apply_env_overrides(config)
        cls._validate(config)
        return config

    @classmethod
    def _parse_simple_yaml_or_json(cls, content: str) -> Dict[str, Any]:
        """Simple fallback if pyyaml is not installed."""
        try:
            return json.loads(content)
        except Exception:
            # Minimal key-value parse for flat/simple structures
            result: Dict[str, Any] = {}
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    # Try number conversion
                    try:
                        if "." in val:
                            val = float(val)
                        else:
                            val = int(val)
                    except ValueError:
                        if val.lower() == "true":
                            val = True
                        elif val.lower() == "false":
                            val = False
                    result[key] = val
            return result

    @classmethod
    def _merge_dict_into_config(cls, base: EngineConfig, data: Dict[str, Any]) -> EngineConfig:
        if not data:
            return base

        if "app_name" in data:
            base.app_name = str(data["app_name"])
        if "environment" in data:
            base.environment = str(data["environment"])

        # Behavior
        b = data.get("behavior", {})
        for field_name in [
            "base_delay_seconds", "jitter_min_seconds", "jitter_max_seconds",
            "jitter_distribution", "gaussian_std_dev", "cooldown_after_actions",
            "cooldown_min_seconds", "cooldown_max_seconds", "enable_circadian_pacing",
            "max_backoff_retries", "backoff_base_seconds", "backoff_max_seconds",
            "backoff_jitter_factor"
        ]:
            if field_name in b:
                setattr(base.behavior, field_name, b[field_name])

        # Profile Generator
        pg = data.get("profile_generator", {})
        for field_name in [
            "default_locale", "avatar_sources", "avatar_download_dir",
            "validate_image_headers", "max_avatar_size_bytes", "include_personas",
            "personas_pool"
        ]:
            if field_name in pg:
                setattr(base.profile_generator, field_name, pg[field_name])

        # Storage
        st = data.get("storage", {})
        for field_name in ["data_directory", "accounts_file", "audit_log_file", "atomic_writes", "backup_on_save"]:
            if field_name in st:
                setattr(base.storage, field_name, st[field_name])

        # Network
        net = data.get("network", {})
        for field_name in ["timeout_seconds", "user_agent", "simulate_network_jitter", "max_concurrent_tasks"]:
            if field_name in net:
                setattr(base.network, field_name, net[field_name])

        return base

    @classmethod
    def _apply_env_overrides(cls, config: EngineConfig) -> None:
        """Allows 12-factor cloud runners / GitHub Actions to override via env."""
        if os.getenv("PERSONAPULSE_ENV"):
            config.environment = os.getenv("PERSONAPULSE_ENV")  # type: ignore

        if os.getenv("PERSONAPULSE_ACCOUNTS_FILE"):
            config.storage.accounts_file = os.getenv("PERSONAPULSE_ACCOUNTS_FILE")  # type: ignore

        if os.getenv("PERSONAPULSE_BASE_DELAY"):
            try:
                config.behavior.base_delay_seconds = float(os.getenv("PERSONAPULSE_BASE_DELAY"))  # type: ignore
            except ValueError:
                pass

        if os.getenv("PERSONAPULSE_JITTER_MAX"):
            try:
                config.behavior.jitter_max_seconds = float(os.getenv("PERSONAPULSE_JITTER_MAX"))  # type: ignore
            except ValueError:
                pass

    @classmethod
    def _validate(cls, config: EngineConfig) -> None:
        """Ensures logical invariants."""
        if config.behavior.jitter_min_seconds < 0:
            config.behavior.jitter_min_seconds = 0.1
        if config.behavior.jitter_max_seconds < config.behavior.jitter_min_seconds:
            config.behavior.jitter_max_seconds = config.behavior.jitter_min_seconds + 1.0
        if config.behavior.base_delay_seconds < 0:
            config.behavior.base_delay_seconds = 1.0
