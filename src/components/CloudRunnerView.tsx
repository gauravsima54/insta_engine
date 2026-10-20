import React, { useState } from 'react';
import { Terminal, Copy, Check, Server, GitBranch, Cpu, ShieldCheck } from 'lucide-react';

export const CloudRunnerView: React.FC = () => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const systemdContent = `[Unit]
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
WantedBy=multi-user.target`;

  const cronContent = `# PersonaPulse: Generate 5 profiles and run paced simulation every 4 hours
0 */4 * * * cd /opt/personapulse && ./venv/bin/python main.py simulate --count 5 >> logs/cron.log 2>&1`;

  const dockerContent = `FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY automation_engine/ ./automation_engine/
COPY main.py config.yaml ./

# Configure non-root user for security
RUN useradd -m -u 1000 automation && \\
    mkdir -p data logs && \\
    chown -R automation:automation /app
USER automation

ENV PYTHONUNBUFFERED=1
ENV PERSONAPULSE_ENV=headless_production

ENTRYPOINT ["python", "main.py"]
CMD ["simulate", "--count", "5"]`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-xl font-bold tracking-tight text-white">Headless Linux & Cloud Runner Architecture</h2>
        <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
          <span>Continuous Testing</span>
          <span aria-hidden="true">·</span>
          <span>Zero-GUI Headless Mode</span>
          <span aria-hidden="true">·</span>
          <span>Signal Handlers (SIGTERM/SIGINT)</span>
        </div>
      </div>

      {/* Cloud Runner Methods */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Method 1: GitHub Actions */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-purple-400" />
              <span>GitHub Actions Cloud Runner</span>
            </h3>
            <span className="text-[11px] font-mono text-emerald-400">Included in Repo</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            The repository contains a fully automated workflow at <code className="font-mono text-emerald-400">.github/workflows/profile_simulation.yml</code>. It runs scheduled tasks, executes unit tests, performs human-paced profile generation, and publishes datasets to GitHub Artifacts.
          </p>

          <div className="space-y-2 text-xs">
            <div className="bg-slate-950 p-3 rounded border border-slate-800 space-y-1.5">
              <span className="text-slate-400 font-semibold block">Key Workflow Features:</span>
              <ul className="space-y-1 text-slate-300 list-disc list-inside">
                <li>Automatic cron trigger: <code className="font-mono text-slate-400">0 */6 * * *</code></li>
                <li>Manual dispatch trigger with dynamic profile count inputs</li>
                <li>Matrix unit test verification before simulation</li>
                <li>Automated export to CSV and 14-day artifact retention</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Method 2: Systemd Linux Daemon */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-400" />
              <span>Linux Systemd Service Unit</span>
            </h3>
            <button
              onClick={() => copyToClipboard(systemdContent, 'systemd')}
              className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white cursor-pointer"
            >
              {copiedKey === 'systemd' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedKey === 'systemd' ? 'Copied' : 'Copy Unit'}</span>
            </button>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            For dedicated Ubuntu/Debian/RHEL runner nodes, install as a system service with auto-recovery on failure:
          </p>

          <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto max-h-48">
            {systemdContent}
          </pre>
        </div>

        {/* Method 3: Cron Schedule */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>Headless Cron Job Execution</span>
            </h3>
            <button
              onClick={() => copyToClipboard(cronContent, 'cron')}
              className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white cursor-pointer"
            >
              {copiedKey === 'cron' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedKey === 'cron' ? 'Copied' : 'Copy Cron'}</span>
            </button>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Add to runner crontab via <code className="font-mono text-emerald-400">crontab -e</code> for headless unattended profile generation:
          </p>

          <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-xs font-mono text-amber-300 overflow-x-auto">
            {cronContent}
          </pre>
        </div>

        {/* Method 4: Docker Container */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Production Dockerfile</span>
            </h3>
            <button
              onClick={() => copyToClipboard(dockerContent, 'docker')}
              className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white cursor-pointer"
            >
              {copiedKey === 'docker' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedKey === 'docker' ? 'Copied' : 'Copy Dockerfile'}</span>
            </button>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Hermetic container build without GUI dependencies or bloated display managers:
          </p>

          <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-xs font-mono text-cyan-300 overflow-x-auto max-h-48">
            {dockerContent}
          </pre>
        </div>
      </div>
    </div>
  );
};
