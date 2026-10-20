"""
Profile Metadata Generator for PersonaPulse.
Generates realistic human names, dynamic natural-sounding bios,
fetches placeholder profile images from public endpoints, and validates assets.
"""

from __future__ import annotations
import hashlib
import json
import os
import random
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4
from .config import ProfileGenConfig


@dataclass
class GeneratedProfile:
    """Structured representation of an automated profile configuration."""
    id: str
    first_name: str
    last_name: str
    full_name: str
    username: str
    email: str
    bio: str
    persona: str
    avatar_url: str
    local_avatar_path: Optional[str]
    location: str
    timezone: str
    status: str = "pending"  # "pending", "active", "cooldown", "verified"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneratedProfile":
        return cls(**data)


class ProfileMetadataGenerator:
    """Generates human-like profile attributes and fetches placeholder avatars."""

    FIRST_NAMES = [
        "Elena", "Marcus", "Sophia", "Liam", "Amara", "Kai", "Chloe", "Mateo",
        "Aria", "Julian", "Zoe", "Niko", "Maya", "Dante", "Nadia", "Caleb",
        "Isla", "Ethan", "Sienna", "Jaxon", "Freya", "Lucas", "Naomi", "Owen",
        "Leila", "Gabriel", "Talia", "Asher", "Camila", "Rowan"
    ]

    LAST_NAMES = [
        "Vance", "Mercer", "Lindqvist", "Chen", "Kowalski", "Patel", "Sinclair",
        "Moreno", "Kaufmann", "O'Connor", "Takahashi", "Delgado", "Sterling",
        "Al-Mansoor", "Novak", "Hawthorne", "Dubois", "Kim", "Westbrook", "Silva"
    ]

    ROLES_BY_PERSONA = {
        "tech_enthusiast": [
            "Systems engineer obsessed with distributed consensus and low-latency code",
            "Full-stack software developer exploring Rust and web assembly",
            "Cloud infrastructure engineer who still loves physical server racks",
            "Self-taught developer building developer tools and automated testing pipelines"
        ],
        "creative_designer": [
            "UI/UX product designer focused on accessible typography and design systems",
            "Brand strategist and digital illustrator crafting thoughtful brand identities",
            "Motion designer turning complex software interactions into fluid animations",
            "Design generalist bridging human research and production code"
        ],
        "digital_nomad": [
            "Remote product consultant currently working between Lisbon and Tokyo",
            "Async-first workflow advocate, writing documentation from coffee shops worldwide",
            "Technical writer and documentation enthusiast living out of a carry-on pack",
            "Independent software consultant researching distributed team collaboration"
        ],
        "coffee_devotee": [
            "Specialty coffee roaster and amateur espresso machine repair person",
            "Pour-over fanatic tracking brew ratios in meticulously formatted spreadsheets",
            "Barista turned developer who measures productivity in single-origin beans",
            "Searching for the ultimate light roast across third-wave cafes"
        ],
        "fitness_runner": [
            "Marathon trainee balancing long Sunday runs with software deployments",
            "Trail runner and ultra-distance enthusiast testing GPS watch accuracy",
            "Gravel cyclist and weekend endurance athlete with a passion for data logs",
            "Strength and mobility advocate keeping active away from the desk"
        ],
        "open_source_builder": [
            "Open source maintainer and clean code advocate",
            "Building small, resilient CLI utilities in Python and Go",
            "Passionate about reproducible builds, open standards, and public software",
            "Fixing edge-case bugs and writing clear issue reproduction steps"
        ],
        "photographer": [
            "Architectural and street photographer capturing quiet morning light",
            "Analog 35mm film photographer with a darkroom hobby and digital hybrid workflow",
            "Documentary photographer exploring industrial spaces and urban geometry",
            "Chasing natural textures, overcast skies, and balanced compositions"
        ]
    }

    CASUAL_INTERESTS = [
        "mechanical keyboards and vintage audio gear",
        "sourdough hydration experiments",
        "collecting Japanese stationery and fountain pens",
        "weekend mountain hikes with my golden retriever",
        "curating obscure electronic ambient playlists",
        "restoring mid-century modern furniture",
        "sci-fi novels from the 1970s",
        "fermenting hot sauces and ginger beer",
        "learning classical guitar fingerpicking"
    ]

    MOTTO_CLOSERS = [
        "Always building something new.",
        "Obsessed with details that matter.",
        "Keeping things delightfully simple.",
        "Good design is quiet design.",
        "Coffee first, troubleshooting second.",
        "Curious by default.",
        "Writing clean tests so future me can sleep peacefully.",
        "Working in the open."
    ]

    LOCATIONS = [
        ("Seattle, WA", "America/Los_Angeles"),
        ("Austin, TX", "America/Chicago"),
        ("Brooklyn, NY", "America/New_York"),
        ("London, UK", "Europe/London"),
        ("Berlin, Germany", "Europe/Berlin"),
        ("Toronto, Canada", "America/Toronto"),
        ("Amsterdam, Netherlands", "Europe/Amsterdam"),
        ("Denver, CO", "America/Denver"),
        ("Stockholm, Sweden", "Europe/Stockholm"),
        ("Melbourne, Australia", "Australia/Melbourne")
    ]

    # Public verified portrait endpoints with diverse human profiles
    PUBLIC_AVATARS = [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?w=400&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=400&auto=format&fit=crop&q=80"
    ]

    def __init__(self, config: Optional[ProfileGenConfig] = None):
        self.config = config or ProfileGenConfig()
        self.avatar_pool = self.config.avatar_sources if self.config.avatar_sources else self.PUBLIC_AVATARS
        # Ensure output directory exists
        Path(self.config.avatar_download_dir).mkdir(parents=True, exist_ok=True)

    def generate_name(self) -> tuple[str, str, str]:
        """Generates realistic (first_name, last_name, full_name)."""
        first = random.choice(self.FIRST_NAMES)
        last = random.choice(self.LAST_NAMES)
        return first, last, f"{first} {last}"

    def generate_username(self, first_name: str, last_name: str) -> str:
        """Generates organic usernames avoiding bot-like randomized character strings."""
        first = re.sub(r"[^a-zA-Z]", "", first_name).lower()
        last = re.sub(r"[^a-zA-Z]", "", last_name).lower()
        num_suffix = random.choice(["", str(random.randint(2, 99)), str(random.randint(1985, 2002))])

        formats = [
            f"{first}.{last}{num_suffix}",
            f"{first}_{last}",
            f"{first}{last[:1]}_{random.choice(['dev', 'design', 'lab', 'build', 'io'])}",
            f"{random.choice(['the', 'iam', 'real'])}_{first}{last}",
            f"{last}.{first}{num_suffix}",
            f"{first}{last}{num_suffix}"
        ]
        return random.choice(formats)

    def generate_email(self, username: str) -> str:
        """Generates clean corporate or standard email handles."""
        domains = ["gmail.com", "outlook.com", "proton.me", "icloud.com", "fastmail.com"]
        clean_user = username.replace(".", "_") if random.random() > 0.5 else username
        return f"{clean_user}@{random.choice(domains)}"

    def generate_bio(self, persona: str) -> str:
        """Generates a natural, casual, human-written bio using multi-part syntactic templates."""
        role_candidates = self.ROLES_BY_PERSONA.get(persona, self.ROLES_BY_PERSONA["tech_enthusiast"])
        primary_role = random.choice(role_candidates)
        interest = random.choice(self.CASUAL_INTERESTS)
        closer = random.choice(self.MOTTO_CLOSERS)

        templates = [
            f"{primary_role}. Big fan of {interest}. {closer}",
            f"{primary_role} · Into {interest} · {closer}",
            f"By day: {primary_role}. Outside the screen: {interest}. {closer}",
            f"{primary_role}. When not shipping updates, you can find me enjoying {interest}.",
            f"{primary_role} | {closer} Enthusiast for {interest}."
        ]
        return random.choice(templates)

    def select_avatar_url(self) -> str:
        """Selects a public placeholder portrait URL."""
        return random.choice(self.avatar_pool)

    def download_and_verify_avatar(
        self,
        image_url: str,
        profile_id: str,
        timeout: float = 8.0
    ) -> Optional[str]:
        """
        Downloads placeholder picture from public endpoint and validates image integrity.
        Includes a local offline SVG/PNG fallback if network is unreachable in sandbox/CI.
        """
        target_dir = Path(self.config.avatar_download_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"avatar_{profile_id[:8]}.jpg"
        target_path = target_dir / filename

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        }

        try:
            req = urllib.request.Request(image_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read()

                # Basic size validation
                if len(content) > self.config.max_avatar_size_bytes:
                    raise ValueError(f"Avatar exceeded max bytes ({len(content)})")

                # Verify image magic bytes (JPEG or PNG)
                is_jpeg = content.startswith(b"\xff\xd8\xff")
                is_png = content.startswith(b"\x89PNG\r\n\x1a\n")
                if self.config.validate_image_headers and not (is_jpeg or is_png):
                    raise ValueError("Downloaded file does not match JPEG or PNG magic header")

                target_path.write_bytes(content)
                return str(target_path)

        except Exception:
            # Fallback for offline sandboxes, hermetic CI runners, or rate-limited public APIs
            # Synthesize an authentic profile badge so workflow NEVER fails
            fallback_path = target_dir / f"avatar_{profile_id[:8]}_fallback.svg"
            svg_content = self._generate_fallback_svg_avatar(profile_id)
            fallback_path.write_text(svg_content, encoding="utf-8")
            return str(fallback_path)

    def _generate_fallback_svg_avatar(self, seed: str) -> str:
        """Generates a clean vector avatar when offline or in hermetic cloud runners."""
        h = int(hashlib.md5(seed.encode()).hexdigest()[:6], 16)
        colors = [
            ("#3b82f6", "#1e3a8a"),
            ("#10b981", "#064e3b"),
            ("#8b5cf6", "#4c1d95"),
            ("#f59e0b", "#78350f"),
            ("#ec4899", "#831843"),
            ("#06b6d4", "#164e63"),
        ]
        bg1, bg2 = colors[h % len(colors)]
        initials = seed[:2].upper()
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg1}"/>
      <stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="100" fill="url(#grad)" />
  <text x="50%" y="54%" font-family="Plus Jakarta Sans, sans-serif" font-size="64" font-weight="bold" fill="#ffffff" dominant-baseline="middle" text-anchor="middle">{initials}</text>
</svg>"""

    def generate_single_profile(self, download_avatar: bool = False) -> GeneratedProfile:
        """Assembles a complete, ready-to-use profile instance."""
        profile_id = str(uuid4())
        first_name, last_name, full_name = self.generate_name()
        username = self.generate_username(first_name, last_name)
        email = self.generate_email(username)
        persona = random.choice(self.config.personas_pool)
        bio = self.generate_bio(persona)
        avatar_url = self.select_avatar_url()
        location, tz = random.choice(self.LOCATIONS)

        local_path = None
        if download_avatar:
            local_path = self.download_and_verify_avatar(avatar_url, profile_id)

        return GeneratedProfile(
            id=profile_id,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            username=username,
            email=email,
            bio=bio,
            persona=persona,
            avatar_url=avatar_url,
            local_avatar_path=local_path,
            location=location,
            timezone=tz,
            status="pending",
            metadata={
                "locale": self.config.default_locale,
                "browser_fingerprint": f"chrome_v124_linux_{profile_id[:6]}",
                "simulated_trust_score": round(random.uniform(0.82, 0.99), 2),
                "tags": [persona, location.split(",")[0].lower().replace(" ", "_")]
            }
        )

    def generate_batch(self, count: int, download_avatars: bool = False) -> List[GeneratedProfile]:
        """Generates multiple profiles."""
        return [self.generate_single_profile(download_avatar=download_avatars) for _ in range(count)]
