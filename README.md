# PersonaPulse: Production Profile Automation & Behavioral Pacing Suite

**PersonaPulse** is a modular, production-ready Python application engineered for automated profile generation, task scheduling simulation, human-like pacing with randomized jitter, and graceful exponential backoff under rate limits.

Optimized for **headless Linux environments**, **continuous testing**, and **GitHub Actions cloud runners**.

---

## Architecture Overview

```
                      ┌─────────────────────────────────────────┐
                      │          EngineConfig (YAML/Env)        │
                      └────────────────────┬────────────────────┘
                                           │
         ┌─────────────────────────────────┼────────────────────────────────┐
         ▼                                 ▼                                ▼
┌─────────────────────┐         ┌─────────────────────┐          ┌─────────────────────┐
│  Profile Generator  │         │   Behavior Engine   │          │    Data Manager     │
│  - Names & Bios     │         │  - Gaussian Jitter  │          │  - Atomic JSON swap │
│  - Avatar Fetcher   │         │  - Cooldown Cycles  │          │  - Safe backups     │
│  - Image Validation │         │  - Full-Jitter Exp  │          │  - CSV/JSON Export  │
└──────────┬──────────┘         └──────────┬──────────┘          └──────────┬──────────┘
           │                               │                                │
           └───────────────────────┬───────┴────────────────────────────────┘
                                   ▼
                      ┌─────────────────────────┐
                      │     Task Scheduler      │
                      │  - Multi-step workflows │
                      │  - Rate-limit recovery  │
                      │  - Signal interception  │
                      └────────────┬────────────┘
                                   │
                      ┌────────────▼────────────┐
                      │ ExecutionLogger (CI/TTY)│
                      └─────────────────────────┘
```

### Core Components

1. **Profile Metadata Generator (`automation_engine/generator.py`)**
   - Synthesizes organic names across diverse international pools.
   - Generates natural, casual human bios using multi-part syntactic templates (roles, casual hobbies, lifestyle closures).
   - Fetches placeholder avatars from public endpoints (Unsplash, Pravatar) with binary image header validation (JPEG/PNG magic bytes).
   - Embedded SVG fallback generator ensures 100% test completion even in air-gapped sandboxes or network timeouts.

2. **Human-Like Behavior Engine (`automation_engine/behavior.py`)**
   - **Randomized Jitter Models**:
     - **Gaussian**: Normal bell-curve distribution centered around base delay with standard deviation clamping.
     - **Uniform**: Flat randomized bounding between configured minimum and maximum bounds.
     - **Pareto**: 80/20 bursts (80% quick micro-delays mimicking typing, 20% cognitive pauses for reading/thinking).
   - **Cooldown Management**: Automatic rest intervals (e.g. 15s–45s) triggered after every $N$ consecutive actions to emulate human user fatigue and stepping away.
   - **Exponential Backoff with Full Jitter**:
     $$\text{Sleep} = \text{Uniform}\left(0, \min\left(\text{MaxBackoff}, \text{BaseBackoff} \times 2^{\text{attempt}}\right)\right)$$
     Gracefully parses HTTP 429 `Retry-After` headers and prevents thundering herd congestion.

3. **Data Management (`automation_engine/data_manager.py`)**
   - High-reliability storage into `data/accounts.json`.
   - **Atomic Write Guarantee**: Writes to a temporary file on the target filesystem, executes `os.fsync()`, then atomically renames (`os.replace`) to ensure zero file corruption on container kills.
   - Automatic `.json.bak` snapshot creation prior to destructive modifications.

4. **Task Scheduler & Execution Logging (`automation_engine/scheduler.py`, `logger.py`)**
   - Coordinates profile lifecycle stages: `ACCOUNT_REGISTRATION` $\to$ `DOWNLOAD_AVATAR` $\to$ `UPDATE_BIO_AND_TAGS` $\to$ `VERIFY_CREDENTIALS`.
   - Headless-first logging: Colorized ANSI output in interactive terminal; clean, unescaped logs or single-line JSON formatting when running under CI/CD (`CI=true` or `--json-logs`).
   - Signal handling (`SIGINT`, `SIGTERM`) for zero-data-loss shutdown in Docker containers and Kubernetes pods.

---

## Quickstart & Installation

### 1. Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`:
  - `requests>=2.31.0`
  - `Pillow>=10.2.0`
  - `PyYAML>=6.0.1`
  - `tabulate>=0.9.0`
  - `pytest>=8.0.0`

### 2. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

*(Note: PersonaPulse includes built-in standard library fallbacks for `urllib` and JSON configuration, allowing operation even in zero-dependency environments).*

### 3. Run Unit Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## Command-Line Interface (CLI)

The application provides a unified CLI via `main.py`:

### Generate Realistic Profiles
```bash
# Generate 10 profiles and save to data/accounts.json
python main.py generate --count 10

# Generate with avatar downloads and export directly to CSV
python main.py generate --count 5 --download-avatars --export-csv exports/profiles.csv
```

### Run Paced Simulation
```bash
# Run multi-step automated setup with real human jitter and cooldowns
python main.py simulate --count 3

# Fast dry-run mode (calculates timing without sleeping)
python main.py simulate --count 5 --dry-run

# Test rate-limit resilience with simulated 30% HTTP 429 injection
python main.py simulate --count 3 --inject-rate-limit 0.30 --dry-run
```

### Benchmark Behavioral Jitter & Backoff
```bash
# Evaluate statistical distribution of delays (Gaussian model)
python main.py test-behavior --samples 100 --distribution gaussian

# Benchmark Pareto 80/20 burst distribution + verify 5-step exponential backoff
python main.py test-behavior --samples 50 --distribution pareto --test-backoff
```

### Inspect Stored Profiles
```bash
python main.py list --limit 15
python main.py export --format csv --output exports/accounts.csv
```

---

## Configuration (`config.yaml`)

Configuration can be customized via `config.yaml` or overridden via environment variables:

```yaml
app_name: "PersonaPulse"
environment: "headless_production"

behavior:
  base_delay_seconds: 3.5
  jitter_min_seconds: 1.2
  jitter_max_seconds: 6.8
  jitter_distribution: "gaussian"  # gaussian | uniform | pareto
  gaussian_std_dev: 1.25
  cooldown_after_actions: 4
  cooldown_min_seconds: 15.0
  cooldown_max_seconds: 40.0
  max_backoff_retries: 5
  backoff_base_seconds: 2.0
  backoff_max_seconds: 64.0
  backoff_jitter_factor: 1.0

profile_generator:
  avatar_download_dir: "data/avatars"
  validate_image_headers: true
  max_avatar_size_bytes: 5242880
  personas_pool:
    - "tech_enthusiast"
    - "digital_nomad"
    - "creative_designer"
    - "coffee_devotee"
    - "fitness_runner"
    - "open_source_builder"
    - "photographer"

storage:
  accounts_file: "data/accounts.json"
  audit_log_file: "logs/execution.log"
  atomic_writes: true
  backup_on_save: true
```

### Environment Variable Overrides
- `PERSONAPULSE_ENV`: Environment tag (`development`, `ci`, `headless_production`)
- `PERSONAPULSE_ACCOUNTS_FILE`: Path to custom accounts JSON file
- `PERSONAPULSE_BASE_DELAY`: Base delay in seconds
- `PERSONAPULSE_JITTER_MAX`: Maximum jitter ceiling

---

## Cloud Runner & Headless Linux Deployment

### Option A: GitHub Actions (Scheduled Cloud Runner)
A complete workflow is provided at `.github/workflows/profile_simulation.yml`.
It executes on a configurable cron schedule (`0 */6 * * *`) or manual dispatch, runs the test suite, executes the simulation, exports CSV data, and uploads artifacts to GitHub storage.

### Option B: Linux Systemd Service (Headless Server)
Create `/etc/systemd/system/personapulse.service`:

```ini
[Unit]
Description=PersonaPulse Profile Automation Daemon
After=network.target

[Service]
Type=simple
User=automation
WorkingDirectory=/opt/personapulse
ExecStart=/opt/personapulse/venv/bin/python main.py simulate --count 20
Restart=on-failure
RestartSec=30
Environment=PYTHONUNBUFFERED=1
Environment=PERSONAPULSE_ENV=headless_production

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now personapulse.service
sudo journalctl -u personapulse.service -f
```

### Option C: Cron Job on Headless Linux
```bash
# Run simulation every 3 hours and append to logs
0 */3 * * * cd /opt/personapulse && ./venv/bin/python main.py simulate --count 5 >> logs/cron.log 2>&1
```

---

## Data Schema (`data/accounts.json`)

```json
{
  "schema_version": "1.0",
  "last_updated": "2026-10-20T17:28:02.000000Z",
  "total_count": 1,
  "profiles": [
    {
      "id": "5c893608-fca0-410e-8bb2-3112c3b2909a",
      "first_name": "Elena",
      "last_name": "Vance",
      "full_name": "Elena Vance",
      "username": "elena.vance92",
      "email": "elena.vance92@proton.me",
      "bio": "Systems engineer obsessed with distributed consensus. Into sourdough hydration experiments. Obsessed with details that matter.",
      "persona": "tech_enthusiast",
      "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80",
      "local_avatar_path": "data/avatars/avatar_5c893608.jpg",
      "location": "Seattle, WA",
      "timezone": "America/Los_Angeles",
      "status": "verified",
      "created_at": "2026-10-20T17:28:01.000000Z",
      "metadata": {
        "locale": "en_US",
        "browser_fingerprint": "chrome_v124_linux_5c8936",
        "simulated_trust_score": 0.94,
        "tags": ["tech_enthusiast", "seattle"]
      }
    }
  ]
}
```
