import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Search, Tag, Clock, ShieldCheck, ChevronRight, Book, History as HistoryIcon } from 'lucide-react';
import api, { type WikiPage } from '../lib/api';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function WikiExplorer() {
  const [pages, setPages] = useState<WikiPage[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [pageData, setPageData] = useState<WikiPage | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchPages();
  }, []);

  useEffect(() => {
    if (selectedSlug) {
      fetchPage(selectedSlug);
    }
  }, [selectedSlug]);

  const fetchPages = async () => {
    try {
      const res = await api.get('/memory/wiki');
      setPages(res.data);
    } catch (err) {
      console.error("Failed to fetch wiki pages", err);
    }
  };

  const fetchPage = async (slug: string) => {
    try {
      const res = await api.get(`/memory/wiki/${slug}`);
      setPageData(res.data);
    } catch (err) {
      console.error("Failed to fetch page", err);
    }
  };

  const filteredPages = pages.filter(p => 
    p.title.toLowerCase().includes(search.toLowerCase()) || 
    p.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex h-full min-w-0">
      {/* Page List */}
      <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search wiki..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-100 border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredPages.map(p => (
            <button
              key={p.slug}
              onClick={() => setSelectedSlug(p.slug)}
              className={cn(
                "w-full text-left p-3 rounded-xl transition-all group",
                selectedSlug === p.slug ? "bg-indigo-50 border-indigo-100" : "hover:bg-slate-50"
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={cn("text-sm font-semibold", selectedSlug === p.slug ? "text-indigo-700" : "text-slate-700")}>
                  {p.title}
                </span>
                <ChevronRight size={14} className={cn("transition-transform", selectedSlug === p.slug ? "text-indigo-500 translate-x-0" : "text-slate-300 -translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100")} />
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 bg-slate-200 rounded-full overflow-hidden">
                  <div 
                    className={cn("h-full rounded-full transition-all duration-500", p.confidence > 0.7 ? "bg-emerald-400" : p.confidence > 0.4 ? "bg-amber-400" : "bg-rose-400")} 
                    style={{ width: `${p.confidence * 100}%` }} 
                  />
                </div>
                <span className="text-[10px] font-medium text-slate-400">{(p.confidence * 100).toFixed(0)}%</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Page Content */}
      <div className="flex-1 bg-white overflow-y-auto">
        {pageData ? (
          <div className="max-w-4xl mx-auto p-12">
            <header className="mb-12">
              <div className="flex items-center gap-2 mb-4 text-xs font-bold text-indigo-600 uppercase tracking-widest">
                <Book size={14} /> Wiki Page
              </div>
              <h1 className="text-4xl font-extrabold text-slate-900 mb-6 tracking-tight leading-tight">
                {pageData.title}
              </h1>
              
              <div className="flex flex-wrap gap-4 items-center text-sm text-slate-500">
                <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full">
                  <ShieldCheck size={16} className="text-indigo-500" />
                  <span className="font-medium">v{pageData.version}</span>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full">
                  <Clock size={16} />
                  <span>Last updated {new Date().toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  {pageData.tags.map(t => (
                    <span key={t} className="flex items-center gap-1 bg-indigo-50 text-indigo-600 px-2 py-1 rounded text-[11px] font-bold">
                      <Tag size={12} /> {t}
                    </span>
                  ))}
                </div>
              </div>
            </header>

            <div className="prose prose-slate prose-indigo max-w-none mb-16">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{pageData.content || ''}</ReactMarkdown>
            </div>

            {pageData.update_log && pageData.update_log.length > 0 && (
              <section className="border-t border-slate-100 pt-12">
                <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <HistoryIcon size={18} className="text-slate-400" /> Update Log
                </h3>
                <div className="space-y-4">
                  {pageData.update_log.map((log, i) => (
                    <div key={i} className="flex gap-4 group">
                      <div className="flex flex-col items-center">
                        <div className="w-2.5 h-2.5 rounded-full border-2 border-indigo-500 bg-white z-10" />
                        {i !== pageData.update_log!.length - 1 && <div className="w-0.5 flex-1 bg-slate-100 my-1" />}
                      </div>
                      <div className="pb-6">
                        <div className="text-[11px] font-bold text-indigo-500 uppercase tracking-wide mb-1">
                          Version {log.version} • {new Date(log.date).toLocaleString()}
                        </div>
                        <p className="text-sm text-slate-600 leading-relaxed">{log.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-400">
            Select a page to view its contents.
          </div>
        )}
      </div>
    </div>
  );
}
