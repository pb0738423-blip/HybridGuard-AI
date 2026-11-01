import React from 'react';

export default function ScoreGauge({ value, label, prediction, uncertainty, needsReview }) {
  const percent = Math.round(value <= 1.0 ? value * 100 : value);
  const isFake = prediction === 'Fake';
  const isReview = needsReview;

  const strokeColor = isReview 
    ? '#f59e0b' 
    : isFake 
    ? '#f43f5e' 
    : '#10b981';

  const badgeColor = isReview
    ? 'bg-amber-500/10 border-amber-500/25 text-amber-400'
    : isFake
    ? 'bg-rose-500/10 border-rose-500/25 text-rose-400'
    : 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400';

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percent / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-dark-900 border border-slate-800">
      <div className="relative w-24 h-24 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 90 90">
          <circle
            cx="45"
            cy="45"
            r={radius}
            className="stroke-slate-800"
            strokeWidth="6"
            fill="transparent"
          />
          <circle
            cx="45"
            cy="45"
            r={radius}
            stroke={strokeColor}
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-xl font-bold text-white font-mono">{percent}%</span>
          <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Confidence</span>
        </div>
      </div>

      <div className="mt-2.5 text-center">
        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeColor}`}>
          {isReview ? 'Needs Review' : prediction}
        </span>
        {label && <p className="text-[11px] text-slate-400 mt-1">{label}</p>}
      </div>
    </div>
  );
}
