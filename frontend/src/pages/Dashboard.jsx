import React, { useEffect, useState } from 'react';
import { Newspaper, Search, Youtube, BarChart3, Radio, ArrowRight, ShieldCheck, CheckCircle2, Sparkles } from 'lucide-react';
import { api } from '../services/api';

export default function Dashboard({ onNavigate }) {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    api.getMetrics().then(setMetrics).catch(() => null);
  }, []);

  const stats = [
    { label: 'Model Accuracy', value: '96.96%', detail: 'Calibrated Linear SVM' },
    { label: 'Macro F1-Score', value: '96.93%', detail: 'Balanced Evaluation' },
    { label: 'Calibration Error', value: '0.82%', detail: 'ECE (Platt Scaled)' },
    { label: 'Inference Latency', value: '< 15 ms', detail: 'Instant CPU Execution' },
  ];

  const tools = [
    {
      id: 'news',
      title: 'Fake News Detector',
      description: 'Analyze article text, headlines, and rhetoric using our calibrated hybrid stacking classifier.',
      icon: Newspaper,
      cta: 'Analyze Article',
      badge: 'ML Ensemble',
    },
    {
      id: 'factcheck',
      title: 'Fact Checking Engine',
      description: 'Verify specific factual assertions against live encyclopedia and web sources with authentic citations.',
      icon: Search,
      cta: 'Verify Claim',
      badge: 'Live Sources',
    },
    {
      id: 'video',
      title: 'YouTube & Shorts Analysis',
      description: 'Extract captions, segment transcripts, and verify claims with click-to-seek video playback.',
      icon: Youtube,
      cta: 'Inspect Video',
      badge: 'Shorts & Longform',
    },
    {
      id: 'speech',
      title: 'Live Audio Stream',
      description: 'Real-time speech transcription with asynchronous claim verification and latency tracking.',
      icon: Radio,
      cta: 'Stream Audio',
      badge: 'Real-Time Extension',
    },
  ];

  return (
    <div className="space-y-10 max-w-6xl mx-auto">
      {/* Clean Hero */}
      <div className="text-center max-w-3xl mx-auto space-y-4 pt-4">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/10 text-primary-400 border border-primary-500/20 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Generation Verification Intelligence</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Verify Any News, Claim, or Video
        </h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
          HybridGuard AI combines explainable machine-learning text classification with grounded live evidence retrieval to combat misinformation.
        </p>

        {/* Quick Actions */}
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => onNavigate('news')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-xs font-semibold shadow-md shadow-primary-600/25 transition-all cursor-pointer"
          >
            <Newspaper className="w-4 h-4" />
            <span>Detect Fake News</span>
          </button>
          <button
            onClick={() => onNavigate('factcheck')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-all cursor-pointer"
          >
            <Search className="w-4 h-4" />
            <span>Fact-Check Claim</span>
          </button>
        </div>
      </div>

      {/* Clean Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-dark-900 border border-slate-800/90 text-center">
            <span className="text-xs text-slate-400">{s.label}</span>
            <div className="text-2xl font-bold text-white font-mono mt-0.5">{s.value}</div>
            <span className="text-[11px] text-slate-500">{s.detail}</span>
          </div>
        ))}
      </div>

      {/* Main Capabilities Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white tracking-tight">Core Modules</h2>
          <button 
            onClick={() => onNavigate('models')}
            className="text-xs text-primary-400 hover:text-primary-300 font-medium transition-colors"
          >
            View Model Benchmarks →
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tools.map((t) => {
            const Icon = t.icon;
            return (
              <div
                key={t.id}
                onClick={() => onNavigate(t.id)}
                className="group p-5 rounded-2xl bg-dark-900 border border-slate-800/90 hover:border-slate-700 hover:bg-slate-900/60 transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700/80 flex items-center justify-center text-primary-400 group-hover:bg-primary-600 group-hover:text-white transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-800/60 px-2.5 py-0.5 rounded border border-slate-700/60">
                      {t.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white group-hover:text-primary-300 transition-colors">
                    {t.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    {t.description}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-primary-400 group-hover:translate-x-0.5 transition-transform">
                  <span>{t.cta}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
