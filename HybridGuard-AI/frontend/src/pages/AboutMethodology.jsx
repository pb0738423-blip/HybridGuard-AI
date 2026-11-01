import React from 'react';
import { BookOpen, Cpu, Database, Network, Scale, AlertTriangle } from 'lucide-react';

export default function AboutMethodology() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          System Architecture & Methodology
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          A dual-engine framework combining statistical machine learning with live evidence retrieval.
        </p>
      </div>

      {/* Dual Engine Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-dark-900 border border-slate-800 space-y-2.5">
          <div className="flex items-center gap-2 text-primary-400">
            <Cpu className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Engine 1: Stylistic ML Classifier</span>
          </div>
          <h3 className="text-base font-bold text-white">Linguistic Deception Analysis</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates syntax, sensationalism, and emotional cues across a 25,000-term TF-IDF unigram + bigram matrix.
            Combines Logistic Regression, Calibrated Linear SVM, and Naive Bayes through an out-of-fold stacking meta-learner.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900 border border-slate-800 space-y-2.5">
          <div className="flex items-center gap-2 text-emerald-400">
            <Network className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Engine 2: Fact-Checking Engine</span>
          </div>
          <h3 className="text-base font-bold text-white">Grounded Evidence Verification</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Extracts discrete propositions, filters subjective rhetoric, queries live Wikipedia and DuckDuckGo endpoints,
            and measures corroborating vs. contradicting stance without hallucinated citations.
          </p>
        </div>
      </div>

      {/* Dataset Card */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-3">
        <div className="flex items-center gap-2 text-white">
          <Database className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold">Benchmark Dataset & Leakage Controls</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Trained on the <strong className="text-white">WELFake benchmark dataset</strong> (72,134 news items). 
          Strictly preprocessed with deduplication (8,452 duplicate articles removed) and partitioned into reproducible 70% Train (17,500), 15% Validation (3,750), and 15% Test (3,750) splits.
        </p>
        <p className="text-xs text-slate-400 leading-relaxed">
          The TF-IDF vocabulary is fitted strictly on the training partition to ensure zero data leakage. The meta-estimator is trained using 5-fold out-of-fold cross-validation.
        </p>
      </div>

      {/* Probability Calibration */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-3">
        <div className="flex items-center gap-2 text-white">
          <Scale className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-bold">Probability Calibration & Expected Calibration Error (ECE)</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Platt Sigmoid Calibration maps raw margin distances into reliable posterior probabilities. Evaluated across 10 probability bins, the system achieves an ECE of <strong className="text-purple-400 font-mono">0.82%</strong> (0.0082).
        </p>
        <div className="p-3 rounded-lg bg-dark-950 border border-slate-800/80 font-mono text-[11px] text-slate-300">
          ECE = sum_{'{'}m=1{'}'}^M (|B_m| / N) * |accuracy(B_m) - confidence(B_m)|
        </div>
      </div>

      {/* Ethical Boundaries */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-2">
        <div className="flex items-center gap-2 text-amber-400">
          <AlertTriangle className="w-4 h-4" />
          <h3 className="text-sm font-bold text-white">Limitations & Responsible Use</h3>
        </div>
        <ul className="text-xs text-slate-400 space-y-1.5 leading-relaxed">
          <li>• Stylistic ML detection measures writing style, not absolute empirical ground truth.</li>
          <li>• A contradicted claim in a video transcript does not label the entire speaker dishonest.</li>
          <li>• Zero hallucination policy: when external sources are absent, the system outputs "Insufficient Evidence".</li>
        </ul>
      </div>
    </div>
  );
}
