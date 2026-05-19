import { Archive, Book, BrainCircuit, FileText, Loader2, MessageSquare, Moon, RefreshCw, Save, Sparkles, Trash2 } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SidebarProps {
  activeTab: 'chat' | 'wiki' | 'logs';
  setActiveTab: (tab: 'chat' | 'wiki' | 'logs') => void;
  onDream: () => void;
  onMemoryOperation: (
    operation: 'flush-current' | 'flush-idle' | 'flush-all' | 'reconsolidate-current' | 'dream' | 'decay' | 'clear-memory'
  ) => void;
  hasSelectedSession: boolean;
  runningMemoryOperation: string | null;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  onDream,
  onMemoryOperation,
  hasSelectedSession,
  runningMemoryOperation,
}: SidebarProps) {
  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'wiki', label: 'Wiki', icon: Book },
    { id: 'logs', label: 'Logs', icon: FileText },
  ] as const;

  const memoryOps = [
    {
      id: 'flush-current',
      label: 'Flush Current',
      icon: Save,
      needsSession: true,
      tooltip: 'Encode the selected chat episode into episodic memory.',
    },
    {
      id: 'flush-idle',
      label: 'Flush Idle',
      icon: RefreshCw,
      needsSession: false,
      tooltip: 'Encode episodes that are idle or have grown large.',
    },
    {
      id: 'flush-all',
      label: 'Flush All',
      icon: Archive,
      needsSession: false,
      tooltip: 'Encode every active chat episode now.',
    },
    {
      id: 'reconsolidate-current',
      label: 'Resolve Current',
      icon: BrainCircuit,
      needsSession: true,
      tooltip: 'Apply pending reconsolidation updates for the selected chat.',
    },
    {
      id: 'decay',
      label: 'Decay Pass',
      icon: RefreshCw,
      needsSession: false,
      tooltip: 'Recompute decay scores and archive weak memories.',
    },
    {
      id: 'clear-memory',
      label: 'Clear Memory',
      icon: Trash2,
      needsSession: false,
      tooltip: 'Delete all wiki pages and episodic logs for development.',
    },
  ] as const;

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center text-white">
          <Sparkles size={20} />
        </div>
        <h1 className="text-xl font-bold text-white tracking-tight">Mycelium</h1>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              activeTab === tab.id 
                ? "bg-slate-800 text-white" 
                : "hover:bg-slate-800 hover:text-white"
            )}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="p-4 mt-auto space-y-2 border-t border-slate-800">
        <div className="px-1 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Memory Operations
        </div>
        {memoryOps.map((op) => {
          const Icon = op.icon;
          const isRunning = runningMemoryOperation === op.id;
          const anyRunning = runningMemoryOperation !== null;
          const disabled = (op.needsSession && !hasSelectedSession) || anyRunning;
          return (
            <button
              key={op.id}
              onClick={() => onMemoryOperation(op.id)}
              disabled={disabled}
              title={disabled ? 'Select a chat session first.' : op.tooltip}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md text-xs font-semibold transition-colors",
                disabled
                  ? "text-slate-600 cursor-not-allowed"
                  : op.id === 'clear-memory'
                    ? "text-rose-300 hover:bg-rose-950/50 hover:text-rose-100"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              {isRunning ? <Loader2 size={15} className="animate-spin" /> : <Icon size={15} />}
              {op.label}
            </button>
          );
        })}
        <button
          onClick={onDream}
          disabled={runningMemoryOperation !== null}
          title="Consolidate encoded episodic logs into wiki memory."
          className={cn(
            "w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold transition-all shadow-lg shadow-indigo-500/20 active:scale-95",
            runningMemoryOperation
              ? "bg-indigo-900 text-indigo-200 cursor-wait"
              : "bg-indigo-600 hover:bg-indigo-700 text-white"
          )}
        >
          {runningMemoryOperation === 'dream' ? <Loader2 size={18} className="animate-spin" /> : <Moon size={18} />}
          Dream Pass
        </button>
      </div>
    </aside>
  );
}
