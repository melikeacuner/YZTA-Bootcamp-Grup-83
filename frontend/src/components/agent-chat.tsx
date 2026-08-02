"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { getSession, submitStepResponse, agentResolve, sendToPool, searchKnowledge } from "@/lib/api";
import { SessionResponse, KnowledgeSearchResult } from "@/lib/types";
import { Send, CheckCircle, HelpCircle, Bot, User, Loader2, ArrowRight, Sparkles, Inbox, X } from "lucide-react";
import UnifiedRecordDetail from "./unified-record-detail";

interface AgentChatProps {
  sessionId: string;
  onFinalized: (recordId: string) => void;
  onViewReport?: (recordId: string) => void;
}

export default function AgentChat({ sessionId, onFinalized, onViewReport }: AgentChatProps) {
  const { token } = useAuth();
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [sendingPool, setSendingPool] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Similar records state for top-right dynamic search
  const [similarRecords, setSimilarRecords] = useState<KnowledgeSearchResult[]>([]);
  const [previewRecordId, setPreviewRecordId] = useState<string | null>(null);

  function handleRecordClick(recordId: string) {
    setPreviewRecordId(recordId);
  }

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadSession = useCallback(async () => {
    if (!token || !sessionId) return;
    try {
      const s = await getSession(token, sessionId);
      setSession(s);
      setMessages(s.agent_chat_history || []);

      // Trigger initial dynamic search
      if (s.problem_description) {
        const results = await searchKnowledge(token, s.problem_description);
        setSimilarRecords(results.slice(0, 3));
      }
    } catch (err) {
      console.error("Failed to load session details:", err);
      setError("Oturum yüklenirken hata oluştu.");
    } finally {
      setLoading(false);
    }
  }, [token, sessionId]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    loadSession();
  }, [loadSession, sessionId]);

  // Dynamic similarity search when user types or messages update
  useEffect(() => {
    if (!token || !session) return;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user")?.content || "";
    const queryText = `${session.problem_description} ${lastUserMsg}`.trim();
    if (queryText.length < 5) return;

    const timer = setTimeout(async () => {
      try {
        const res = await searchKnowledge(token, queryText);
        setSimilarRecords(res.filter(r => (r.score ?? 0) >= 0.65).slice(0, 3));
      } catch (err) {
        console.error("Dynamic semantic search failed:", err);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [messages, session, token]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !inputMessage.trim() || sending) return;

    const userText = inputMessage;
    setInputMessage("");
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setSending(true);
    setError(null);

    try {
      const res = await submitStepResponse(token, sessionId, userText);
      setMessages(res.agent_chat_history || []);
    } catch (err: any) {
      setError(err.message || "Mesaj iletilemedi.");
    } finally {
      setSending(false);
    }
  }

  async function handleSendToPool() {
    if (!token || !sessionId || sendingPool) return;
    setSendingPool(true);
    setError(null);

    try {
      const record = await sendToPool(token, sessionId);
      onFinalized(record.record_id);
    } catch (err: any) {
      setError(err.message || "Problem Havuzuna aktarılamadı.");
    } finally {
      setSendingPool(false);
    }
  }

  async function handleResolve() {
    if (!token || resolving) return;
    setResolving(true);
    setError(null);

    try {
      const response = await agentResolve(token, sessionId);
      onFinalized(response.record_id);
    } catch (err: any) {
      console.error("Resolve error:", err);
      setError(err.message || "Problem sonlandırılamadı.");
    } finally {
      setResolving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">AI Kök Neden Danışmanı Bağlanıyor...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden max-w-6xl mx-auto w-full animate-fade-in gap-4 relative">
      {/* Modal for viewing clicked similar record */}
      {previewRecordId && (
        <div className="fixed inset-0 bg-[#030a10]/92 modal-backdrop-smooth gpu-accelerate flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="w-full max-w-4xl max-h-[90vh] bg-[#061320] border border-[#10293f] rounded-2xl flex flex-col overflow-hidden shadow-2xl p-4 gpu-accelerate">
            <div className="flex justify-end pb-2">
              <button 
                onClick={() => setPreviewRecordId(null)}
                className="p-1.5 hover:bg-red-950/30 text-[#4f7b92] hover:text-red-400 rounded-lg transition-all"
              >
                <X size={18} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <UnifiedRecordDetail recordId={previewRecordId} onClose={() => setPreviewRecordId(null)} />
            </div>
          </div>
        </div>
      )}

      {/* Top Bar with Title and Actions */}
      <div className="p-4 glass rounded-xl flex flex-wrap items-center justify-between shadow-lg gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-cyan-500/10 flex items-center justify-center text-[#00e5ff] border border-cyan-500/25 shrink-0">
            <Bot size={18} className="dot-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-[#e0f7fa]">Yeni Problem - Kök Neden Analizi (RCA)</h3>
            <p className="text-[10px] text-[#4f7b92] truncate max-w-[280px] sm:max-w-md">
              {session?.problem_description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Main Action: Send Root Cause to Problem Pool */}
          <button
            onClick={handleSendToPool}
            disabled={sendingPool || messages.length < 1}
            className="btn btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5 bg-gradient-to-r from-[#00e5ff] to-[#00b0ff] text-[#030a10] font-bold shadow-md shadow-cyan-500/10"
            title="Kök nedeni onaylayıp çözüm üretilmesi için Problem Havuzuna aktarır"
          >
            {sendingPool ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Inbox size={14} />
            )}
            <span>Kök Nedeni Problem Havuzuna Gönder</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Left Chat Area (2 cols), Right Dynamic Similar Cases (1 col) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 overflow-hidden">
        
        {/* Chat Box */}
        <div className="lg:col-span-2 flex flex-col bg-[#040c14] border border-[#10293f] rounded-xl overflow-hidden shadow-xl">
          {/* Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 flex flex-col">
            {/* System Welcome message strictly explaining Root Cause Focus */}
            <div className="flex gap-3 max-w-[88%] self-start">
              <div className="w-8 h-8 rounded-full bg-[#10293f] flex items-center justify-center text-xs text-[#00e5ff] border border-cyan-500/20 shrink-0">
                AI
              </div>
              <div className="p-3.5 glass rounded-r-xl rounded-bl-xl text-xs text-[#80deea] leading-relaxed shadow-sm space-y-2 border-l-2 border-l-[#00e5ff]">
                <div className="font-bold text-[#e0f7fa] flex items-center gap-1.5">
                  <Sparkles size={13} className="text-[#00e5ff]" />
                  <span>Kök Neden Analiz Danışmanı</span>
                </div>
                <p>
                  Merhaba! Bu ekranda sadece problemin altında yatan <strong>gerçek kök nedeni</strong> (5 Why / Ishikawa) bulmaya odaklanıyoruz. Doğrudan hızlı çözüm vermeyeceğim; öncelikle kök nedeni sorgulayıp netleştireceğiz. Kök nedeni bulduğumuzda yukarıdaki <strong>&quot;Kök Nedeni Problem Havuzuna Gönder&quot;</strong> butonuna basabilirsiniz.
                </p>
              </div>
            </div>

            {/* Dynamic chat history */}
            {messages.map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={idx}
                  className={`flex gap-3 max-w-[85%] ${
                    isUser ? "self-end flex-row-reverse" : "self-start"
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs shrink-0 border ${
                      isUser
                        ? "bg-gradient-to-br from-[#00e5ff] to-[#7c4dff] text-[#030a10] border-transparent"
                        : "bg-[#10293f] text-[#00e5ff] border-cyan-500/20"
                    }`}
                  >
                    {isUser ? <User size={13} /> : <Bot size={13} />}
                  </div>
                  <div
                    className={`p-3 text-xs leading-relaxed shadow-sm rounded-xl ${
                      isUser
                        ? "bg-[#0f2438] border border-cyan-500/20 text-[#e0f7fa] rounded-l-xl rounded-br-xl"
                        : "bg-[#061320] border border-[#10293f] text-[#80deea] rounded-r-xl rounded-bl-xl"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              );
            })}

            {/* Sending typing indicator */}
            {sending && (
              <div className="flex gap-3 max-w-[85%] self-start">
                <div className="w-8 h-8 rounded-full bg-[#10293f] flex items-center justify-center text-xs text-[#00e5ff] border border-cyan-500/20 shrink-0">
                  <Bot size={13} className="animate-spin text-cyan-400" />
                </div>
                <div className="p-3 bg-[#061320] border border-[#10293f] rounded-xl text-xs text-[#4f7b92] italic flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Kök neden analiz ediliyor...
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <form
            onSubmit={handleSendMessage}
            className="p-3 bg-[#061320] border-t border-[#10293f] flex items-center gap-2 shrink-0"
          >
            <input
              type="text"
              placeholder="Problemin detaylarını veya sorularınızı yazın..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={sending}
              className="flex-1 p-2.5 bg-[#030a10] border border-[#10293f] rounded-lg text-xs text-[#e0f7fa] placeholder-[#4f7b92] focus:border-[#00e5ff] transition"
            />
            <button
              type="submit"
              disabled={sending || !inputMessage.trim()}
              className="btn btn-primary p-2.5 rounded-lg shrink-0"
            >
              {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </form>
        </div>

        {/* Right: Dynamic Similarity Sidebar */}
        <div className="flex flex-col space-y-4 overflow-y-auto">
          <div className="p-4 glass rounded-xl border-[#10293f] flex-1">
            <div className="flex items-center gap-2 pb-2 border-b border-[#10293f]">
              <HelpCircle size={16} className="text-[#00e5ff]" />
              <h4 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-wider">
                Bak Benzer Problem Yaşanmış!
              </h4>
            </div>
            <p className="text-[10px] text-[#4f7b92] mt-2 leading-relaxed">
              Sohbet geliştikçe benzer vakalar burada listelenecektir.
            </p>

            {similarRecords.length === 0 ? (
              <div className="p-6 text-center text-[11px] text-[#4f7b92] italic mt-4 border border-dashed border-[#10293f] rounded-lg">
                Henüz tam eşleşen vaka bulunamadı.
              </div>
            ) : (
              <div className="space-y-3 mt-4">
                <span className="text-[10px] text-cyan-400 font-bold uppercase font-mono block">
                  İlgili Benzer Geçmiş Problemler ({similarRecords.length})
                </span>
                {similarRecords.map((rec) => (
                  <div
                    key={rec.id}
                    onClick={() => handleRecordClick(rec.id)}
                    className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl hover:border-[#00e5ff] hover:bg-[#061320] transition-all space-y-1.5 group cursor-pointer"
                  >
                    <div className="flex justify-between items-start gap-1">
                      <h5 className="text-xs font-semibold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors line-clamp-1">
                        {rec.title || "Başlıksız Kayıt"}
                      </h5>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-950/50 text-[#00e5ff] border border-cyan-500/20 font-mono">
                        %{rec.score ? (rec.score * 100).toFixed(0) : "0"} Benzer
                      </span>
                    </div>
                    {rec.root_cause && (
                      <p className="text-[10px] text-[#80deea] opacity-90 line-clamp-2 bg-[#061320] p-2 rounded border border-[#10293f]/40">
                        <strong className="text-[#00e5ff]">Kök Neden:</strong> {rec.root_cause}
                      </p>
                    )}
                    <div className="flex items-center justify-between text-[9px] text-[#4f7b92] pt-1">
                      <span>Birim: {rec.department || "Genel"}</span>
                      <span className="text-[#00e5ff] font-mono flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
                        İncele <ArrowRight size={10} />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
