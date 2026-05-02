'use client';

import { useState } from 'react';
import { api, PerplexityResult, ChatMessage } from '@/lib/api';

type Mode = 'search' | 'research' | 'fact-check' | 'chat' | 'market' | 'technical';

const MODES: { id: Mode; label: string; icon: string; description: string }[] = [
  { id: 'search', label: 'Web Search', icon: '🔍', description: 'Fast, grounded web search' },
  { id: 'research', label: 'Deep Research', icon: '📚', description: 'Multi-step expert research' },
  { id: 'fact-check', label: 'Fact Check', icon: '✅', description: 'Verify claims with live sources' },
  { id: 'chat', label: 'Chat', icon: '💬', description: 'Conversational search' },
  { id: 'market', label: 'Market Analysis', icon: '📈', description: 'Structured market intelligence' },
  { id: 'technical', label: 'Technical Research', icon: '⚙️', description: 'Deep technical documentation' },
];

export default function ResearchPage() {
  const [mode, setMode] = useState<Mode>('search');
  const [input, setInput] = useState('');
  const [depth, setDepth] = useState<'standard' | 'deep'>('standard');
  const [model, setModel] = useState('sonar');
  const [result, setResult] = useState<PerplexityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Chat-specific state
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let res: PerplexityResult;

      switch (mode) {
        case 'search':
          res = await api.perplexitySearch(input, model);
          break;
        case 'research':
          res = await api.perplexityResearch(input, depth);
          break;
        case 'fact-check':
          res = await api.perplexityFactCheck(input);
          break;
        case 'chat': {
          const newMessages: ChatMessage[] = [...chatHistory, { role: 'user', content: input }];
          res = await api.perplexityChat(newMessages, model);
          setChatHistory([...newMessages, { role: 'assistant', content: res.content }]);
          break;
        }
        case 'market':
          res = await api.perplexityMarketAnalysis(input);
          break;
        case 'technical':
          res = await api.perplexityTechnicalResearch(input);
          break;
        default:
          throw new Error('Unknown mode');
      }

      setResult(res);
      if (mode !== 'chat') setInput('');
      else setInput('');
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Request failed. Check that PERPLEXITY_API_KEY is configured on the server.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const selectedMode = MODES.find(m => m.id === mode)!;

  const inputPlaceholders: Record<Mode, string> = {
    search: 'Ask anything...',
    research: 'Enter a topic to research in depth...',
    'fact-check': 'Enter a claim to verify...',
    chat: 'Continue the conversation...',
    market: 'Enter a market, sector, or asset (e.g. "AI infrastructure 2025")...',
    technical: 'Enter a technology or concept (e.g. "FastAPI dependency injection")...',
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-5xl mx-auto px-4 py-10 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Perplexity Research</h1>
          <p className="text-gray-400 mt-2">
            Real-time web intelligence powered by Perplexity AI — grounded answers with live citations.
          </p>
        </div>

        {/* Mode selector */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
          {MODES.map(m => (
            <button
              key={m.id}
              onClick={() => { setMode(m.id); setResult(null); setError(null); }}
              className={`p-3 rounded-lg border text-left transition ${
                mode === m.id
                  ? 'border-blue-500 bg-blue-900/30 text-blue-300'
                  : 'border-gray-700 bg-gray-800 hover:border-gray-600 text-gray-300'
              }`}
            >
              <div className="text-xl mb-1">{m.icon}</div>
              <div className="text-xs font-semibold">{m.label}</div>
              <div className="text-xs text-gray-500 mt-0.5 hidden lg:block">{m.description}</div>
            </button>
          ))}
        </div>

        {/* Options row */}
        <div className="flex flex-wrap gap-4 mb-4 items-center">
          {(mode === 'search' || mode === 'chat') && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Model</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              >
                <option value="sonar">sonar (fast)</option>
                <option value="sonar-pro">sonar-pro (accurate)</option>
                <option value="sonar-reasoning">sonar-reasoning</option>
                <option value="sonar-reasoning-pro">sonar-reasoning-pro</option>
              </select>
            </div>
          )}

          {mode === 'research' && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Depth</label>
              <select
                value={depth}
                onChange={e => setDepth(e.target.value as 'standard' | 'deep')}
                className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              >
                <option value="standard">Standard (sonar-pro)</option>
                <option value="deep">Deep (sonar-deep-research)</option>
              </select>
            </div>
          )}

          {mode === 'chat' && chatHistory.length > 0 && (
            <button
              onClick={() => { setChatHistory([]); setResult(null); }}
              className="text-xs text-red-400 hover:text-red-300 border border-red-800 rounded px-2 py-1"
            >
              Clear chat
            </button>
          )}
        </div>

        {/* Chat history */}
        {mode === 'chat' && chatHistory.length > 0 && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 mb-4 space-y-4 max-h-96 overflow-y-auto">
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] px-4 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-blue-700 text-white'
                      : 'bg-gray-700 text-gray-100'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Input form */}
        <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e as any); } }}
            placeholder={inputPlaceholders[mode]}
            rows={mode === 'research' || mode === 'technical' ? 3 : 2}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500 transition"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-semibold transition self-start"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin h-4 w-4 border-b-2 border-white rounded-full inline-block"></span>
                {mode === 'research' && depth === 'deep' ? 'Researching...' : 'Searching...'}
              </span>
            ) : (
              selectedMode.icon
            )}
          </button>
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-900/40 border border-red-700 rounded-lg p-4 mb-6 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 space-y-4">

            {/* Meta bar */}
            <div className="flex items-center justify-between text-xs text-gray-500 border-b border-gray-700 pb-3">
              <span>Model: <span className="text-gray-300">{result.model}</span></span>
              {result.usage?.completion_tokens !== undefined && (
                <span>{result.usage.completion_tokens} tokens</span>
              )}
            </div>

            {/* Content */}
            <div className="prose prose-invert prose-sm max-w-none text-gray-100 whitespace-pre-wrap leading-relaxed">
              {result.content}
            </div>

            {/* Citations */}
            {result.citations && result.citations.length > 0 && (
              <div className="border-t border-gray-700 pt-4">
                <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">
                  Sources
                </p>
                <ol className="space-y-1">
                  {result.citations.map((url, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs">
                      <span className="text-gray-600 w-4 shrink-0">{i + 1}.</span>
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 break-all transition"
                      >
                        {url}
                      </a>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
