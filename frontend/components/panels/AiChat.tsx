'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Bot, Send, User } from 'lucide-react';

interface TradeReport {
  ticker: string;
  side: string;
  quantity: number;
  status: 'success' | 'failed';
  detail?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  payload?: {
    reports?: TradeReport[];
  };
}

export function AiChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${API_URL}/api/chat/history?limit=50`);
        const data = await res.json();
        setMessages(data);
      } catch (e) {
        console.error('Failed to load chat history', e);
      }
    };
    fetchHistory();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply,
        payload: { reports: data.reports }
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'System Error: Could not connect to AI Copilot.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <aside className="w-full min-w-0 h-full bg-panel rounded-xl border border-line flex flex-col gap-4 p-4 overflow-hidden shadow-xl">
      <div className="flex items-center gap-2 flex-shrink-0">
        <Bot className="w-5 h-5 text-accent" />
        <h2 className="text-sm font-bold text-ink/60 uppercase tracking-wider">NeonPulse Copilot</h2>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar"
      >
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-ink/40 text-sm text-center">
            How can I assist you with your portfolio today?
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`max-w-[85%] rounded p-3 text-sm ${
              msg.role === 'user' ? 'bg-raised border border-line text-ink' : 'bg-raised border border-line text-ink'
            }`}>
              <div className="flex items-center gap-2 mb-1 text-xs opacity-50 font-bold uppercase">
                {msg.role === 'user' ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                {msg.role}
              </div>
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>

            {/* Trade Cards */}
            {msg.payload?.reports && msg.payload.reports.length > 0 && (
              <div className="flex flex-col gap-2 mt-2 w-full max-w-[85%]">
                {msg.payload.reports.map((r, i) => (
                  <div key={i} className={`p-2 rounded border text-xs flex justify-between items-center ${
                    r.status === 'success' ? 'bg-up/10 border-up/30 text-up' : 'bg-down/10 border-down/30 text-down'
                  }`}>
                    <div className="flex gap-2 items-center">
                      <span className="font-bold uppercase">{r.side}</span>
                      <span className="font-mono">{r.quantity} {r.ticker}</span>
                    </div>
                    <div className="uppercase font-bold text-[10px]">
                      {r.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-ink/40 text-sm p-2">
            <Bot className="w-4 h-4 animate-pulse text-accent" />
            <span className="animate-pulse">Thinking...</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 flex-shrink-0">
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask NeonPulse to analyze or trade..."
            className="w-full min-w-0 bg-raised border border-line rounded px-3 py-2 text-sm text-black font-bold placeholder:text-black/60 focus:outline-none focus:border-accent disabled:opacity-50 pr-12"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-ink/40 border border-line rounded px-1.5 py-0.5 pointer-events-none">
            ⌘K
          </div>
        </div>
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-accent text-black p-2 rounded hover:bg-accent/90 disabled:opacity-50 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </aside>
  );
}
