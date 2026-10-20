import React, { useState } from 'react';
import { Profile } from '../types';
import { Search, Download, UserPlus, Eye, CheckCircle2, Clock, Globe } from 'lucide-react';

interface ProfilesViewProps {
  profiles: Profile[];
  loading: boolean;
  onRefresh: () => void;
  onGenerate: (count: number, downloadAvatars: boolean) => Promise<void>;
}

export const ProfilesView: React.FC<ProfilesViewProps> = ({
  profiles,
  loading,
  onRefresh,
  onGenerate
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPersona, setSelectedPersona] = useState<string>('all');
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateCount, setGenerateCount] = useState(5);
  const [downloadAvatars, setDownloadAvatars] = useState(false);
  const [showGenModal, setShowGenModal] = useState(false);

  const personas = ['all', 'tech_enthusiast', 'creative_designer', 'digital_nomad', 'coffee_devotee', 'fitness_runner', 'open_source_builder', 'photographer'];

  const filtered = profiles.filter(p => {
    const matchesSearch =
      p.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.bio.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.location.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesPersona = selectedPersona === 'all' || p.persona === selectedPersona;
    return matchesSearch && matchesPersona;
  });

  const handleStartGenerate = async () => {
    setIsGenerating(true);
    try {
      await onGenerate(generateCount, downloadAvatars);
      setShowGenModal(false);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportCSV = () => {
    const headers = ['id', 'full_name', 'username', 'email', 'persona', 'location', 'timezone', 'status', 'created_at', 'bio'];
    const rows = filtered.map(p => [
      p.id,
      `"${p.full_name}"`,
      p.username,
      p.email,
      p.persona,
      `"${p.location}"`,
      p.timezone,
      p.status,
      p.created_at,
      `"${p.bio.replace(/"/g, '""')}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `personapulse_accounts_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top action & filter bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Generated Profiles Repository</h2>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
            <span>Storage: <code className="font-mono text-slate-300">data/accounts.json</code></span>
            <span aria-hidden="true">·</span>
            <span className="font-mono tabular-nums text-emerald-400">{profiles.length} total profiles</span>
            <span aria-hidden="true">·</span>
            <span>Atomic JSON Swap</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-md transition-colors whitespace-nowrap cursor-pointer border border-slate-700"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setShowGenModal(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-950 bg-emerald-400 hover:bg-emerald-300 rounded-md transition-colors whitespace-nowrap cursor-pointer shadow-sm font-semibold"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Generate Profiles</span>
          </button>
        </div>
      </div>

      {/* Search & Persona Segmented Filter */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, handle, bio keywords, location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-md pl-9 pr-3 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-thin">
          {personas.map(p => (
            <button
              key={p}
              onClick={() => setSelectedPersona(p)}
              className={`px-2.5 py-1 text-xs rounded-md whitespace-nowrap cursor-pointer transition-colors ${
                selectedPersona === p
                  ? 'bg-slate-800 text-emerald-400 font-medium border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {p === 'all' ? 'All Personas' : p.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* High-density Profiles Grid / Table */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/50 rounded-lg border border-slate-800">
          <p className="text-slate-400 text-sm">No profiles found matching your search criteria.</p>
          <button
            onClick={() => setShowGenModal(true)}
            className="mt-3 px-3 py-1.5 text-xs font-medium text-emerald-400 hover:text-emerald-300 cursor-pointer underline"
          >
            Generate new synthetic profiles now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(profile => (
            <div
              key={profile.id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors rounded-lg p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start gap-3">
                  {/* Avatar thumbnail */}
                  <div className="w-12 h-12 rounded-full overflow-hidden bg-slate-800 shrink-0 border border-slate-700">
                    <img
                      src={profile.avatar_url}
                      alt={profile.full_name}
                      referrerPolicy="no-referrer"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback SVG icon if external image url is blocked
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-bold text-white truncate">{profile.full_name}</h3>
                    <p className="text-xs text-slate-400 font-mono truncate">@{profile.username}</p>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                      <span>{profile.persona.replace('_', ' ')}</span>
                      <span aria-hidden="true">·</span>
                      <span className="truncate">{profile.location}</span>
                    </div>
                  </div>
                </div>

                {/* Natural Bio */}
                <p className="text-xs text-slate-300 mt-3 line-clamp-3 leading-relaxed bg-slate-950/50 p-2.5 rounded border border-slate-800/60 font-sans">
                  {profile.bio}
                </p>
              </div>

              {/* Card Footer with clean unboxed metadata */}
              <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800 text-xs">
                <div className="flex items-center gap-2 text-slate-400">
                  <span className={`font-mono text-[11px] ${
                    profile.status === 'verified' ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {profile.status}
                  </span>
                  <span aria-hidden="true">·</span>
                  <span className="font-mono tabular-nums text-[11px]">
                    TZ: {profile.timezone.split('/')[1] || profile.timezone}
                  </span>
                </div>

                <button
                  onClick={() => setSelectedProfile(profile)}
                  className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors cursor-pointer text-xs"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Profile Detail Slideover / Modal */}
      {selectedProfile && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-lg max-w-xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <img
                  src={selectedProfile.avatar_url}
                  alt={selectedProfile.full_name}
                  referrerPolicy="no-referrer"
                  className="w-14 h-14 rounded-full object-cover border border-slate-700"
                />
                <div>
                  <h3 className="text-lg font-bold text-white">{selectedProfile.full_name}</h3>
                  <p className="text-sm font-mono text-emerald-400">@{selectedProfile.username}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedProfile(null)}
                className="text-slate-400 hover:text-white text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-400 uppercase font-semibold">Casual Natural Bio</label>
                <p className="text-slate-200 mt-1 bg-slate-950 p-3 rounded border border-slate-800 leading-relaxed">
                  {selectedProfile.bio}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-400">Email Address:</span>
                  <p className="font-mono text-slate-200 mt-0.5 truncate">{selectedProfile.email}</p>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-400">Location & Timezone:</span>
                  <p className="text-slate-200 mt-0.5">{selectedProfile.location} ({selectedProfile.timezone})</p>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-400">Persona Profile:</span>
                  <p className="text-slate-200 mt-0.5">{selectedProfile.persona}</p>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-400">Profile ID:</span>
                  <p className="font-mono text-slate-200 mt-0.5 truncate">{selectedProfile.id}</p>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 uppercase font-semibold">JSON Configuration Representation</label>
                <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto max-h-48 mt-1">
                  {JSON.stringify(selectedProfile, null, 2)}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setSelectedProfile(null)}
                className="px-4 py-1.5 text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 rounded cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generation Modal */}
      {showGenModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-lg max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Generate Profiles (Profile Metadata Generator)</h3>
            <p className="text-xs text-slate-400">
              Synthesizes realistic human identities with casual text bios and public avatar placeholders, saving directly to <code className="font-mono text-slate-300">accounts.json</code>.
            </p>

            <div className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-300 block mb-1">Batch Count (1 - 50)</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={generateCount}
                  onChange={(e) => setGenerateCount(parseInt(e.target.value, 10) || 1)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-slate-200 font-mono text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="downloadAvatarsCheck"
                  checked={downloadAvatars}
                  onChange={(e) => setDownloadAvatars(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-0 cursor-pointer"
                />
                <label htmlFor="downloadAvatarsCheck" className="text-xs text-slate-300 cursor-pointer">
                  Download & verify image headers (saves to <code className="font-mono">data/avatars/</code>)
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowGenModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleStartGenerate}
                disabled={isGenerating}
                className="px-4 py-1.5 text-xs font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 rounded cursor-pointer disabled:opacity-50"
              >
                {isGenerating ? 'Generating...' : 'Generate Batch'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
