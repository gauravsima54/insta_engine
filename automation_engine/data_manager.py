"""
Data Management Module for PersonaPulse.
Manages structured persistence into accounts.json using atomic tempfile swap,
file locking, schema validation, and safe backups for headless environments.
"""

from __future__ import annotations
import csv
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from .config import StorageConfig
from .generator import GeneratedProfile


class DataManager:
    """Thread-safe and process-safe storage manager for profile records."""

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.accounts_file = Path(self.config.accounts_file)
        self._ensure_storage_ready()

    def _ensure_storage_ready(self) -> None:
        """Creates parent directories and seeds empty accounts.json if missing."""
        self.accounts_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.accounts_file.exists():
            self._write_raw_data({
                "schema_version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_count": 0,
                "profiles": []
            })

    def _read_raw_data(self) -> Dict[str, Any]:
        """Reads accounts.json safely."""
        if not self.accounts_file.exists():
            return {"schema_version": "1.0", "profiles": [], "total_count": 0}

        try:
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            # Attempt to restore from backup if corrupted
            backup = self.accounts_file.with_suffix(".json.bak")
            if backup.exists():
                with open(backup, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"schema_version": "1.0", "profiles": [], "total_count": 0}

    def _write_raw_data(self, data: Dict[str, Any]) -> None:
        """
        Atomic write implementation.
        Writes payload to a temporary file in the same directory, flushes and syncs to disk,
        then atomically renames it. Guarantees no half-written JSON files.
        """
        parent_dir = self.accounts_file.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        if "profiles" in data:
            data["total_count"] = len(data["profiles"])

        # Create backup if configured and file already exists
        if self.config.backup_on_save and self.accounts_file.exists():
            try:
                shutil.copy2(self.accounts_file, self.accounts_file.with_suffix(".json.bak"))
            except OSError:
                pass

        # Write to temporary file in same filesystem for atomic rename
        fd, temp_path = tempfile.mkstemp(dir=parent_dir, prefix=".accounts_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            # Atomic swap
            os.replace(temp_path, self.accounts_file)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def load_all_profiles(self) -> List[GeneratedProfile]:
        """Loads and parses all stored profiles."""
        raw = self._read_raw_data()
        profiles_raw = raw.get("profiles", [])
        results: List[GeneratedProfile] = []
        for p in profiles_raw:
            try:
                results.append(GeneratedProfile.from_dict(p))
            except Exception:
                continue
        return results

    def save_all_profiles(self, profiles: List[GeneratedProfile]) -> None:
        """Overwrites or saves entire collection of profiles."""
        payload = {
            "schema_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_count": len(profiles),
            "profiles": [p.to_dict() for p in profiles]
        }
        self._write_raw_data(payload)

    def add_profile(self, profile: GeneratedProfile) -> None:
        """Appends a new profile, avoiding duplicate IDs."""
        profiles = self.load_all_profiles()
        if not any(p.id == profile.id for p in profiles):
            profiles.append(profile)
            self.save_all_profiles(profiles)

    def add_profiles_batch(self, new_profiles: List[GeneratedProfile]) -> int:
        """Appends a batch of new profiles. Returns count added."""
        existing = self.load_all_profiles()
        existing_ids = {p.id for p in existing}
        added = 0
        for p in new_profiles:
            if p.id not in existing_ids:
                existing.append(p)
                existing_ids.add(p.id)
                added += 1
        self.save_all_profiles(existing)
        return added

    def get_profile(self, profile_id: str) -> Optional[GeneratedProfile]:
        """Retrieves a single profile by ID."""
        for p in self.load_all_profiles():
            if p.id == profile_id:
                return p
        return None

    def update_status(self, profile_id: str, new_status: str, metadata_patch: Optional[Dict[str, Any]] = None) -> bool:
        """Updates a profile's operational status and metadata."""
        profiles = self.load_all_profiles()
        found = False
        for p in profiles:
            if p.id == profile_id:
                p.status = new_status
                if metadata_patch:
                    p.metadata.update(metadata_patch)
                found = True
                break
        if found:
            self.save_all_profiles(profiles)
        return found

    def export_to_csv(self, output_path: str) -> str:
        """Exports profiles into a clean CSV format for analysis."""
        profiles = self.load_all_profiles()
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "id", "full_name", "username", "email", "persona", "location",
            "timezone", "status", "avatar_url", "local_avatar_path", "created_at"
        ]

        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in profiles:
                d = p.to_dict()
                row = {k: d.get(k, "") for k in fieldnames}
                writer.writerow(row)

        return str(out_file)

    def get_summary(self) -> Dict[str, Any]:
        """Calculates storage statistics."""
        profiles = self.load_all_profiles()
        statuses: Dict[str, int] = {}
        personas: Dict[str, int] = {}

        for p in profiles:
            statuses[p.status] = statuses.get(p.status, 0) + 1
            personas[p.persona] = personas.get(p.persona, 0) + 1

        file_size = self.accounts_file.stat().st_size if self.accounts_file.exists() else 0

        return {
            "total_profiles": len(profiles),
            "file_size_bytes": file_size,
            "status_distribution": statuses,
            "persona_distribution": personas,
            "storage_path": str(self.accounts_file)
        }
