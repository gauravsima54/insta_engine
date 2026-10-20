import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { exec, execSync } from 'child_process';
import { createServer as createViteServer } from 'vite';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const isProd = process.env.NODE_ENV === 'production';

app.use(express.json());

// Path helper
const ACCOUNTS_FILE = path.join(__dirname, 'data', 'accounts.json');
const CONFIG_FILE = path.join(__dirname, 'config.yaml');
const LOGS_FILE = path.join(__dirname, 'logs', 'execution.log');

// Ensure directories
fs.mkdirSync(path.join(__dirname, 'data', 'avatars'), { recursive: true });
fs.mkdirSync(path.join(__dirname, 'logs'), { recursive: true });

// 1. GET /api/profiles - retrieve stored profiles and stats
app.get('/api/profiles', (req, res) => {
  try {
    if (!fs.existsSync(ACCOUNTS_FILE)) {
      return res.json({ profiles: [], total_count: 0 });
    }
    const raw = fs.readFileSync(ACCOUNTS_FILE, 'utf-8');
    const data = JSON.parse(raw);
    res.json(data);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// 2. POST /api/generate - run profile generation via Python
app.post('/api/generate', (req, res) => {
  const count = Math.min(Math.max(parseInt(req.body.count || 5, 10), 1), 50);
  const downloadAvatars = req.body.downloadAvatars ? '--download-avatars' : '';

  exec(`python3 main.py generate --count ${count} ${downloadAvatars}`, { cwd: __dirname }, (error, stdout, stderr) => {
    if (error) {
      console.error('Generation error:', stderr);
      return res.status(500).json({ error: stderr || error.message });
    }

    // Read updated data
    let data = { profiles: [], total_count: 0 };
    if (fs.existsSync(ACCOUNTS_FILE)) {
      try {
        data = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf-8'));
      } catch (e) {
        // ignore parse error
      }
    }

    res.json({
      success: true,
      output: stdout,
      data
    });
  });
});

// 3. POST /api/simulate - run multi-step simulation
app.post('/api/simulate', (req, res) => {
  const count = Math.min(Math.max(parseInt(req.body.count || 2, 10), 1), 20);
  const dryRun = req.body.dryRun !== false ? '--dry-run' : '';
  const rateLimitProb = parseFloat(req.body.rateLimitProb || 0);

  const rlArg = rateLimitProb > 0 ? `--inject-rate-limit ${rateLimitProb}` : '';
  const cmd = `python3 main.py simulate --count ${count} ${dryRun} ${rlArg}`;

  exec(cmd, { cwd: __dirname }, (error, stdout, stderr) => {
    let logs = '';
    if (fs.existsSync(LOGS_FILE)) {
      try {
        const fullLogs = fs.readFileSync(LOGS_FILE, 'utf-8');
        logs = fullLogs.split('\n').slice(-100).join('\n');
      } catch (e) {
        // ignore
      }
    }

    let updatedProfiles = [];
    if (fs.existsSync(ACCOUNTS_FILE)) {
      try {
        updatedProfiles = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf-8')).profiles || [];
      } catch (e) {
        // ignore
      }
    }

    res.json({
      success: !error,
      output: stdout,
      error: error ? stderr : null,
      logs,
      profiles: updatedProfiles
    });
  });
});

// 4. POST /api/benchmark - test jitter and backoff calculations
app.post('/api/benchmark', (req, res) => {
  const distribution = req.body.distribution || 'gaussian';
  const samples = Math.min(Math.max(parseInt(req.body.samples || 50, 10), 10), 200);

  const script = `
import json, random
from automation_engine.config import BehaviorConfig
from automation_engine.behavior import HumanBehaviorEngine, ExponentialBackoffHandler

config = BehaviorConfig(jitter_distribution="${distribution}")
engine = HumanBehaviorEngine(config)

delays = [engine.calculate_jitter_delay() for _ in range(${samples})]

# Backoff progression simulation
handler = ExponentialBackoffHandler(base_seconds=2.0, max_seconds=64.0)
backoff_samples = []
for attempt in range(1, 7):
    # generate 10 trials per attempt to illustrate full-jitter range
    trials = [handler.calculate_backoff(attempt) for _ in range(8)]
    ceiling = min(64.0, 2.0 * (2 ** attempt))
    backoff_samples.append({
        "attempt": attempt,
        "ceiling": ceiling,
        "sample_trials": trials,
        "average": round(sum(trials) / len(trials), 2)
    })

print(json.dumps({
    "distribution": "${distribution}",
    "delays": delays,
    "min": round(min(delays), 3),
    "max": round(max(delays), 3),
    "mean": round(sum(delays) / len(delays), 3),
    "backoff_progression": backoff_samples
}))
`;

  exec(`python3 -c '${script.replace(/'/g, "'\"'\"'")}'`, { cwd: __dirname }, (error, stdout, stderr) => {
    if (error) {
      return res.status(500).json({ error: stderr || error.message });
    }
    try {
      const result = JSON.parse(stdout);
      res.json(result);
    } catch (e: any) {
      res.status(500).json({ error: 'Failed to parse benchmark: ' + e.message, raw: stdout });
    }
  });
});

// 5. GET /api/codebase - returns all python source files for inspection & export
app.get('/api/codebase', (req, res) => {
  const files = [
    { path: 'main.py', category: 'Entrypoint' },
    { path: 'config.yaml', category: 'Configuration' },
    { path: 'requirements.txt', category: 'Dependencies' },
    { path: 'automation_engine/__init__.py', category: 'Module Init' },
    { path: 'automation_engine/config.py', category: 'Config Manager' },
    { path: 'automation_engine/generator.py', category: 'Profile Generator' },
    { path: 'automation_engine/behavior.py', category: 'Behavior Engine' },
    { path: 'automation_engine/data_manager.py', category: 'Data Manager' },
    { path: 'automation_engine/scheduler.py', category: 'Task Scheduler' },
    { path: 'automation_engine/logger.py', category: 'Execution Logger' },
    { path: 'automation_engine/cli.py', category: 'CLI Controller' },
    { path: 'tests/test_generator.py', category: 'Tests' },
    { path: 'tests/test_behavior.py', category: 'Tests' },
    { path: 'tests/test_data_manager.py', category: 'Tests' },
    { path: '.github/workflows/profile_simulation.yml', category: 'Cloud Runner / CI' },
    { path: 'README.md', category: 'Documentation' },
  ];

  const result = files.map(item => {
    const fullPath = path.join(__dirname, item.path);
    let content = '';
    let size = 0;
    if (fs.existsSync(fullPath)) {
      content = fs.readFileSync(fullPath, 'utf-8');
      size = fs.statSync(fullPath).size;
    }
    return {
      path: item.path,
      category: item.category,
      size,
      content
    };
  });

  res.json({ files: result });
});

// 6. GET /api/download-zip - generates and downloads complete .zip package
app.get('/api/download-zip', (req, res) => {
  try {
    const zipPath = path.join(__dirname, 'data', 'personapulse_engine.zip');
    const zipScript = `
import zipfile, os
files = [
    'main.py', 'config.yaml', 'requirements.txt', 'README.md',
    'automation_engine/__init__.py', 'automation_engine/config.py',
    'automation_engine/generator.py', 'automation_engine/behavior.py',
    'automation_engine/data_manager.py', 'automation_engine/scheduler.py',
    'automation_engine/logger.py', 'automation_engine/cli.py',
    'tests/test_generator.py', 'tests/test_behavior.py', 'tests/test_data_manager.py',
    '.github/workflows/profile_simulation.yml'
]
with zipfile.ZipFile('${zipPath}', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for f in files:
        if os.path.exists(f):
            zipf.write(f, arcname=f)
print("ZIP_CREATED")
`;
    execSync(`python3 -c "${zipScript.replace(/"/g, '\\"')}"`, { cwd: __dirname });

    res.download(zipPath, 'personapulse_automation_suite.zip');
  } catch (err: any) {
    res.status(500).json({ error: 'Failed to build zip: ' + err.message });
  }
});

// 7. GET /api/logs - fetch latest execution logs
app.get('/api/logs', (req, res) => {
  if (fs.existsSync(LOGS_FILE)) {
    try {
      const content = fs.readFileSync(LOGS_FILE, 'utf-8');
      const lines = content.split('\n').filter(Boolean);
      return res.json({ logs: lines.slice(-200) });
    } catch (e: any) {
      return res.status(500).json({ error: e.message });
    }
  }
  res.json({ logs: [] });
});

async function startServer() {
  if (!isProd) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, () => {
    console.log(`PersonaPulse Server & Automation Engine running on port ${PORT}`);
  });
}

startServer();
