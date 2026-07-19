"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { getSession, agentChat, agentResolve } from "@/lib/api";
import { SessionResponse } from "@/lib/types";
import { Send, CheckCircle, HelpCircle, Bot, User, Loader2 } from "lucide-react";


interface AgentChatProps {
  sessionId: string;
  onFinalized: (recordId: string) => void;
}

export default function AgentChat({ sessionId, onFinalized }: AgentChatProps) {
  const { token } = useAuth();
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadSession = useCallback(async () => {
    if (!token || !sessionId) return;
    try {
      const s = await getSession(token, sessionId);
      setSession(s);
      setMessages(s.agent_chat_history || []);
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

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !inputMessage.trim() || sending) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    setSending(true);

    // Optimistically add user message
    setMessages((prev) => [...prev, { role: "user", content: userText }]);

    try {
      const response = await agentChat(token, sessionId, userText);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
    } catch (err: any) {
      console.error("Send message error:", err);
      setError("Mesaj gönderilemedi. Lütfen tekrar deneyin.");
    } finally {
      setSending(false);
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
        <p className="text-sm font-mono">AI Danışman Bağlanıyor...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden max-w-4xl mx-auto w-full animate-fade-in">
      {/* Top Header */}
      <div className="p-4 glass rounded-t-xl flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-cyan-500/10 flex items-center justify-center text-[#00e5ff] border border-cyan-500/25">
            <Bot size={18} className="dot-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-[#e0f7fa]">Yapay Zeka Problem Çözme Danışmanı</h3>
            <p className="text-[10px] text-[#4f7b92] truncate max-w-[280px] sm:max-w-md">
              {session?.problem_description}
            </p>
          </div>
        </div>

        <button
          onClick={handleResolve}
          disabled={resolving || messages.length < 2}
          className="btn btn-primary text-xs py-2 px-3 flex items-center gap-1.5"
          title="Görüşmeyi kapatıp A3 Raporunu otomatik sentezler"
        >
          {resolving ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <CheckCircle size={14} />
          )}
          <span>Problemi Çöz ve Kapat</span>
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 bg-[#040c14] border-x border-[#10293f] p-4 overflow-y-auto space-y-4 flex flex-col">
        {/* System Welcome message */}
        <div className="flex gap-3 max-w-[85%] self-start">
          <div className="w-8 h-8 rounded-full bg-[#10293f] flex items-center justify-center text-xs text-[#00e5ff] border border-cyan-500/20 shrink-0">
            AI
          </div>
          <div className="p-3 glass rounded-r-xl rounded-bl-xl text-xs text-[#80deea] leading-relaxed shadow-sm">
            Merhaba! Ben sizin problem çözme danışmanınızım. Bu problemi çözebilmemiz için bana detayları anlatır mısınız? Önlem aldınız mı veya belirlediğiniz olası kök nedenler var mı? FMEA puanlarını da konuşabiliriz.
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
              Ajan analiz ediyor...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Message Area */}
      <div className="p-4 glass rounded-b-xl">
        <form onSubmit={handleSendMessage} className="flex gap-3">
          <input
            required
            type="text"
            placeholder="Mesajınızı yazın..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={sending || resolving}
            className="flex-1 bg-[#030a10] border border-[#10293f] text-[#e0f7fa] placeholder-[#4f7b92] text-sm py-2.5 px-4 rounded-lg focus:border-[#00e5ff] transition"
          />
          <button
            type="submit"
            disabled={sending || resolving || !inputMessage.trim()}
            className="btn btn-primary px-5 py-2.5"
          >
            <Send size={15} />
          </button>
        </form>
        {error && <p className="text-red-400 text-[11px] mt-2 text-center">{error}</p>}
      </div>
    </div>
  );
}
