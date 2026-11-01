import React, { useState, useRef } from 'react';
import { Youtube, Play, RotateCcw, AlertTriangle, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../services/api';
import ClaimCard from '../components/ClaimCard';

const SAMPLE_VIDEOS = [
  {
    label: 'Science Fact-Check Short',
    url: 'https://www.youtube.com/shorts/aUyVATJqEoQ',
    transcript: `[00:00] Did you know that lightning actually strikes the Earth over 100 times every single second?
[00:08] NASA scientists have confirmed that extreme weather events produce massive electrical storms.
[00:16] But contrary to viral rumors on social media, cell phones do not attract lightning during outdoor storms.
[00:25] NOAA meteorologists have repeatedly verified that wearing metal or carrying smartphones has zero measurable effect on lightning strike probability.`
  },
  {
    label: 'Standard YouTube Video',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    transcript: `[00:00] We're no strangers to love. You know the rules and so do I.
[00:15] A full commitment's what I'm thinking of. You wouldn't get this from any other guy.`
  }
];

export default function VideoAnalysis() {
  const [url, setUrl] = useState('https://www.youtube.com/shorts/aUyVATJqEoQ');
  const [manualTranscript, setManualTranscript] = useState('');
  const [showManual, setShowManual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const iframeRef = useRef(null);

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!url.trim()) {
      setError('Please provide a valid YouTube video or Shorts link.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.analyzeVideo(url, manualTranscript.trim() || null, 6);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze video transcript.');
      setShowManual(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSeek = (seconds) => {
    if (iframeRef.current) {
      iframeRef.current.contentWindow.postMessage(
        JSON.stringify({ event: 'command', func: 'seekTo', args: [seconds, true] }),
        '*'
      );
    }
  };

  const loadPreset = (s) => {
    setUrl(s.url);
    setManualTranscript(s.transcript);
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Clean Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Video & Shorts Fact-Checker
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Segments YouTube captions, extracts factual claims, and verifies assertions with timestamped playback seeking.
        </p>
      </div>

      {/* Input Card */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 sm:p-6 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Sample Links:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {SAMPLE_VIDEOS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => loadPreset(s)}
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleAnalyze} className="space-y-3">
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste YouTube or Shorts link (e.g. https://www.youtube.com/shorts/aUyVATJqEoQ)..."
              className="w-full rounded-xl bg-dark-950 border border-slate-800 p-3.5 pl-10 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-rose-500 transition-all font-sans"
            />
            <Youtube className="w-4 h-4 text-rose-400 absolute left-3.5 top-4 pointer-events-none" />
          </div>

          {/* Manual Transcript Fallback Accordion */}
          <div className="border border-slate-800/80 rounded-xl overflow-hidden bg-dark-950/50">
            <button
              type="button"
              onClick={() => setShowManual(!showManual)}
              className="w-full px-3.5 py-2 flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <span className="flex items-center gap-1.5 font-medium">
                <FileText className="w-3.5 h-3.5 text-primary-400" />
                Manual Transcript Fallback (in case captions are disabled)
              </span>
              {showManual ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showManual && (
              <div className="p-3 pt-0 border-t border-slate-800/60 space-y-1.5">
                <textarea
                  rows={3}
                  value={manualTranscript}
                  onChange={(e) => setManualTranscript(e.target.value)}
                  placeholder="[00:10] Spoken claim text..."
                  className="w-full rounded-lg bg-dark-950 border border-slate-800 p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none font-mono"
                />
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={() => { setUrl(''); setManualTranscript(''); setResult(null); setError(null); }}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              Clear
            </button>

            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-semibold shadow transition-all cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Analyzing Captions...</span>
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 fill-current" />
                  <span>Analyze Video</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Analysis View */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Video Player & Summary Header */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
            <div className="md:col-span-7 rounded-2xl bg-dark-900 border border-slate-800 p-3.5">
              <div className="aspect-video w-full rounded-xl overflow-hidden bg-black">
                {result.embed_url ? (
                  <iframe
                    ref={iframeRef}
                    src={result.embed_url}
                    title="YouTube Player"
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-500 text-xs">
                    Embed unavailable
                  </div>
                )}
              </div>
            </div>

            <div className="md:col-span-5 rounded-2xl bg-dark-900 border border-slate-800 p-4 space-y-3">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Summary Assessment
                </span>
                <h3 className="text-base font-bold text-white mt-0.5">
                  {result.summary.overall_status}
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                <div className="p-2.5 rounded-lg bg-dark-950 border border-slate-800">
                  <span className="text-lg font-bold text-emerald-400 font-mono block">
                    {result.summary.supported_claims}
                  </span>
                  <span className="text-[10px] text-slate-400">Supported</span>
                </div>
                <div className="p-2.5 rounded-lg bg-dark-950 border border-slate-800">
                  <span className="text-lg font-bold text-rose-400 font-mono block">
                    {result.summary.contradicted_claims}
                  </span>
                  <span className="text-[10px] text-slate-400">Contradicted</span>
                </div>
                <div className="p-2.5 rounded-lg bg-dark-950 border border-slate-800">
                  <span className="text-lg font-bold text-amber-400 font-mono block">
                    {result.summary.partial_misleading_claims}
                  </span>
                  <span className="text-[10px] text-slate-400">Misleading</span>
                </div>
                <div className="p-2.5 rounded-lg bg-dark-950 border border-slate-800">
                  <span className="text-lg font-bold text-slate-400 font-mono block">
                    {result.summary.insufficient_evidence_claims}
                  </span>
                  <span className="text-[10px] text-slate-400">Unverified</span>
                </div>
              </div>
            </div>
          </div>

          {/* Timestamped Claims */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-white">
              Timestamped Claims ({result.timestamped_claims.length})
            </h3>
            {result.timestamped_claims.map((claimItem, idx) => (
              <ClaimCard
                key={idx}
                claimData={claimItem}
                onTimestampClick={handleSeek}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
