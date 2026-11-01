import React, { useState, useEffect, useRef } from 'react';
import { Radio, Mic, MicOff, Play, Square, RotateCcw, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import ClaimCard from '../components/ClaimCard';

const SIMULATED_STREAM_SEGMENTS = [
  { text: "Good evening and welcome to our live science briefing.", time: 0 },
  { text: "NASA confirmed that the James Webb Space Telescope detected water vapor on an exoplanet.", time: 6 },
  { text: "Meanwhile health authorities warned that drinking unpasteurized bleach does not cure viral infections and can cause fatal organ damage.", time: 14 },
  { text: "In economic news the central bank announced interest rates will remain unchanged through the fourth quarter.", time: 22 },
];

export default function LiveSpeech() {
  const [isRecording, setIsRecording] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [verifiedClaims, setVerifiedClaims] = useState([]);
  const [error, setError] = useState(null);

  const recognitionRef = useRef(null);
  const simTimerRef = useRef(null);
  const pollTimerRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = async (event) => {
        let current = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          const textChunk = item[0].transcript;
          current += textChunk;

          if (item.isFinal && sessionId) {
            try {
              await api.sendSpeechChunk(sessionId, textChunk, event.timeStamp / 1000, true);
            } catch (e) {}
          }
        }
        setTranscript((prev) => prev + ' ' + current);
      };

      recognition.onerror = (e) => {
        if (e.error === 'not-allowed') {
          setError('Microphone access denied. You can use the "Stream Simulation" button instead.');
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) try { recognitionRef.current.stop(); } catch (e) {}
      if (simTimerRef.current) clearInterval(simTimerRef.current);
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [sessionId]);

  useEffect(() => {
    if ((isRecording || isSimulating) && sessionId) {
      pollTimerRef.current = setInterval(async () => {
        try {
          const status = await api.getSpeechStatus(sessionId);
          if (status?.verifications) {
            setVerifiedClaims(status.verifications);
          }
        } catch (e) {}
      }, 2000);
    } else {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [isRecording, isSimulating, sessionId]);

  const startMic = async () => {
    setError(null);
    try {
      const sess = await api.createSpeechSession();
      setSessionId(sess.session_id);

      if (recognitionRef.current) {
        recognitionRef.current.start();
        setIsRecording(true);
      } else {
        setError('Web Speech API not supported in this browser. Try the Simulated Stream mode.');
      }
    } catch (e) {
      setError(e.message);
    }
  };

  const stopMic = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    setIsRecording(false);
  };

  const startSim = async () => {
    setError(null);
    setIsSimulating(true);
    setTranscript('');
    setVerifiedClaims([]);

    try {
      const sess = await api.createSpeechSession();
      setSessionId(sess.session_id);

      let step = 0;
      simTimerRef.current = setInterval(async () => {
        if (step < SIMULATED_STREAM_SEGMENTS.length) {
          const seg = SIMULATED_STREAM_SEGMENTS[step];
          setTranscript((prev) => (prev ? prev + ' ' : '') + seg.text);
          try {
            await api.sendSpeechChunk(sess.session_id, seg.text, seg.time, true);
          } catch (e) {}
          step++;
        } else {
          clearInterval(simTimerRef.current);
          setIsSimulating(false);
        }
      }, 3500);
    } catch (e) {
      setError(e.message);
      setIsSimulating(false);
    }
  };

  const stopSim = () => {
    if (simTimerRef.current) clearInterval(simTimerRef.current);
    setIsSimulating(false);
  };

  const handleReset = () => {
    stopMic();
    stopSim();
    setTranscript('');
    setVerifiedClaims([]);
    setSessionId(null);
    setError(null);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Real-Time Audio Fact-Checker
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Transcribes spoken audio, detects emerging claims on rolling intervals, and verifies assertions asynchronously.
        </p>
      </div>

      <div className="rounded-2xl bg-dark-900 border border-slate-800 p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {!isRecording ? (
              <button
                onClick={startMic}
                disabled={isSimulating}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white text-xs font-semibold shadow transition-all cursor-pointer"
              >
                <Mic className="w-3.5 h-3.5" />
                <span>Microphone</span>
              </button>
            ) : (
              <button
                onClick={stopMic}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow transition-all cursor-pointer animate-pulse"
              >
                <MicOff className="w-3.5 h-3.5" />
                <span>Stop Mic</span>
              </button>
            )}

            {!isSimulating ? (
              <button
                onClick={startSim}
                disabled={isRecording}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 border border-slate-700 text-slate-200 text-xs font-medium transition-all cursor-pointer"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Simulation Stream</span>
              </button>
            ) : (
              <button
                onClick={stopSim}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium transition-all cursor-pointer"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            )}

            <button
              onClick={handleReset}
              className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span className={`w-2 h-2 rounded-full ${
              isRecording || isSimulating ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'
            }`}></span>
            <span>{isRecording ? 'Listening...' : isSimulating ? 'Streaming...' : 'Idle'}</span>
          </div>
        </div>

        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
            Transcript Feed:
          </span>
          <div className="min-h-[80px] max-h-[140px] overflow-y-auto rounded-xl bg-dark-950 p-3.5 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans">
            {transcript ? (
              <p>{transcript}</p>
            ) : (
              <p className="text-slate-600 italic">Spoken transcript will appear here as speech is recognized...</p>
            )}
          </div>
        </div>

        {error && (
          <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Verified Claims List */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white">
          Extracted Claims ({verifiedClaims.length})
        </h3>
        {verifiedClaims.length > 0 ? (
          <div className="space-y-3">
            {verifiedClaims.map((claimItem, idx) => (
              <ClaimCard key={idx} claimData={claimItem} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-dark-900 border border-slate-800 p-6 text-center text-slate-500 text-xs">
            No claims detected yet. Start microphone recording or stream the simulated broadcast.
          </div>
        )}
      </div>
    </div>
  );
}
