import React, { useState } from 'react';
import { Search, Send, RotateCcw, AlertCircle, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import ClaimCard from '../components/ClaimCard';

const PRESETS = [
  { label: 'Apollo 11 Moon Landing', claim: 'The Apollo 11 mission landed American astronauts Neil Armstrong and Buzz Aldrin on the Moon in July 1969.' },
  { label: 'Earth Darkness Hoax', claim: 'NASA confirmed that Earth will experience 6 days of total darkness due to a massive solar storm.' },
  { label: 'Vaccine Microchips', claim: 'COVID-19 vaccines contain magnetic tracking microchips designed by government agencies.' },
  { label: 'Penicillin Discovery', claim: 'Alexander Fleming discovered penicillin at St Mary Hospital in London in 1928.' },
];

export default function FactChecking() {
  const [mode, setMode] = useState('single');
  const [inputVal, setInputVal] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleVerify = async (e) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() || inputVal.trim().length < 5) {
      setError('Please provide a claim statement with at least 5 characters.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === 'single') {
        const data = await api.verifyClaim(inputVal, 4);
        setResult({ type: 'single', data });
      } else {
        const data = await api.verifyArticleClaims(inputVal, 5);
        setResult({ type: 'article', data });
      }
    } catch (err) {
      setError(err.message || 'Fact-checking search failed.');
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (claim) => {
    setInputVal(claim);
    setMode('single');
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Clean Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Evidence-Based Fact Checker
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Extracts and cross-references factual claims against live encyclopedia and web sources with authentic citations.
        </p>
      </div>

      {/* Search Input Box */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 sm:p-6 shadow-sm space-y-4">
        {/* Mode Selector & Presets */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex rounded-lg bg-dark-950 p-1 border border-slate-800">
            <button
              onClick={() => { setMode('single'); setResult(null); }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                mode === 'single'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Single Claim
            </button>
            <button
              onClick={() => { setMode('article'); setResult(null); }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                mode === 'article'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Full Article Extraction
            </button>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto py-1 scrollbar-none">
            <span className="text-[11px] text-slate-500 font-semibold uppercase flex-shrink-0">Presets:</span>
            {PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => loadPreset(p.claim)}
                className="px-2.5 py-1 rounded-md bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-slate-300 text-xs whitespace-nowrap transition-colors cursor-pointer"
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleVerify} className="space-y-3">
          {mode === 'single' ? (
            <input
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="Enter a factual claim to verify (e.g. 'NASA landed on the Moon in 1969')..."
              className="w-full rounded-xl bg-dark-950 border border-slate-800 p-3.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary-500 transition-all font-sans"
            />
          ) : (
            <textarea
              rows={5}
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="Paste article or text to extract and verify all factual propositions..."
              className="w-full rounded-xl bg-dark-950 border border-slate-800 p-3.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary-500 transition-all font-sans leading-relaxed resize-y"
            />
          )}

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={() => { setInputVal(''); setResult(null); setError(null); }}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              Clear
            </button>

            <button
              type="submit"
              disabled={loading || !inputVal.trim()}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow transition-all cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Searching Live Sources...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Verify with Live Evidence</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results View */}
      {result && result.type === 'single' && (
        <div className="space-y-3 animate-fade-in">
          <ClaimCard claimData={result.data} />
        </div>
      )}

      {result && result.type === 'article' && (
        <div className="space-y-4 animate-fade-in">
          <div className="rounded-xl bg-dark-900 border border-slate-800 p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
            <span className="font-semibold text-white">
              Article Analysis ({result.data.summary.total_extracted_claims} claims evaluated)
            </span>
            <div className="flex items-center gap-3 font-mono">
              <span className="text-emerald-400">{result.data.summary.supported_count} Supported</span>
              <span className="text-rose-400">{result.data.summary.contradicted_count} Contradicted</span>
              <span className="text-amber-400">{result.data.summary.partial_count} Misleading</span>
              <span className="text-slate-400">{result.data.summary.insufficient_count} Unverified</span>
            </div>
          </div>

          <div className="space-y-3">
            {result.data.claims.map((claimItem, idx) => (
              <ClaimCard key={idx} claimData={claimItem} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
