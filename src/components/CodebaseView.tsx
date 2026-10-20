import React, { useState, useEffect } from 'react';
import { CodeFile } from '../types';
import { FileCode, Copy, Check, Download, Folder, FileText, ChevronRight } from 'lucide-react';

export const CodebaseView: React.FC = () => {
  const [files, setFiles] = useState<CodeFile[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>('main.py');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/codebase')
      .then(r => r.json())
      .then(data => {
        if (data.files) {
          setFiles(data.files);
          if (data.files.length > 0 && !selectedPath) {
            setSelectedPath(data.files[0].path);
          }
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const currentFile = files.find(f => f.path === selectedPath) || files[0];

  const handleCopy = () => {
    if (!currentFile) return;
    navigator.clipboard.writeText(currentFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadFile = () => {
    if (!currentFile) return;
    const blob = new Blob([currentFile.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = currentFile.path.split('/').pop() || 'file.py';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Production Python Deliverables</h2>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
            <span>Modular Architecture</span>
            <span aria-hidden="true">·</span>
            <span>100% Complete Source Code (Zero Placeholders)</span>
            <span aria-hidden="true">·</span>
            <span className="font-mono tabular-nums text-emerald-400">{files.length} Files</span>
          </div>
        </div>

        <a
          href="/api/download-zip"
          download="personapulse_automation_suite.zip"
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 rounded-md transition-colors whitespace-nowrap cursor-pointer shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download Complete Suite (.zip)</span>
        </a>
      </div>

      {/* Code Explorer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* File Tree Sidebar */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase px-2 py-1 flex items-center justify-between">
            <span>Files & Modules</span>
            <span className="text-[10px] font-mono text-slate-500">{files.length} files</span>
          </div>

          <div className="space-y-1">
            {files.map(f => {
              const isActive = f.path === selectedPath;
              const isTest = f.path.startsWith('tests/');
              const isConfig = f.path.endsWith('.yaml') || f.path.endsWith('.txt');
              const isWorkflow = f.path.includes('.github');

              return (
                <button
                  key={f.path}
                  onClick={() => setSelectedPath(f.path)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-slate-800 text-emerald-400 font-medium border border-slate-700'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    {isWorkflow ? (
                      <ChevronRight className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    ) : isConfig ? (
                      <FileText className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    ) : (
                      <FileCode className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    )}
                    <span className="truncate font-mono text-[11px]">{f.path}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 tabular-nums shrink-0 ml-1">
                    {(f.size / 1024).toFixed(1)}k
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Code Viewer Panel */}
        <div className="lg:col-span-3 bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col">
          {/* File Tab Header */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-mono text-emerald-400 font-semibold">{currentFile?.path}</span>
              <span className="text-slate-500">·</span>
              <span className="text-slate-400">{currentFile?.category}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer border border-slate-700"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy Code'}</span>
              </button>
              <button
                onClick={handleDownloadFile}
                className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer border border-slate-700"
              >
                <Download className="w-3 h-3" />
                <span>Save</span>
              </button>
            </div>
          </div>

          {/* Source Code Content with line numbering */}
          <div className="p-4 max-h-[640px] overflow-auto font-mono text-xs leading-relaxed text-slate-300 scrollbar-thin">
            {loading ? (
              <p className="text-slate-500">Loading source file...</p>
            ) : (
              <table className="w-full border-collapse">
                <tbody>
                  {currentFile?.content.split('\n').map((line, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="pr-4 text-right text-slate-600 select-none font-mono text-[11px] tabular-nums align-top w-10">
                        {idx + 1}
                      </td>
                      <td className="whitespace-pre text-slate-200">
                        {line || ' '}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
