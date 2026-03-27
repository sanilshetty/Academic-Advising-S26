import { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  Box,
  Brain,
  Database,
  ExternalLink,
  Monitor,
  Paperclip,
  RotateCcw,
  Search,
  Send,
  Sparkles,
  X,
  Zap,
} from 'lucide-react';
import purdueIcon from './assets/purdue-icon.png';
import { getStatus, sendChat } from './api';
import { processTranscriptFile } from './pdfRedactor';

const DEFAULT_TRANSCRIPT = 'No transcript provided.';

function getCurrentTime() {
  return new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function Modal({ onClose, children, maxWidth = 'max-w-2xl' }) {
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-6">
      <div className={`bg-black border border-[#4075C9]/50 rounded-3xl w-full ${maxWidth} p-8 shadow-2xl shadow-[#4075C9]/20 relative`}>
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-full transition-colors"
          aria-label="Close"
        >
          <X className="w-6 h-6 text-white/60" />
        </button>
        {children}
      </div>
    </div>
  );
}

export default function App() {
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [showChat, setShowChat] = useState(false);
  const [showCodoInfo, setShowCodoInfo] = useState(false);
  const [showBotInfo, setShowBotInfo] = useState(false);
  const [showRequirements, setShowRequirements] = useState(false);
  const [showDisclaimer, setShowDisclaimer] = useState(true);
  const [showTranscriptModal, setShowTranscriptModal] = useState(false);
  const [showTranscriptSteps, setShowTranscriptSteps] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [transcriptData, setTranscriptData] = useState(DEFAULT_TRANSCRIPT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [dbReady, setDbReady] = useState(null);

  const transcriptRef = useRef(null);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    const check = () => {
      getStatus()
        .then((data) => setDbReady(Boolean(data.db_ready)))
        .catch(() => setDbReady(false));
    };
    check();
    const id = setInterval(check, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, loading]);

  const addMessage = (role, text, latency_ms) => {
    setChatMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.random(),
        role,
        text,
        time: getCurrentTime(),
        latency_ms,
      },
    ]);
  };

  const handleStartChat = () => {
    setShowChat(true);
    if (chatMessages.length === 0) {
      addMessage('assistant', "Hi, I'm CODO AI. Ask me about your CS CODO eligibility.");
    }
  };

  const handleSendMessage = async () => {
    const q = message.trim();
    if (!q || loading) return;

    const history = chatMessages.map((m) => ({
      role: m.role,
      content: m.text,
    }));

    setError('');
    setMessage('');
    setShowChat(true);
    addMessage('user', q);
    setLoading(true);

    try {
      const res = await sendChat(q, transcriptData, history);
      addMessage('assistant', res.answer, res.latency_ms);
    } catch (err) {
      setError(err.message || 'Chat request failed.');
    } finally {
      setLoading(false);
    }
  };

  // Auto-trigger eligibility analysis immediately after transcript upload.
  // We pass freshTranscript directly to sendChat instead of reading from
  // transcriptData state, which may not have updated yet (stale closure bug).
  const autoAnalyzeTranscript = async (freshTranscript) => {
    const question = 'Am I eligible to CODO into Computer Science?';
    setLoading(true);
    setShowChat(true);
    addMessage('user', question);
    try {
      const res = await sendChat(question, freshTranscript, []);
      addMessage('assistant', res.answer, res.latency_ms);
    } catch (err) {
      setError(err.message || 'Chat request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleTranscriptFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF transcript.');
      event.target.value = '';
      return;
    }

    setUploadedFile(file);
    setError('');

    try {
      const parsed = await processTranscriptFile(file);
      const freshTranscript = parsed.redactedText || DEFAULT_TRANSCRIPT;
      setTranscriptData(freshTranscript);
      setShowTranscriptModal(false);
      // Auto-send analysis using the fresh transcript text directly
      await autoAnalyzeTranscript(freshTranscript);
    } catch (err) {
      setError(err.message || 'Failed to process transcript PDF.');
    } finally {
      event.target.value = '';
    }
  };



  const handleRestartChat = () => {
    setShowChat(false);
    setChatMessages([]);
    setMessage('');
    setError('');
  };

  return (
    <div className="size-full bg-black relative overflow-hidden flex flex-col">
      <header className="bg-black px-6 py-4 flex items-center justify-between border-b-2 border-[#4075C9]">
        <div className="flex items-center gap-4">
          <img src={purdueIcon} alt="Purdue P" className="w-12 h-12 object-contain" />
          <div className="border-l-2 border-[#4075C9]/50 pl-4 ml-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">CODO AI</h1>
            <p className="text-xs text-[#4075C9] uppercase tracking-wide">Check Your CODO Eligibility</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="px-3 py-1.5 rounded-full border border-white/20 text-white/80 flex items-center gap-2">
            <Database className="w-4 h-4 text-[#4075C9]" />
            {dbReady === null ? 'Checking DB…' : dbReady ? 'DB Ready' : 'DB Not Ready'}
          </div>



          <button
            onClick={() => setShowRequirements(true)}
            className="text-white/60 hover:text-white transition-colors flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            Requirements
          </button>

          <button
            onClick={() => setShowContactModal(true)}
            className="text-white/60 hover:text-white transition-colors flex items-center gap-2"
          >
            <Box className="w-4 h-4" />
            Contact Us
          </button>

          <button
            onClick={handleRestartChat}
            className="ml-2 px-4 py-2 bg-[#4075C9] hover:bg-[#3065B9] rounded-full flex items-center gap-2 transition-colors"
          >
            <RotateCcw className="w-4 h-4 text-white" />
            <span className="text-white text-sm font-medium">Restart Chat</span>
          </button>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-start pt-10 pb-6 px-6 bg-black overflow-y-auto">
        <div className="flex flex-col items-center gap-6 max-w-4xl w-full">
          <div className="flex flex-col items-center gap-4">
            <div className="w-20 h-20 rounded-2xl bg-black border-2 border-[#4075C9] flex items-center justify-center shadow-xl shadow-[#4075C9]/20">
              <Monitor className="w-10 h-10 text-[#4075C9]" strokeWidth={2} />
            </div>
            <h2 className="text-4xl font-medium text-white">Hi, I'm CODO AI</h2>
            <p className="text-white/50 text-lg">Upload your transcript and ask eligibility questions.</p>
          </div>



          {showChat && (
            <div className="w-full space-y-4 max-h-[45vh] overflow-y-auto pr-1">
              {chatMessages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                  <div className="max-w-3xl">
                    <div className={`${msg.role === 'assistant' ? 'bg-white/10 border border-white/20' : 'bg-[#4075C9]'} rounded-3xl px-6 py-4 text-white shadow-lg`}>
                      <p className="whitespace-pre-line">{msg.text}</p>
                    </div>
                    <div className="text-[11px] text-white/40 mt-1 px-2 flex gap-2">
                      <span>{msg.time}</span>
                      {msg.latency_ms != null && <span>· {(msg.latency_ms / 1000).toFixed(2)}s</span>}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white/10 border border-white/20 rounded-3xl px-6 py-4 text-white shadow-lg">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#8fb6ff] animate-pulse" />
                      <span className="w-2 h-2 rounded-full bg-[#8fb6ff] animate-pulse [animation-delay:150ms]" />
                      <span className="w-2 h-2 rounded-full bg-[#8fb6ff] animate-pulse [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>
          )}

          <div className="w-full bg-white/10 backdrop-blur-sm border border-white/20 rounded-3xl p-6 shadow-lg">
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="Ask about CODO eligibility, GPA, or transcript details"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-white/40 text-lg"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />

              <input
                ref={transcriptRef}
                type="file"
                id="transcript-upload"
                accept=".pdf"
                onChange={handleTranscriptFile}
                className="hidden"
              />
              <button
                onClick={() => transcriptRef.current?.click()}
                className="p-2 hover:bg-white/10 rounded-full transition-colors"
                title="Upload transcript PDF"
              >
                <Paperclip className="w-6 h-6 text-[#4075C9]" />
              </button>

              <button
                onClick={handleSendMessage}
                disabled={!message.trim() || loading}
                className="p-2 bg-[#4075C9] hover:bg-[#3065B9] rounded-full transition-colors disabled:opacity-40"
                title="Send"
              >
                <Send className="w-5 h-5 text-white" />
              </button>
            </div>

            {uploadedFile && (
              <div className="mt-4 px-4 py-2 bg-[#4075C9]/20 border border-[#4075C9]/40 rounded-full flex items-center gap-2 w-fit">
                <span className="text-sm text-[#9ec2ff]">PDF: {uploadedFile.name}</span>
              </div>
            )}

            {!showChat && (
              <div className="flex items-center gap-4 mt-6 flex-wrap">
                <button
                  onClick={() => setShowCodoInfo(true)}
                  className="px-6 py-2 bg-[#222222] hover:bg-[#2a2a2a] border border-white/10 hover:border-[#4075C9]/50 rounded-full flex items-center gap-2 transition-colors"
                >
                  <Search className="w-5 h-5 text-[#4075C9]" />
                  <span className="text-gray-300 underline">What is CODO?</span>
                </button>
                <button
                  onClick={() => setShowBotInfo(true)}
                  className="px-6 py-2 bg-[#222222] hover:bg-[#2a2a2a] border border-white/10 hover:border-[#4075C9]/50 rounded-full flex items-center gap-2 transition-colors"
                >
                  <Brain className="w-5 h-5 text-[#4075C9]" />
                  <span className="text-gray-300 underline">How to use this tool</span>
                </button>
                <button
                  onClick={handleStartChat}
                  className="px-6 py-2 bg-[#4075C9] hover:bg-[#3065B9] rounded-full flex items-center gap-2 transition-colors"
                >
                  <Zap className="w-4 h-4 text-white" />
                  <span className="text-white">Quick Check</span>
                </button>
              </div>
            )}

            {error && <p className="text-red-300 text-sm mt-4">{error}</p>}
          </div>
        </div>
      </main>

      {showCodoInfo && (
        <Modal onClose={() => setShowCodoInfo(false)}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-full bg-[#4075C9] flex items-center justify-center">
              <Search className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-3xl font-semibold text-white">What is CODO?</h2>
          </div>
          <div className="space-y-4 text-white/70">
            <p>
              CODO means <span className="text-white font-semibold">Change of Degree Objective</span>. It is Purdue&apos;s process for changing majors.
            </p>
            <p>
              This advisor helps you understand whether your current academic record aligns with CS change-of-major expectations.
            </p>
          </div>
        </Modal>
      )}

      {showBotInfo && (
        <Modal onClose={() => setShowBotInfo(false)}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-full bg-[#4075C9] flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-3xl font-semibold text-white">How To Use</h2>
          </div>
          <ol className="space-y-3 text-white/70 list-decimal list-inside">
            <li>Upload your transcript PDF (paperclip icon).</li>
            <li>Ask a specific eligibility question.</li>
            <li>Upload knowledge-base files in the header if needed.</li>
          </ol>
        </Modal>
      )}

      {showRequirements && (
        <Modal onClose={() => setShowRequirements(false)}>
          <h2 className="text-3xl font-semibold text-white mb-6">CS CODO Requirements (Summary)</h2>
          <ul className="space-y-3 text-white/80">
            <li>GPA and course thresholds vary by term and policy updates.</li>
            <li>Core math and CS prerequisites are typically required.</li>
            <li>Use this chat to evaluate your situation against the loaded docs.</li>
          </ul>
        </Modal>
      )}

      {showTranscriptModal && (
        <Modal onClose={() => setShowTranscriptModal(false)} maxWidth="max-w-lg">
          <div className="flex flex-col items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-[#4075C9] flex items-center justify-center shadow-xl">
              <Paperclip className="w-8 h-8 text-white" strokeWidth={2} />
            </div>
            <div className="text-center">
              <h2 className="text-3xl font-semibold text-white mb-2">Upload Your Transcript</h2>
              <p className="text-white/50">Upload a PDF to include transcript context in chat.</p>
            </div>
            <input
              type="file"
              id="transcript-modal-upload"
              accept=".pdf"
              onChange={handleTranscriptFile}
              className="hidden"
            />
            <label
              htmlFor="transcript-modal-upload"
              className="w-full px-6 py-4 bg-[#4075C9] hover:bg-[#3065B9] text-white rounded-2xl transition-all cursor-pointer flex items-center justify-center gap-3 shadow-lg font-semibold text-lg"
            >
              <Paperclip className="w-6 h-6" />
              Choose PDF File
            </label>
            <button
              onClick={() => {
                setShowTranscriptModal(false);
                setShowTranscriptSteps(true);
              }}
              className="w-full px-6 py-3 bg-white/5 hover:bg-white/10 border border-[#4075C9]/40 hover:border-[#4075C9] text-white/70 hover:text-white rounded-2xl transition-colors font-medium flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4 text-[#4075C9]" />
              How to get my transcript
            </button>
          </div>
        </Modal>
      )}

      {showTranscriptSteps && (
        <Modal onClose={() => setShowTranscriptSteps(false)} maxWidth="max-w-lg">
          <h2 className="text-2xl font-semibold text-white mb-4">Transcript Steps</h2>
          <ol className="space-y-3 text-white/70 list-decimal list-inside">
            <li>Sign into MyPurdue.</li>
            <li>Open Student Records, then Academic Transcript.</li>
            <li>Download unofficial transcript as PDF.</li>
            <li>Return here and upload it.</li>
          </ol>
          <div className="flex gap-3 pt-6">
            <button
              onClick={() => {
                setShowTranscriptSteps(false);
                setShowTranscriptModal(true);
              }}
              className="flex items-center gap-2 px-5 py-3 bg-[#222222] hover:bg-[#2a2a2a] border border-white/20 text-white rounded-2xl transition-colors font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button
              onClick={() => setShowTranscriptSteps(false)}
              className="flex-1 px-6 py-3 bg-[#4075C9] hover:bg-[#3065B9] text-white rounded-2xl transition-colors font-semibold"
            >
              Got It
            </button>
          </div>
        </Modal>
      )}

      {showContactModal && (
        <Modal onClose={() => setShowContactModal(false)} maxWidth="max-w-lg">
          <div className="flex flex-col items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-[#4075C9] flex items-center justify-center shadow-xl">
              <Box className="w-8 h-8 text-white" strokeWidth={2} />
            </div>
            <div className="text-center">
              <h2 className="text-3xl font-semibold text-white mb-2">Contact Us</h2>
              <p className="text-white/50">Questions about CODO? Reach out directly.</p>
            </div>
            <div className="w-full bg-[#4075C9]/10 border border-[#4075C9]/30 rounded-2xl p-6 text-center">
              <p className="text-sm text-white/50 mb-3">Email:</p>
              <a href="mailto:csug@purdue.edu" className="text-2xl font-semibold text-[#79a8ff] hover:text-[#9ec2ff] transition-colors">
                csug@purdue.edu
              </a>
            </div>
          </div>
        </Modal>
      )}

      {showDisclaimer && (
        <Modal onClose={() => {
          setShowDisclaimer(false);
          setShowTranscriptModal(true);
        }} maxWidth="max-w-md">
          <div className="flex flex-col items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-[#4075C9] flex items-center justify-center shadow-xl">
              <span className="text-3xl">⚠️</span>
            </div>
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-semibold text-white">Important Notice</h2>
              <p className="text-white/70 text-base leading-relaxed">
                CODOing into Computer Science is highly competitive. Meeting the minimum requirements <strong className="text-[#9ec2ff]">does not guarantee admission</strong> into the major.
              </p>
              <p className="text-white/70 text-base leading-relaxed">
                This AI tool is a helpful guide based on official policy, but it <strong className="text-[#9ec2ff]">cannot provide an official decision</strong> on your CODO status.
              </p>
            </div>
            <button
              onClick={() => {
                setShowDisclaimer(false);
                setShowTranscriptModal(true);
              }}
              className="w-full px-6 py-4 bg-[#4075C9] hover:bg-[#3065B9] text-white rounded-2xl transition-all cursor-pointer shadow-lg font-semibold text-lg"
            >
              I Understand
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
