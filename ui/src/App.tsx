import { useState, useEffect } from 'react';
import api, { type Session } from './lib/api';
import Chat from './components/Chat';
import WikiExplorer from './components/WikiExplorer';
import LogExplorer from './components/LogExplorer';
import Sidebar from './components/Sidebar';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'wiki' | 'logs'>('chat');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [runningMemoryOperation, setRunningMemoryOperation] = useState<string | null>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await api.get('/sessions/');
      setSessions(res.data);
      if (res.data.length > 0 && !selectedSessionId) {
        setSelectedSessionId(res.data[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch sessions", err);
    }
  };

  const handleCreateSession = async (query?: string) => {
    try {
      const name = query?.trim() || "New session";
      const res = await api.post('/sessions/', { query: name });
      setSessions([...sessions, res.data]);
      setSelectedSessionId(res.data.id);
      setActiveTab('chat');
    } catch (err) {
      console.error("Failed to create session", err);
    }
  };

  const handleRenameSession = async (id: string, query: string) => {
    const name = query.trim();
    if (!name) return;
    try {
      const res = await api.patch(`/sessions/${id}`, { query: name });
      setSessions(prev => prev.map(s => s.id === id ? { ...s, query: res.data.query } : s));
    } catch (err) {
      console.error("Failed to rename session", err);
    }
  };

  const handleDream = async () => {
    await handleMemoryOperation('dream');
  };

  const handleMemoryOperation = async (
    operation: 'flush-current' | 'flush-idle' | 'flush-all' | 'reconsolidate-current' | 'dream' | 'decay' | 'clear-memory'
  ) => {
    try {
      if (operation === 'clear-memory') {
        const confirmed = window.confirm(
          'Delete all wiki pages and episodic logs? This is intended for development and cannot be undone.'
        );
        if (!confirmed) return;
      }
      setRunningMemoryOperation(operation);
      let res;
      if (operation === 'flush-current') {
        if (!selectedSessionId) {
          alert('Select a chat session first.');
          return;
        }
        res = await api.post('/memory/episodes/flush', { session_id: selectedSessionId });
      } else if (operation === 'flush-idle') {
        res = await api.post('/memory/episodes/flush-idle', { idle_minutes: 20, max_turns: 25 });
      } else if (operation === 'flush-all') {
        res = await api.post('/memory/episodes/flush-all');
      } else if (operation === 'reconsolidate-current') {
        if (!selectedSessionId) {
          alert('Select a chat session first.');
          return;
        }
        res = await api.post('/memory/reconsolidation/resolve', { session_id: selectedSessionId });
      } else if (operation === 'decay') {
        res = await api.post('/memory/decay');
      } else if (operation === 'clear-memory') {
        res = await api.post('/memory/dev/clear');
      } else {
        res = await api.post('/memory/dream');
      }
      alert(`${operation.replaceAll('-', ' ')} complete:\n${JSON.stringify(res.data, null, 2)}`);
    } catch (err) {
      console.error("Memory operation failed", err);
      alert('Memory operation failed. Check the console and backend logs.');
    } finally {
      setRunningMemoryOperation(null);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onDream={handleDream}
        onMemoryOperation={handleMemoryOperation}
        hasSelectedSession={Boolean(selectedSessionId)}
        runningMemoryOperation={runningMemoryOperation}
      />
      
      <main className="flex-1 flex flex-col min-w-0 h-full">
        {activeTab === 'chat' && (
          <Chat 
            sessions={sessions}
            selectedId={selectedSessionId}
            onSelect={setSelectedSessionId}
            onCreate={handleCreateSession}
            onRename={handleRenameSession}
          />
        )}
        {activeTab === 'wiki' && <WikiExplorer />}
        {activeTab === 'logs' && <LogExplorer />}
      </main>
    </div>
  );
}

export default App;
