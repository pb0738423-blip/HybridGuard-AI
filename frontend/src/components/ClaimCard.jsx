import React, { useState } from 'react';
import VerdictBadge from './VerdictBadge';
import { ExternalLink, ChevronDown, ChevronUp, Clock, Check, X } from 'lucide-react';

export default function ClaimCard({ claimData, onTimestampClick }) {
  const [expanded, setExpanded] = useState(false);

  const {
    claim,
    verdict,
    confidence,
    explanation,
    citations = [],
    supporting_evidence = [],
    contradicting_evidence = [],
    timestamp_formatted,
    timestamp_seconds,
  } = claimData;

  const hasEvidence = citations.length > 0 || supporting_evidence.length > 0 || contradicting_evidence.length > 0;

  return (
    <div className="rounded-xl bg-dark-900 border border-slate-800/90 p-4 sm:p-5 hover:border-slate-700/80 transition-all">
      {/* Top Header: Timestamp & Verdict */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
        <div className="flex items-center gap-2">
          {timestamp_formatted && (
            <button
              onClick={() => onTimestampClick && onTimestampClick(timestamp_seconds)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-primary-500/10 text-primary-400 border border-primary-500/25 text-xs font-mono hover:bg-primary-500/20 transition-colors cursor-pointer"
              title="Click to seek video player"
            >
              <Clock className="w-3 h-3" />
              <span>{timestamp_formatted}</span>
            </button>
          )}
          <span className="text-xs text-slate-400">
            Confidence: <strong className="text-slate-200">{(confidence * 100).toFixed(0)}%</strong>
          </span>
        </div>
        <VerdictBadge verdict={verdict} size="sm" />
      </div>

      {/* Claim Body */}
      <h4 className="text-base font-semibold text-white mb-2 leading-snug">
        "{claim}"
      </h4>

      {/* Grounded Explanation */}
      <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-3">
        {explanation}
      </p>

      {/* Citations Preview / Toggle */}
      {hasEvidence && (
        <div className="pt-2.5 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-3">
            {supporting_evidence.length > 0 && (
              <span className="flex items-center gap-1 text-emerald-400">
                <Check className="w-3 h-3" /> {supporting_evidence.length} supporting
              </span>
            )}
            {contradicting_evidence.length > 0 && (
              <span className="flex items-center gap-1 text-rose-400">
                <X className="w-3 h-3" /> {contradicting_evidence.length} refuting
              </span>
            )}
            {citations.length > 0 && (
              <span>{citations.length} sources</span>
            )}
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-primary-400 hover:text-primary-300 font-medium transition-colors cursor-pointer"
          >
            <span>{expanded ? 'Hide Sources' : 'View Verified Sources'}</span>
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>
      )}

      {/* Expanded Citations */}
      {expanded && (
        <div className="mt-3.5 pt-3.5 border-t border-slate-800 space-y-3">
          {/* Supporting */}
          {supporting_evidence.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                Supporting Excerpts:
              </span>
              {supporting_evidence.map((s, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs">
                  <p className="italic text-slate-200 mb-1">"{s.excerpt}"</p>
                  <a
                    href={s.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 hover:underline inline-flex items-center gap-1 text-[11px]"
                  >
                    <span>{s.source_title}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
              ))}
            </div>
          )}

          {/* Contradicting */}
          {contradicting_evidence.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
                Refuting Excerpts:
              </span>
              {contradicting_evidence.map((c, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/20 text-xs">
                  <p className="italic text-slate-200 mb-1">"{c.excerpt}"</p>
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-rose-400 hover:underline inline-flex items-center gap-1 text-[11px]"
                  >
                    <span>{c.source_title}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
              ))}
            </div>
          )}

          {/* Web Reference Links */}
          {citations.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Reference Links:
              </span>
              <div className="flex flex-wrap gap-2">
                {citations.map((cite, idx) => (
                  <a
                    key={idx}
                    href={cite.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800/80 hover:bg-slate-800 border border-slate-700/70 text-xs text-slate-300 hover:text-white transition-colors"
                  >
                    <span className="truncate max-w-[200px]">{cite.title}</span>
                    <ExternalLink className="w-3 h-3 text-slate-400" />
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
