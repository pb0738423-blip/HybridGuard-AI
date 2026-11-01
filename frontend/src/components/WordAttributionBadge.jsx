import React from 'react';

export default function WordAttributionBadge({ word, attribution, tfidf, isFakeOriented }) {
  const isPositive = isFakeOriented;
  const colorClasses = isPositive
    ? 'bg-rose-500/10 text-rose-300 border-rose-500/20 hover:bg-rose-500/15'
    : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20 hover:bg-emerald-500/15';

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md border text-xs font-mono transition-colors ${colorClasses}`}
      title={`Token: "${word}" | Attribution: ${attribution.toFixed(4)} | TF-IDF: ${tfidf ? tfidf.toFixed(4) : 'N/A'}`}
    >
      <span className="font-medium">{word}</span>
      <span className="text-[10px] opacity-70">
        {isPositive ? '+' : '-'}{Math.abs(attribution).toFixed(2)}
      </span>
    </span>
  );
}
