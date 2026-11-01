import React, { useState } from 'react';
import { Newspaper, Send, RotateCcw, AlertTriangle, CheckCircle2, XCircle, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import ScoreGauge from '../components/ScoreGauge';
import WordAttributionBadge from '../components/WordAttributionBadge';

const SAMPLES = {
  real: {
    label: 'Verified Wire Report',
    title: 'Senate Confirms Veteran Diplomat to Ambassadorial Post Following Bipartisan Vote',
    text: `WASHINGTON — The United States Senate voted 78 to 21 on Thursday to confirm career foreign service officer Eleanor Vance as the next ambassador to the Federal Republic of Germany. The confirmation follows several weeks of committee hearings during which lawmakers from both parties questioned Vance on trade policy, NATO defense contributions, and cybersecurity cooperation.

Committee Chairman Richard Shelby praised Vance's three decades of diplomatic service in European security affairs, noting her previous tenure in Brussels and Warsaw.`
  },
  fake: {
    label: 'Sensational Fake News',
    title: 'BOMBSHELL REVEALED: Secret Cabal Caught Smuggling Alien Technology in Underground Military Base',
    text: `SHOCKING BREAKING NEWS: Unbelievable leaked documents from an anonymous military insider have finally proven what the mainstream media refused to report! A treasonous globalist cabal has been caught operating an illegal underground laboratory manufacturing secret frequency weapons and hidden biological chips. High-ranking military sources confirm that federal marshals were placed on high alert!`
  },
  borderline: {
    label: 'Borderline Sample',
    title: 'Industry Analysts Express Mixed Outlook on Proposed Regional Energy Grid Reform',
    text: `State regulators and regional grid operators convened on Wednesday to discuss proposed structural adjustments to interstate electricity transmission corridors. While clean energy proponents argue the plan could accelerate renewables integration, utility representatives voiced concern regarding near-term cost allocations.`
  }
};

export default function NewsDetection() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const charCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!text.trim() || text.trim().length < 15) {
      setError('Please provide at least 15 characters of text to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.predictNews(text, true, 10);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to complete prediction.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setText('');
    setResult(null);
    setError(null);
  };

  const loadSample = (type) => {
    const s = SAMPLES[type];
    if (s) {
      setText(`${s.title}\n\n${s.text}`);
      setResult(null);
      setError(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Clean Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          News Credibility Classifier
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Detects sensationalism, manipulative rhetoric, and stylistic deception using calibrated ML models.
        </p>
      </div>

      {/* Input Card */}
      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 sm:p-6 shadow-sm">
        {/* Sample Pills */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Sample Benchmarks:
          </span>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => loadSample('real')}
              className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-emerald-400 text-xs font-medium transition-colors cursor-pointer"
            >
              {SAMPLES.real.label}
            </button>
            <button
              type="button"
              onClick={() => loadSample('fake')}
              className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-rose-400 text-xs font-medium transition-colors cursor-pointer"
            >
              {SAMPLES.fake.label}
            </button>
            <button
              type="button"
              onClick={() => loadSample('borderline')}
              className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-amber-400 text-xs font-medium transition-colors cursor-pointer"
            >
              {SAMPLES.borderline.label}
            </button>
          </div>
        </div>

        {/* Text Area */}
        <form onSubmit={handleAnalyze} className="space-y-3">
          <textarea
            rows={7}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste news headline and article text to analyze..."
            className="w-full rounded-xl bg-dark-950 border border-slate-800 p-4 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary-500 transition-all font-sans leading-relaxed resize-y"
          />

          <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
            <span>{wordCount} words • {charCount} characters</span>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
              >
                Clear
              </button>
              <button
                type="submit"
                disabled={loading || !text.trim()}
                className="inline-flex items-center gap-1.5 px-5 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white text-xs font-semibold shadow transition-all cursor-pointer"
              >
                {loading ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Analyze</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-5 animate-fade-in">
          {/* Main Verdict Card */}
          <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 sm:p-6 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-3 w-full max-w-xl">
              <div className="flex items-center gap-2.5">
                {result.needs_review ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400 text-xs font-semibold">
                    <AlertTriangle className="w-4 h-4" /> Needs Review (Uncertain)
                  </span>
                ) : result.prediction === 'Fake' ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs font-semibold">
                    <XCircle className="w-4 h-4" /> Classified as Fabricated / Fake
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold">
                    <CheckCircle2 className="w-4 h-4" /> Classified as Reliable / Real
                  </span>
                )}
              </div>

              <h2 className="text-xl sm:text-2xl font-bold text-white">
                {result.needs_review
                  ? 'Marginal Confidence: Ambiguous Stylistic Features'
                  : result.prediction === 'Fake'
                  ? 'High Probability of Sensationalism & Deception'
                  : 'Consistent with Verified Journalistic Standards'}
              </h2>

              {/* Calibrated Probability Bar */}
              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-xs text-slate-400 font-mono">
                  <span>P(Real): {(result.p_real * 100).toFixed(1)}%</span>
                  <span>P(Fake): {(result.p_fake * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex">
                  <div
                    style={{ width: `${result.p_real * 100}%` }}
                    className="h-full bg-emerald-500 transition-all duration-500"
                  />
                  <div
                    style={{ width: `${result.p_fake * 100}%` }}
                    className="h-full bg-rose-500 transition-all duration-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex-shrink-0">
              <ScoreGauge
                value={result.confidence}
                prediction={result.prediction}
                uncertainty={result.uncertainty_score}
                needsReview={result.needs_review}
                label="Calibrated Score"
              />
            </div>
          </div>

          {/* Model Breakdown */}
          <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Constituent Classifier Outputs
              </span>
              <span className="text-xs text-slate-400">
                Consensus: <strong className="text-white">{(result.agreement_ratio * 100).toFixed(0)}%</strong>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {Object.entries(result.individual_models).map(([name, data]) => {
                const label = name === 'logistic_regression'
                  ? 'Logistic Regression'
                  : name === 'linear_svm'
                  ? 'Linear SVM'
                  : 'Multinomial NB';

                const isFake = data.prediction === 'Fake';
                return (
                  <div key={name} className="p-3.5 rounded-xl bg-dark-950 border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-200">{label}</span>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                        isFake ? 'text-rose-400 bg-rose-500/10' : 'text-emerald-400 bg-emerald-500/10'
                      }`}>
                        {data.prediction}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-slate-400 font-mono">
                      <span>Confidence:</span>
                      <span className="text-white">{(data.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Influential Words */}
          <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 space-y-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
              Influential Term Attributions
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <span className="text-xs font-medium text-rose-400 block">Terms Pushing Towards "Fake"</span>
                {result.top_fake_words.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {result.top_fake_words.map((w, idx) => (
                      <WordAttributionBadge key={idx} word={w.word} attribution={w.attribution} tfidf={w.tfidf_weight} isFakeOriented={true} />
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">None detected.</p>
                )}
              </div>

              <div className="space-y-2">
                <span className="text-xs font-medium text-emerald-400 block">Terms Pushing Towards "Real"</span>
                {result.top_real_words.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {result.top_real_words.map((w, idx) => (
                      <WordAttributionBadge key={idx} word={w.word} attribution={w.attribution} tfidf={w.tfidf_weight} isFakeOriented={false} />
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">None detected.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
