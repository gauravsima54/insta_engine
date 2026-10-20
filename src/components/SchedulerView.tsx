import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, AlertTriangle, Terminal, CheckCircle2, Clock } from 'lucide-react';

interface SchedulerViewProps {
  onSimulationComplete: () => void;
}

export const SchedulerView: React.FC<SchedulerViewProps> = ({ onSimulationComplete }) => {
  const [profileCount, setProfileCount] = useState(2);
  const [dryRun, setDryRun] = useState(true);
  const [rateLimitProb, setRateLimitProb] = useState(0.0);
  const [isRunning, setIsRunning] = useState(false);
  const [liveLogs, setLiveLogs] = useState<string[]>([]);
  const [summary, setSummary] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      const data = await res.json();
      if (data.logs) {
        setLiveLogs(data.logs);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setSummary('Executing automation scheduler via python main.py...');
    try {
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          count: profileCount,
          dryRun,
          rateLimitProb
        })
      });
      const data = await res.json();
      if (data.logs) {
        setLiveLogs(data.logs.split('\n'));
      }
      setSummary(data.output || 'Simulation finished successfully.');
      onSimulationComplete();
    } catch (err: any) {
      setSummary('Execution error: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-xl font-bold tracking-tight text-white">Task Scheduler & Paced Simulation Console</h2>
        <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
          <span>Module: <code className="font-mono text-slate-300">automation_engine/scheduler.py</code></span>
          <span aria-hidden="true">·</span>
          <span>Sequential Graph Execution</span>
          <span aria-hidden="true">·</span>
          <span>Headless Linux Optimized</span>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
        <h3 className="text-sm font-bold text-white">Execution Parameters</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="text-slate-300 block mb-1 font-medium">Batch Profile Count</label>
            <input
              type="number"
              min={1}
              max={10}
              value={profileCount}
              onChange={(e) => setProfileCount(parseInt(e.target.value, 10) || 1)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-200 font-mono text-sm focus:outline-none focus:border-emerald-500"
            />
            <span className="text-[11px] text-slate-500 mt-0.5 block">Schedules 4 lifecycle steps per profile</span>
          </div>

          <div>
            <label className="text-slate-300 block mb-1 font-medium">Execution Mode</label>
            <div className="flex items-center gap-2 mt-1">
              <button
                type="button"
                onClick={() => setDryRun(true)}
                className={`flex-1 py-2 px-3 rounded text-xs font-medium cursor-pointer transition-colors ${
                  dryRun
                    ? 'bg-emerald-400 text-slate-950 font-bold'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Dry Run (Instant)
              </button>
              <button
                type="button"
                onClick={() => setDryRun(false)}
                className={`flex-1 py-2 px-3 rounded text-xs font-medium cursor-pointer transition-colors ${
                  !dryRun
                    ? 'bg-amber-400 text-slate-950 font-bold'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Real-Time Human Pacing
              </button>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              {dryRun ? 'Calculates jitter delays without physical wait' : 'Enforces real time.sleep pauses & cooldowns'}
            </span>
          </div>

          <div>
            <label className="text-slate-300 block mb-1 font-medium">429 Rate-Limit Fault Injection</label>
            <select
              value={rateLimitProb}
              onChange={(e) => setRateLimitProb(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-emerald-500"
            >
              <option value="0.0">0% (Normal Flow)</option>
              <option value="0.25">25% Chance (Test Backoff)</option>
              <option value="0.50">50% Chance (Aggressive Stress)</option>
            </select>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Tests Exponential Backoff recovery</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-400">
            Lifecycle: <span className="text-slate-300 font-mono">REGISTRATION → AVATAR_FETCH → BIO_UPDATE → VERIFY</span>
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2 text-xs font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 rounded-md transition-colors cursor-pointer disabled:opacity-50 shadow-sm"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isRunning ? 'Running Simulation...' : 'Execute Task Schedule'}</span>
          </button>
        </div>
      </div>

      {/* Execution Summary Notification */}
      {summary && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <h4 className="text-xs uppercase font-semibold text-slate-400 mb-1">Process Output</h4>
          <pre className="text-xs font-mono text-emerald-400 whitespace-pre-wrap leading-relaxed max-h-36 overflow-y-auto">
            {summary}
          </pre>
        </div>
      )}

      {/* Live Terminal Log Stream */}
      <div className="bg-slate-950 border border-slate-800 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-mono font-medium">
            <Terminal className="w-3.5 h-3.5 text-emerald-400" />
            <span>execution.log (Headless CI / Local Terminal Stream)</span>
          </div>
          <button
            onClick={fetchLogs}
            className="text-slate-400 hover:text-white transition-colors cursor-pointer text-[11px]"
          >
            Refresh Logs
          </button>
        </div>

        <div className="p-4 font-mono text-xs text-slate-300 max-h-80 overflow-y-auto space-y-1 scrollbar-thin">
          {liveLogs.length === 0 ? (
            <p className="text-slate-500 italic">No logs recorded yet. Run a simulation to populate telemetry.</p>
          ) : (
            liveLogs.map((log, idx) => {
              const isWarning = log.includes('WARNING') || log.includes('COOLDOWN') || log.includes('RATE LIMIT');
              const isInfo = log.includes('INFO');
              const isSuccess = log.includes('✔');
              return (
                <div
                  key={idx}
                  className={`leading-relaxed ${
                    isWarning
                      ? 'text-amber-400'
                      : isSuccess
                      ? 'text-emerald-400'
                      : 'text-slate-300'
                  }`}
                >
                  {log}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
