"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { getSession, updateSession, poolChat, closePoolSession } from "@/lib/api";
import { SessionResponse, METHODOLOGY_LABELS } from "@/lib/types";
import { 
  ArrowLeft, 
  User, 
  Building2, 
  Calendar, 
  Send, 
  Sparkles, 
  CheckCircle, 
  FileText,
  Loader2
} from "lucide-react";

interface PoolSessionDetailProps {
  sessionId: string;
  onFinalized: (recordId: string) => void;
  onBack: () => void;
}

export default function PoolSessionDetail({ sessionId, onFinalized, onBack }: PoolSessionDetailProps) {
  const { token } = useAuth();
  const [session, setSession] = useState<SessionResponse | null>(null);
  
  // Metadata States
  const [assigneeName, setAssigneeName] = useState("");
  const [trackerName, setTrackerName] = useState("");
  const [department, setDepartment] = useState("Kalite");

  // Chat States
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputMsg, setInputMsg] = useState("");

  const [isBusy, setIsBusy] = useState(false);
  const [isSavingMeta, setIsSavingMeta] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function load() {
      if (!token || !sessionId) return;
      try {
        const data = await getSession(token, sessionId);
        setSession(data);
        setAssigneeName(data.assignee_name || "");
        setTrackerName(data.tracker_name || "");
        setDepartment(data.department || "Kalite");
        setMessages(data.agent_chat_history || []);
      } catch (err: any) {
        setError("Oturum detayları yüklenemedi.");
      }
    }
    load();
  }, [token, sessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">Çözüm Oturumu Yükleniyor...</p>
      </div>
    );
  }

  const handleUpdateMetadata = async () => {
    if (!token) return;
    setIsSavingMeta(true);
    try {
      const updated = await updateSession(token, sessionId, {
        assignee_name: assigneeName,
        tracker_name: trackerName,
        department: department
      });
      setSession(updated);
    } catch (err) {
      console.error("Failed to update metadata:", err);
    } finally {
      setIsSavingMeta(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !inputMsg.trim() || isBusy) return;

    const userMessage = inputMsg;
    setInputMsg("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsBusy(true);

    try {
      const updated = await poolChat(token, sessionId, userMessage);
      setSession(updated);
      setMessages(updated.agent_chat_history || []);
    } catch (err: any) {
      setError(err.message || "Mesaj gönderilemedi.");
    } finally {
      setIsBusy(false);
    }
  };

  const handleCloseSession = async () => {
    if (!token || isBusy) return;
    if (confirm("Bu problem çözüm sürecini kapatıp kalıcı A3 raporuna dönüştürmek istediğinize emin misiniz?")) {
      setIsBusy(true);
      setError(null);
      try {
        const response = await closePoolSession(token, sessionId);
        onFinalized(response.record_id);
      } catch (err: any) {
        setError(err.message || "Problem kapatılamadı.");
      } finally {
        setIsBusy(false);
      }
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-fade-in text-[#e0f7fa]">
      {/* Header and Back Button */}
      <div className="flex items-center justify-between border-b border-[#10293f] pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-[#0a1f33] rounded-lg text-[#4f7b92] hover:text-[#00e5ff] transition-all"
            title="Geri Dön"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-xl font-bold tracking-wide">
              {session.summary || "Problem Çözüm Paneli"}
            </h2>
            <p className="text-xs text-[#4f7b92] mt-0.5 font-mono">
              METODOLOJİ: {METHODOLOGY_LABELS[session.methodology]}
            </p>
          </div>
        </div>
        <button
          onClick={handleCloseSession}
          disabled={isBusy}
          className="px-4 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white text-xs font-bold rounded-lg flex items-center gap-1.5 transition-all shadow-md shadow-emerald-500/10"
        >
          <CheckCircle className="w-4 h-4" />
          <span>Çözümü Onayla & Kapat</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-xl text-xs text-red-400">
          {error}
        </div>
      )}

      {/* --- Top Section: Metadata Assignment Inputs --- */}
      <div className="p-5 bg-[#061320] border border-[#10293f] rounded-2xl grid grid-cols-1 md:grid-cols-3 gap-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[1.5px] bg-[#10293f]" />

        {/* Department Selection */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" />
            Atanacak Birim / Departman
          </label>
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            onBlur={handleUpdateMetadata}
            className="w-full p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition-all"
          >
            <option value="Üretim">Üretim</option>
            <option value="Lojistik">Lojistik</option>
            <option value="Kalite">Kalite</option>
            <option value="Bilgi İşlem">Bilgi İşlem</option>
            <option value="Finans">Finans</option>
          </select>
        </div>

        {/* Assignee Name */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            Takip Edecek Sorumlu (Assignee)
          </label>
          <input
            type="text"
            value={assigneeName}
            onChange={(e) => setAssigneeName(e.target.value)}
            onBlur={handleUpdateMetadata}
            placeholder="İsim soyisim girin..."
            className="w-full p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] placeholder-[#4f7b92] transition-all"
          />
        </div>

        {/* Tracker / Supervisor Name */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            Denetçi / Takipçi (Tracker)
          </label>
          <input
            type="text"
            value={trackerName}
            onChange={(e) => setTrackerName(e.target.value)}
            onBlur={handleUpdateMetadata}
            placeholder="İsim soyisim veya birim lideri..."
            className="w-full p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] placeholder-[#4f7b92] transition-all"
          />
        </div>
      </div>

      {/* --- Split Screen Content --- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        
        {/* Left Screen: Dynamic Problem Report */}
        <div className="bg-[#061320] border border-[#10293f] rounded-2xl p-5 shadow-xl flex flex-col space-y-4 max-h-[600px] overflow-y-auto relative">
          <h3 className="text-sm font-bold text-[#80deea] border-b border-[#10293f] pb-2 flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#00e5ff]" />
            Dinamik Problem Analiz Raporu (A3)
          </h3>

          <div className="space-y-4 text-xs">
            {/* Description */}
            <div className="space-y-1.5">
              <span className="text-[#4f7b92] uppercase tracking-wider font-mono text-[9px]">Problem Tanımı</span>
              <p className="bg-[#030a10] p-3 rounded-xl border border-[#10293f]/50 leading-relaxed">
                {session.problem_description}
              </p>
            </div>

            {/* RCA Step Answers */}
            <div className="space-y-2">
              <span className="text-[#4f7b92] uppercase tracking-wider font-mono text-[9px]">Kök Neden Analizi Adımları</span>
              <div className="space-y-2.5">
                {Object.entries(session.answers || {}).map(([stepKey, answerText]) => (
                  <div key={stepKey} className="p-3 bg-[#0a1f33]/40 border border-[#10293f]/50 rounded-xl space-y-1">
                    <div className="text-[10px] font-bold text-cyan-400 uppercase font-mono tracking-wide">
                      {stepKey.replace(/_/g, " ")}
                    </div>
                    <p className="leading-relaxed opacity-95 text-[#e0f7fa]">{answerText as string}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Screen: AI Agent Resolution Chat */}
        <div className="bg-[#061320] border border-[#10293f] rounded-2xl flex flex-col h-[600px] shadow-xl overflow-hidden relative">
          {/* Chat Header */}
          <div className="p-4 bg-[#0a1f33]/60 border-b border-[#10293f] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 dot-pulse" />
              <span className="text-xs font-bold text-[#80deea]">AI Çözüm Ajanı</span>
            </div>
            <span className="text-[9px] px-2 py-0.5 rounded bg-[#10293f] text-[#4f7b92] font-mono uppercase">
              active-resolution
            </span>
          </div>

          {/* Messages view */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 scrollbar-thin bg-[#030a10]/50">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-3 p-6">
                <Sparkles className="w-8 h-8 text-[#00e5ff] opacity-60 animate-bounce" />
                <div>
                  <h4 className="text-xs font-bold text-[#e0f7fa]">Problem Çözüm Ajanı Hazır</h4>
                  <p className="text-[11px] text-[#4f7b92] max-w-xs mt-1">
                    Kök neden analizine uygun kalıcı düzeltici eylemleri planlamak için ajana soru sorabilir veya planlarınızı iletebilirsiniz.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((m, idx) => {
                const isUser = m.role === "user";
                return (
                  <div
                    key={idx}
                    className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}
                  >
                    <div
                      className={`max-w-[85%] p-3 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? "bg-gradient-to-br from-[#7c4dff] to-[#5e35b1] text-white rounded-tr-none"
                          : "bg-[#0a1f33] border border-[#10293f] text-[#e0f7fa] rounded-tl-none"
                      }`}
                    >
                      <p className="whitespace-pre-line">{m.content}</p>
                    </div>
                  </div>
                );
              })
            )}
            {isBusy && (
              <div className="flex justify-start">
                <div className="p-3 bg-[#0a1f33] border border-[#10293f] rounded-2xl rounded-tl-none flex items-center gap-2 text-[#80deea] text-xs">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00e5ff]" />
                  <span>Ajan yazıyor...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Message form */}
          <form onSubmit={handleSendMessage} className="p-3 bg-[#061320] border-t border-[#10293f] flex items-center gap-2">
            <input
              type="text"
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              disabled={isBusy}
              placeholder="Çözüm planınızı yazın veya ajana danışın..."
              className="flex-1 p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] placeholder-[#4f7b92] focus:outline-none"
            />
            <button
              type="submit"
              disabled={isBusy || !inputMsg.trim()}
              className="p-2.5 bg-[#00e5ff] text-[#030a10] hover:bg-[#00b2cc] disabled:bg-[#10293f] disabled:text-[#4f7b92] rounded-xl transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
