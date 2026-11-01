import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle, FileQuestion } from 'lucide-react';

export default function VerdictBadge({ verdict, size = 'md' }) {
  let config = {
    color: 'bg-slate-800/80 text-slate-300 border-slate-700',
    icon: HelpCircle,
    label: verdict || 'Unverified',
  };

  switch (verdict) {
    case 'Supported':
      config = {
        color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
        icon: CheckCircle2,
        label: 'Supported',
      };
      break;
    case 'Contradicted':
      config = {
        color: 'bg-rose-500/10 text-rose-400 border-rose-500/25',
        icon: XCircle,
        label: 'Contradicted',
      };
      break;
    case 'Partially Supported / Misleading':
      config = {
        color: 'bg-amber-500/10 text-amber-400 border-amber-500/25',
        icon: AlertTriangle,
        label: 'Misleading / Partial',
      };
      break;
    case 'Insufficient Evidence':
      config = {
        color: 'bg-slate-800 text-slate-400 border-slate-700/60',
        icon: HelpCircle,
        label: 'Insufficient Evidence',
      };
      break;
    case 'Not a Checkable Factual Claim':
      config = {
        color: 'bg-blue-500/10 text-blue-400 border-blue-500/25',
        icon: FileQuestion,
        label: 'Subjective / Opinion',
      };
      break;
    default:
      break;
  }

  const Icon = config.icon;
  const sizeClasses = size === 'sm' 
    ? 'px-2 py-0.5 text-xs font-medium' 
    : size === 'lg'
    ? 'px-3.5 py-1.5 text-sm font-semibold'
    : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${sizeClasses} ${config.color}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
}
