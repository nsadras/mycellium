import { BrainCircuit, Loader2, Moon, Radio, Sparkles, Waves } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { AssistantStatus } from '../lib/assistantStatus';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const activityCopy: Record<AssistantStatus['activity'], { label: string; detail: string }> = {
  idle: { label: 'Idle', detail: 'Ready' },
  listening: { label: 'Listening', detail: 'Composing' },
  thinking: { label: 'Thinking', detail: 'Calling model' },
  tool_calling: { label: 'Searching', detail: 'Using tools' },
  responding: { label: 'Responding', detail: 'Writing' },
  flushing: { label: 'Flushing', detail: 'Encoding episode' },
  dreaming: { label: 'Dreaming', detail: 'Consolidating logs' },
  decaying: { label: 'Decaying', detail: 'Updating scores' },
  reconsolidating: { label: 'Resolving', detail: 'Updating memory' },
  error: { label: 'Error', detail: 'Check logs' },
};

function ActivityIcon({ activity }: { activity: AssistantStatus['activity'] }) {
  if (activity === 'dreaming') return <Moon size={22} />;
  if (activity === 'flushing') return <Waves size={22} />;
  if (activity === 'decaying') return <Radio size={22} />;
  if (activity === 'reconsolidating') return <BrainCircuit size={22} />;
  if (activity === 'thinking' || activity === 'tool_calling' || activity === 'responding') {
    return <Loader2 size={22} className="animate-spin" />;
  }
  return <Sparkles size={22} />;
}

export default function Avatar({ status }: { status: AssistantStatus }) {
  const copy = activityCopy[status.activity];
  const label = status.label ?? copy.label;
  const detail = status.detail ?? copy.detail;
  const active = status.activity !== 'idle' && status.activity !== 'error';

  return (
    <div
      className={cn(
        "mx-4 mb-4 rounded-lg border p-3 transition-colors",
        status.activity === 'error'
          ? "border-rose-800 bg-rose-950/50"
          : active
            ? "border-indigo-700 bg-slate-800"
            : "border-slate-800 bg-slate-950/40"
      )}
      aria-live="polite"
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "relative flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-white",
            status.activity === 'error'
              ? "bg-rose-600"
              : status.activity === 'dreaming'
                ? "bg-violet-600"
                : status.activity === 'flushing'
                  ? "bg-cyan-600"
                  : active
                    ? "bg-indigo-600"
                    : "bg-slate-700"
          )}
        >
          {active && (
            <span
              className={cn(
                "absolute inset-0 rounded-lg opacity-60",
                status.activity === 'listening' ? "animate-ping bg-emerald-400" : "animate-pulse bg-white"
              )}
            />
          )}
          <span className="relative">
            <ActivityIcon activity={status.activity} />
          </span>
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-white">{label}</div>
          <div className="truncate text-xs text-slate-400">{detail}</div>
        </div>
      </div>
    </div>
  );
}
