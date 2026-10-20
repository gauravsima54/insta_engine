import React, { useState, useEffect } from 'react';
import { TopNav } from './components/TopNav';
import { ProfilesView } from './components/ProfilesView';
import { BehaviorView } from './components/BehaviorView';
import { SchedulerView } from './components/SchedulerView';
import { CodebaseView } from './components/CodebaseView';
import { CloudRunnerView } from './components/CloudRunnerView';
import { Profile } from './types';

export default function App() {
  const [currentTab, setCurrentTab] = useState<string>('profiles');
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/profiles');
      const data = await res.json();
      if (data.profiles) {
        setProfiles(data.profiles);
      }
    } catch (err) {
      console.error('Failed to fetch profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  const showNotice = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3500);
  };

  const handleGenerateProfiles = async (count: number, downloadAvatars: boolean) => {
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count, downloadAvatars })
      });
      const result = await res.json();
      if (result.data?.profiles) {
        setProfiles(result.data.profiles);
      } else {
        await fetchProfiles();
      }
      showNotice(`Successfully synthesized ${count} new profiles to accounts.json`);
    } catch (err: any) {
      showNotice('Generation failed: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 flex flex-col font-sans">
      {/* Top Bar adhering to Top Bar Contract */}
      <TopNav
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onOpenQuickSim={() => setCurrentTab('scheduler')}
      />

      {/* Ephemeral Notification Toast */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-800 text-emerald-400 text-xs font-mono py-2.5 px-4 rounded-md border border-emerald-500/40 shadow-xl flex items-center gap-2">
          <span>{notification}</span>
        </div>
      )}

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'profiles' && (
          <ProfilesView
            profiles={profiles}
            loading={loading}
            onRefresh={fetchProfiles}
            onGenerate={handleGenerateProfiles}
          />
        )}

        {currentTab === 'behavior' && <BehaviorView />}

        {currentTab === 'scheduler' && (
          <SchedulerView onSimulationComplete={fetchProfiles} />
        )}

        {currentTab === 'codebase' && <CodebaseView />}

        {currentTab === 'cloud' && <CloudRunnerView />}
      </main>

      {/* Clean quiet footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 px-6 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-400">PersonaPulse Automation Architecture</span>
          <span aria-hidden="true">·</span>
          <span>Python 3.10+ Headless Engine</span>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>accounts.json: {profiles.length} records</span>
          <span aria-hidden="true">·</span>
          <a
            href="/api/download-zip"
            download="personapulse_automation_suite.zip"
            className="hover:text-emerald-400 transition-colors"
          >
            Export ZIP
          </a>
        </div>
      </footer>
    </div>
  );
}
