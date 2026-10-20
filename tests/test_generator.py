"""
Unit tests for ProfileMetadataGenerator.
Verifies name plausibility, bio generation, structured profile dictionary conversion,
and offline fallback avatar creation.
"""

import unittest
from automation_engine.config import ProfileGenConfig
from automation_engine.generator import ProfileMetadataGenerator, GeneratedProfile


class TestProfileGenerator(unittest.TestCase):

    def setUp(self):
        self.config = ProfileGenConfig()
        self.generator = ProfileMetadataGenerator(self.config)

    def test_generate_name(self):
        first, last, full = self.generator.generate_name()
        self.assertTrue(len(first) > 1)
        self.assertTrue(len(last) > 1)
        self.assertEqual(full, f"{first} {last}")

    def test_generate_username(self):
        username = self.generator.generate_username("Elena", "Vance")
        self.assertTrue(len(username) > 3)
        self.assertTrue("elena" in username.lower() or "vance" in username.lower())

    def test_generate_email(self):
        email = self.generator.generate_email("elena.vance")
        self.assertIn("@", email)
        self.assertTrue(email.endswith((".com", ".me")))

    def test_generate_bio(self):
        bio = self.generator.generate_bio("tech_enthusiast")
        self.assertTrue(len(bio) > 20)
        self.assertIsInstance(bio, str)

    def test_generate_single_profile(self):
        profile = self.generator.generate_single_profile(download_avatar=False)
        self.assertIsInstance(profile, GeneratedProfile)
        self.assertEqual(profile.status, "pending")
        self.assertTrue(profile.email.count("@") == 1)
        self.assertTrue(profile.avatar_url.startswith("http"))
        self.assertIn("tags", profile.metadata)

    def test_fallback_avatar_generation(self):
        svg = self.generator._generate_fallback_svg_avatar("test-profile-seed")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>"))
        self.assertIn("TE", svg)  # Uppercase initials of test-profile-seed


if __name__ == "__main__":
    unittest.main()
