import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function Footer({ onNavigate }) {
  return (
    <footer className="border-t border-slate-800/80 bg-dark-950 mt-16 py-8 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Left: Brand */}
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-primary-400" />
          <span className="font-semibold text-white">HybridGuard AI</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">Hybrid Fake News Detection & Real-Time Fact Checking</span>
        </div>

        {/* Right: Clean Links */}
        <div className="flex items-center space-x-5 text-slate-400">
          <button onClick={() => onNavigate('news')} className="hover:text-slate-200 transition-colors">Detector</button>
          <button onClick={() => onNavigate('factcheck')} className="hover:text-slate-200 transition-colors">Fact Check</button>
          <button onClick={() => onNavigate('video')} className="hover:text-slate-200 transition-colors">Video</button>
          <button onClick={() => onNavigate('models')} className="hover:text-slate-200 transition-colors">Benchmarks</button>
          <button onClick={() => onNavigate('about')} className="hover:text-slate-200 transition-colors">Methodology</button>
          <a href="/docs" target="_blank" rel="noopener noreferrer" className="hover:text-slate-200 transition-colors">API Docs</a>
        </div>
      </div>
    </footer>
  );
}
