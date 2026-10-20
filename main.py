#!/usr/bin/env python3
"""
PersonaPulse - Automated Profile Generation & Behavioral Pacing Suite.
Main executable entry point for headless execution, automated testing, and CI/CD pipelines.

Usage:
    python main.py --help
    python main.py generate --count 5
    python main.py simulate --count 2 --dry-run
    python main.py test-behavior --test-backoff
"""

import sys
from automation_engine.cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
