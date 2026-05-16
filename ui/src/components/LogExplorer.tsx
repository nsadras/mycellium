import { useState, useEffect } from 'react';
import api from '../lib/api';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { FileText, Calendar } from 'lucide-react';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function LogExplorer() {
  const [logs, setLogs] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [content, setContent] = useState('');

  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
    if (selectedFile) {
      fetchLogContent(selectedFile);
    }
  }, [selectedFile]);

  const fetchLogs = async () => {
    try {
      const res = await api.get('/memory/logs');
      setLogs(res.data);
      if (res.data.length > 0 && !selectedFile) {
        setSelectedFile(res.data[0]);
      }
    } catch (err) {
      console.error("Failed to fetch logs", err);
    }
  };

  const fetchLogContent = async (filename: string) => {
    try {
      const res = await api.get(`/memory/logs/${filename}`);
      setContent(res.data.content);
    } catch (err) {
      console.error("Failed to fetch log content", err);
    }
  };

  return (
    <div className="flex h-full min-w-0">
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-700 flex items-center gap-2">
            <Calendar size={16} /> Daily Logs
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {logs.map((f) => (
            <button
              key={f}
              onClick={() => setSelectedFile(f)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center gap-2",
                selectedFile === f ? "bg-indigo-50 text-indigo-700 font-medium" : "hover:bg-slate-50 text-slate-600"
              )}
            >
              <FileText size={14} />
              {f.replace('.md', '')}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-0 bg-slate-900 overflow-hidden flex flex-col">
        {selectedFile ? (
          <div className="flex-1 min-h-0 flex flex-col">
            <div className="shrink-0 bg-slate-800 px-4 py-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
              <span>{selectedFile}</span>
              <span>EPISODIC LOG</span>
            </div>
            <pre className="flex-1 min-h-0 overflow-auto p-6 text-indigo-300 font-mono text-sm leading-relaxed whitespace-pre-wrap">
              {content}
            </pre>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-600">
            No logs available.
          </div>
        )}
      </div>
    </div>
  );
}
