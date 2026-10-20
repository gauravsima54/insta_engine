import React, { useState, useEffect } from 'react';
import { BenchmarkData } from '../types';
import { Activity, ShieldAlert, Zap, Clock, RefreshCw, BarChart2 } from 'lucide-react';

export const BehaviorView: React.FC = () => {
  const [distribution, setDistribution] = useState<'gaussian' | 'uniform' | 'pareto'>('gaussian');
  const [samplesCount, setSamplesCount] = useState(60);
  const [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [loading, setLoading] = useState(false);

  // Rate limit test simulation state
  const [rateLimitTrials, setRateLimitTrials] = useState<{ attempt: number; ceiling: number; delay: number }[]>([]);
  const [isSimulatingRateLimit, setIsSimulatingRateLimit] = useState(false);

  const fetchBenchmark = async (dist = distribution, count = samplesCount) => {
    setLoading(true);
    try {
      const res = await fetch('/api/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ distribution: dist, samples: count })
      });
      const data = await res.json();
      setBenchmark(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, [distribution]);

  const runRateLimitBackoffDemo = () => {
    setIsSimulatingRateLimit(true);
    const trials: { attempt: number; ceiling: number; delay: number }[] = [];
    const base = 2.0;
    const maxCeiling = 64.0;

    for (let attempt = 1; attempt <= 5; attempt++) {
      const ceiling = Math.min(maxCeiling, base * Math.pow(2, attempt));
      // Full jitter: uniform between 0.1 and ceiling
      const delay = +(Math.random() * (ceiling - 0.1) + 0.1).toFixed(2);
      trials.push({ attempt, ceiling, delay });
    }

    setRateLimitTrials(trials);
    setIsSimulatingRateLimit(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-xl font-bold tracking-tight text-white">Human-Like Behavior Engine & Jitter Workbench</h2>
        <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
          <span>Engine: <code className="font-mono text-slate-300">automation_engine/behavior.py</code></span>
          <span aria-hidden="true">·</span>
          <span>Full Jitter Exponential Backoff</span>
          <span aria-hidden="true">·</span>
          <span>Circadian & Cooldown Pacing</span>
        </div>
      </div>

      {/* Model Selector & Live Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 p-4 rounded-lg border border-slate-800">
        <div>
          <label className="text-xs text-slate-400 uppercase font-semibold">Select Jitter Distribution Model</label>
          <div className="flex items-center gap-2 mt-1.5">
            {[
              { id: 'gaussian', label: 'Gaussian (Normal Bell Curve)' },
              { id: 'uniform', label: 'Uniform Random' },
              { id: 'pareto', label: 'Pareto 80/20 (Typing Bursts)' },
            ].map(m => (
              <button
                key={m.id}
                onClick={() => setDistribution(m.id as any)}
                className={`px-3 py-1.5 text-xs rounded-md cursor-pointer transition-colors ${
                  distribution === m.id
                    ? 'bg-emerald-500 text-slate-950 font-bold shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() => fetchBenchmark(distribution, samplesCount)}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Resample Jitter</span>
        </button>
      </div>

      {/* Metric Cards - 1-level flat depth */}
      {benchmark && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
            <span className="text-xs text-slate-400 font-medium">Observed Mean Delay</span>
            <p className="text-2xl font-bold font-mono tabular-nums text-emerald-400 mt-1">
              {benchmark.mean.toFixed(2)}s
            </p>
            <span className="text-[11px] text-slate-500">Base target: 3.50s</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
            <span className="text-xs text-slate-400 font-medium">Observed Min Delay</span>
            <p className="text-2xl font-bold font-mono tabular-nums text-slate-200 mt-1">
              {benchmark.min.toFixed(2)}s
            </p>
            <span className="text-[11px] text-slate-500">Min bound: 1.00s</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
            <span className="text-xs text-slate-400 font-medium">Observed Max Delay</span>
            <p className="text-2xl font-bold font-mono tabular-nums text-slate-200 mt-1">
              {benchmark.max.toFixed(2)}s
            </p>
            <span className="text-[11px] text-slate-500">Max bound: 7.00s</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
            <span className="text-xs text-slate-400 font-medium">Cooldown Cadence</span>
            <p className="text-2xl font-bold font-mono tabular-nums text-amber-400 mt-1">
              15s – 45s
            </p>
            <span className="text-[11px] text-slate-500">Every 4 consecutive actions</span>
          </div>
        </div>
      )}

      {/* Real-time Delay Scatter Visualization */}
      {benchmark && (
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-emerald-400" />
              <span>Sample Delay Distribution ({benchmark.delays.length} Simulated Actions)</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">
              Active Model: {benchmark.distribution.toUpperCase()}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Each bar represents an action delay in seconds. Notice how natural human action pacing avoids constant robotic frequencies.
          </p>

          {/* SVG Bar Chart Visualization */}
          <div className="h-44 flex items-end gap-1.5 pt-6 pb-2 px-2 bg-slate-950/80 rounded border border-slate-800/80 overflow-x-auto">
            {benchmark.delays.map((val, idx) => {
              const maxVal = Math.max(...benchmark.delays, 7);
              const heightPercent = Math.max(12, (val / maxVal) * 100);
              return (
                <div
                  key={idx}
                  className="flex-1 min-w-[6px] group relative flex flex-col items-center justify-end h-full"
                >
                  {/* Tooltip */}
                  <div className="absolute -top-7 hidden group-hover:block bg-slate-800 text-white text-[10px] font-mono px-1.5 py-0.5 rounded shadow whitespace-nowrap z-10">
                    #{idx + 1}: {val.toFixed(2)}s
                  </div>
                  <div
                    style={{ height: `${heightPercent}%` }}
                    className={`w-full rounded-t transition-all ${
                      val > 4.5
                        ? 'bg-amber-400/80 group-hover:bg-amber-400'
                        : val < 2.0
                        ? 'bg-cyan-400/80 group-hover:bg-cyan-400'
                        : 'bg-emerald-400/80 group-hover:bg-emerald-400'
                    }`}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Action #1</span>
            <span>Median Target: 3.50s</span>
            <span>Action #{benchmark.delays.length}</span>
          </div>
        </div>
      )}

      {/* Exponential Backoff & 429 Rate Limit Handler Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Full Jitter Exponential Backoff</span>
            </h3>
            <button
              onClick={runRateLimitBackoffDemo}
              disabled={isSimulatingRateLimit}
              className="px-3 py-1 text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 rounded cursor-pointer transition-colors"
            >
              Simulate 429 Encounter
            </button>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            When target endpoints return <code className="font-mono text-amber-400">HTTP 429 Too Many Requests</code>, naive exponential backoff causes synchronized spikes. PersonaPulse implements AWS/Google's <strong>Full Jitter</strong> formula:
          </p>

          <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
            Sleep = Uniform(0, Min(MaxBackoff, BaseBackoff * 2^attempt))
          </pre>

          {rateLimitTrials.length > 0 ? (
            <div className="space-y-2 pt-2">
              <span className="text-xs text-slate-400 font-medium">Simulated Retry Sequence:</span>
              <div className="space-y-1.5">
                {rateLimitTrials.map(t => (
                  <div
                    key={t.attempt}
                    className="flex items-center justify-between bg-slate-950 px-3 py-2 rounded border border-slate-800 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-amber-400 font-mono font-bold">Attempt {t.attempt}:</span>
                      <span className="text-slate-400">Ceiling: {t.ceiling.toFixed(1)}s</span>
                    </div>
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-slate-500">Selected Delay:</span>
                      <span className="text-emerald-400 font-bold tabular-nums">{t.delay.toFixed(2)}s</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-6 bg-slate-950/40 rounded border border-slate-800/60">
              <p className="text-xs text-slate-500">
                Click "Simulate 429 Encounter" to test backoff calculations across 5 retry attempts.
              </p>
            </div>
          )}
        </div>

        {/* Pacing Rules & Cooldown Architecture */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>Human-Like Behavior Constitution</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-1">
              <span className="text-slate-200 font-semibold">1. Anti-Rapid-Fire Throttling</span>
              <p className="text-slate-400 leading-relaxed">
                Prevents bot-detection signatures by enforcing action-specific multipliers (typing = 0.3x, reading = 1.4x, avatar upload = 1.5x).
              </p>
            </div>

            <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-1">
              <span className="text-slate-200 font-semibold">2. Rest & Fatigue Cycles (Cooldowns)</span>
              <p className="text-slate-400 leading-relaxed">
                Every 4 actions triggers a natural 15s to 45s rest cycle to simulate tab switching, reading notifications, or stepping away.
              </p>
            </div>

            <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-1">
              <span className="text-slate-200 font-semibold">3. Circadian Pace Variation</span>
              <p className="text-slate-400 leading-relaxed">
                Optional toggle adapts action delays based on simulated local timezone (e.g., 35% slower execution during 00:00 - 06:00).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
