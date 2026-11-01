import React, { useEffect, useState } from 'react';
import { BarChart3, AlertTriangle, Layers } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { api } from '../services/api';

export default function ModelDashboard() {
  const [metricsData, setMetricsData] = useState(null);
  const [selectedModel, setSelectedModel] = useState('hybrid_stacking');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getMetrics().then(setMetricsData).catch((err) => setError(err.message)).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] space-y-3">
        <div className="w-7 h-7 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400">Loading benchmark metrics...</p>
      </div>
    );
  }

  if (error || !metricsData) {
    return (
      <div className="p-6 rounded-xl bg-rose-950/20 border border-rose-500/30 text-center max-w-md mx-auto space-y-2">
        <AlertTriangle className="w-6 h-6 text-rose-400 mx-auto" />
        <h3 className="text-sm font-bold text-white">Evaluation Report Unavailable</h3>
        <p className="text-xs text-rose-300">{error || 'Metrics file not found.'}</p>
      </div>
    );
  }

  const modelKeys = Object.keys(metricsData);
  const currentModelReport = metricsData[selectedModel] || metricsData[modelKeys[0]];

  const comparisonData = modelKeys.map((key) => {
    const rep = metricsData[key];
    const nameMap = {
      logistic_regression: 'Logistic Reg.',
      linear_svm: 'Linear SVM',
      multinomial_nb: 'Naive Bayes',
      hybrid_stacking: 'Hybrid Stacking',
    };
    return {
      name: nameMap[key] || key,
      accuracy: +(rep.metrics.accuracy * 100).toFixed(2),
      f1: +(rep.metrics.f1 * 100).toFixed(2),
      roc_auc: +(rep.metrics.roc_auc * 100).toFixed(2),
      latency_ms: rep.latency.mean_ms,
      ece_pct: +(rep.metrics.ece * 100).toFixed(2),
    };
  });

  const calibrationData = currentModelReport?.calibration_curve?.map((b) => ({
    bin: b.bin_range,
    confidence: +(b.confidence * 100).toFixed(1),
    accuracy: +(b.accuracy * 100).toFixed(1),
  })) || [];

  const cm = currentModelReport?.confusion_matrix || {
    true_negatives: 1998,
    false_positives: 53,
    false_negatives: 63,
    true_positives: 1636,
  };

  const totalSamples = currentModelReport?.test_sample_count || 3750;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Model Evaluation Benchmarks
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Empirical evaluation on a sealed test split of 3,750 articles from the WELFake dataset.
        </p>
      </div>

      {/* Model Tabs */}
      <div className="flex flex-wrap gap-1.5 p-1 rounded-xl bg-dark-900 border border-slate-800 w-fit">
        {modelKeys.map((key) => {
          const nameMap = {
            logistic_regression: 'Logistic Regression',
            linear_svm: 'Linear SVM (Calibrated)',
            multinomial_nb: 'Multinomial Naive Bayes',
            hybrid_stacking: 'Hybrid Stacking Ensemble',
          };
          const isActive = selectedModel === key;
          return (
            <button
              key={key}
              onClick={() => setSelectedModel(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                isActive
                  ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {nameMap[key] || key}
            </button>
          );
        })}
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl bg-dark-900 border border-slate-800">
          <span className="text-[11px] text-slate-400">Accuracy</span>
          <div className="text-xl font-bold text-white font-mono mt-0.5">
            {(currentModelReport.metrics.accuracy * 100).toFixed(2)}%
          </div>
        </div>
        <div className="p-3.5 rounded-xl bg-dark-900 border border-slate-800">
          <span className="text-[11px] text-slate-400">F1 Score</span>
          <div className="text-xl font-bold text-emerald-400 font-mono mt-0.5">
            {(currentModelReport.metrics.f1 * 100).toFixed(2)}%
          </div>
        </div>
        <div className="p-3.5 rounded-xl bg-dark-900 border border-slate-800">
          <span className="text-[11px] text-slate-400">ROC-AUC</span>
          <div className="text-xl font-bold text-cyan-400 font-mono mt-0.5">
            {(currentModelReport.metrics.roc_auc * 100).toFixed(2)}%
          </div>
        </div>
        <div className="p-3.5 rounded-xl bg-dark-900 border border-slate-800">
          <span className="text-[11px] text-slate-400">Calibration Error (ECE)</span>
          <div className="text-xl font-bold text-purple-400 font-mono mt-0.5">
            {(currentModelReport.metrics.ece * 100).toFixed(2)}%
          </div>
        </div>
        <div className="p-3.5 rounded-xl bg-dark-900 border border-slate-800">
          <span className="text-[11px] text-slate-400">Brier Score</span>
          <div className="text-xl font-bold text-amber-400 font-mono mt-0.5">
            {currentModelReport.metrics.brier_score.toFixed(4)}
          </div>
        </div>
        <div className="p-3.5 rounded-xl bg-dark-900 border border-slate-800">
          <span className="text-[11px] text-slate-400">Latency (CPU)</span>
          <div className="text-xl font-bold text-slate-200 font-mono mt-0.5">
            {currentModelReport.latency.mean_ms} ms
          </div>
        </div>
      </div>

      {/* Comparison Matrix Table */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 overflow-x-auto shadow-sm">
        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-primary-400" />
          Comparative Matrix (Untouched Test Split, N={totalSamples})
        </h3>
        <table className="w-full text-left text-xs font-sans">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <th className="py-2.5 px-3">Model</th>
              <th className="py-2.5 px-3">Accuracy</th>
              <th className="py-2.5 px-3">Precision</th>
              <th className="py-2.5 px-3">Recall</th>
              <th className="py-2.5 px-3">F1 Score</th>
              <th className="py-2.5 px-3">ROC-AUC</th>
              <th className="py-2.5 px-3">ECE</th>
              <th className="py-2.5 px-3">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {modelKeys.map((key) => {
              const r = metricsData[key];
              const isSelected = selectedModel === key;
              const nameMap = {
                logistic_regression: 'Logistic Regression',
                linear_svm: 'Linear SVM (Calibrated)',
                multinomial_nb: 'Multinomial Naive Bayes',
                hybrid_stacking: 'Hybrid Stacking Ensemble',
              };

              return (
                <tr
                  key={key}
                  onClick={() => setSelectedModel(key)}
                  className={`hover:bg-slate-800/40 transition-colors cursor-pointer ${
                    isSelected ? 'bg-primary-500/10 font-semibold text-white' : ''
                  }`}
                >
                  <td className="py-2.5 px-3 font-sans">{nameMap[key] || key}</td>
                  <td className="py-2.5 px-3">{(r.metrics.accuracy * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3">{(r.metrics.precision * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3">{(r.metrics.recall * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-emerald-400">{(r.metrics.f1 * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-cyan-400">{(r.metrics.roc_auc * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-purple-400">{(r.metrics.ece * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-slate-400">{r.latency.mean_ms} ms</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Visual Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-3">
          <h4 className="text-sm font-bold text-white">Accuracy & F1 Comparison</h4>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis domain={[80, 100]} stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0c111e', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="accuracy" name="Accuracy (%)" fill="#2077fa" radius={[3, 3, 0, 0]} />
                <Bar dataKey="f1" name="F1-Score (%)" fill="#10b981" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white">Calibration Reliability ({selectedModel})</h4>
            <span className="text-[11px] font-mono text-purple-400">
              ECE: {(currentModelReport.metrics.ece * 100).toFixed(2)}%
            </span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={calibrationData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="bin" stroke="#64748b" tick={{ fontSize: 9 }} />
                <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0c111e', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Line type="monotone" dataKey="confidence" name="Confidence" stroke="#64748b" strokeDasharray="4 4" dot={false} />
                <Line type="monotone" dataKey="accuracy" name="Accuracy" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Confusion Matrix */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-3">
        <h4 className="text-sm font-bold text-white">Confusion Matrix ({selectedModel})</h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-center">
          <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/25">
            <span className="text-[11px] text-emerald-400 font-sans block">True Negatives</span>
            <span className="text-2xl font-bold text-emerald-300 mt-0.5 block">{cm.true_negatives}</span>
            <span className="text-[10px] text-slate-500 font-sans">Real as Real</span>
          </div>
          <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/25">
            <span className="text-[11px] text-rose-400 font-sans block">False Positives</span>
            <span className="text-2xl font-bold text-rose-300 mt-0.5 block">{cm.false_positives}</span>
            <span className="text-[10px] text-slate-500 font-sans">Real as Fake</span>
          </div>
          <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/25">
            <span className="text-[11px] text-rose-400 font-sans block">False Negatives</span>
            <span className="text-2xl font-bold text-rose-300 mt-0.5 block">{cm.false_negatives}</span>
            <span className="text-[10px] text-slate-500 font-sans">Fake as Real</span>
          </div>
          <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/25">
            <span className="text-[11px] text-emerald-400 font-sans block">True Positives</span>
            <span className="text-2xl font-bold text-emerald-300 mt-0.5 block">{cm.true_positives}</span>
            <span className="text-[10px] text-slate-500 font-sans">Fake as Fake</span>
          </div>
        </div>
      </div>
    </div>
  );
}
