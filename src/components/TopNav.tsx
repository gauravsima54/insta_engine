import React from 'react';
import { Play } from 'lucide-react';

interface TopNavProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  onOpenQuickSim: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  currentTab,
  onSelectTab,
  onOpenQuickSim
}) => {
  const tabs = [
    { id: 'profiles', label: 'Profiles' },
    { id: 'behavior', label: 'Behavior Engine' },
    { id: 'scheduler', label: 'Task Scheduler' },
    { id: 'codebase', label: 'Python Deliverables' },
    { id: 'cloud', label: 'Cloud Runner' },
  ];

  return (
    <header className="flex items-center justify-between gap-8 px-6 py-3.5 bg-slate-900 border-b border-slate-800 text-slate-100 sticky top-0 z-40">
      {/* Zone 1: Single text element wordmark */}
      <div className="flex items-center gap-3 shrink-0">
        <a
          href="#home"
          onClick={(e) => { e.preventDefault(); onSelectTab('profiles'); }}
          className="text-lg font-bold tracking-tight text-white hover:text-slate-200 transition-colors whitespace-nowrap shrink-0"
        >
          PersonaPulse
        </a>
        <span className="text-xs text-slate-500 hidden sm:inline">· Automation Suite</span>
      </div>

      {/* Zone 2: 4–5 clean single-line text navigation links */}
      <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            className={`whitespace-nowrap shrink-0 transition-colors py-1 cursor-pointer ${
              currentTab === tab.id
                ? 'text-white border-b-2 border-emerald-500 font-semibold'
                : 'hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Zone 3: 1 primary action */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={onOpenQuickSim}
          className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-slate-950 bg-emerald-400 hover:bg-emerald-300 rounded-md transition-colors whitespace-nowrap shrink-0 shadow-sm cursor-pointer"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Launch Simulation</span>
        </button>
      </div>
    </header>
  );
};
