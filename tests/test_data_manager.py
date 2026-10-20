"""
Unit tests for DataManager.
Verifies atomic saving, loading, status updates, and backup creation.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from automation_engine.config import StorageConfig
from automation_engine.data_manager import DataManager
from automation_engine.generator import ProfileMetadataGenerator


class TestDataManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.accounts_file = str(Path(self.test_dir) / "accounts.json")
        self.config = StorageConfig(
            data_directory=self.test_dir,
            accounts_file=self.accounts_file,
            atomic_writes=True,
            backup_on_save=True
        )
        self.data_manager = DataManager(self.config)
        self.generator = ProfileMetadataGenerator()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load_profiles(self):
        profiles = self.generator.generate_batch(3)
        self.data_manager.save_all_profiles(profiles)

        loaded = self.data_manager.load_all_profiles()
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[0].id, profiles[0].id)
        self.assertEqual(loaded[0].full_name, profiles[0].full_name)

    def test_atomic_status_update(self):
        profile = self.generator.generate_single_profile()
        self.data_manager.add_profile(profile)

        updated = self.data_manager.update_status(profile.id, "active", {"tag": "updated_test"})
        self.assertTrue(updated)

        reloaded = self.data_manager.get_profile(profile.id)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.status, "active")
        self.assertEqual(reloaded.metadata.get("tag"), "updated_test")

    def test_export_to_csv(self):
        profiles = self.generator.generate_batch(2)
        self.data_manager.save_all_profiles(profiles)
        csv_path = str(Path(self.test_dir) / "export.csv")
        self.data_manager.export_to_csv(csv_path)

        self.assertTrue(Path(csv_path).exists())
        content = Path(csv_path).read_text(encoding="utf-8")
        self.assertIn("username", content)
        self.assertIn(profiles[0].username, content)


if __name__ == "__main__":
    unittest.main()
