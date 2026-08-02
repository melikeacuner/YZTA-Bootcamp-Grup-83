"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  getSession,
  submitStepResponse,
  requestFollowUp,
  goBackStep,
  completeSession,
  createRecord,
  agentResolve,
  agentChat
} from "@/lib/api";
import { METHODOLOGY_STEPS, MIN_STEPS_TO_COMPLETE } from "@/lib/methodology-steps";
import { METHODOLOGY_LABELS, SessionResponse } from "@/lib/types";
import { AlertCircle, HelpCircle, ArrowLeft, ArrowRight, Loader2, Sparkles, X } from "lucide-react";

interface MethodologyChatProps {
  sessionId: string;
  onFinalized: (recordId: string) => void;
}

export default function MethodologyChat({ sessionId, onFinalized }: MethodologyChatProps) {
  const { token } = useAuth();
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [editingMsgIndex, setEditingMsgIndex] = useState<number | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Completion Form States
  const [title, setTitle] = useState("");
  const [lessonsLearned, setLessonsLearned] = useState("");
  const [rootCause, setRootCause] = useState("");
  const [correctiveActions, setCorrectiveActions] = useState("");
  const [department, setDepartment] = useState("Üretim");
  const [industry, setIndustry] = useState("İmalat");
  const [category, setCategory] = useState("Kalite Hatası");
  const [severity, setSeverity] = useState(5);
  const [occurrence, setOccurrence] = useState(4);
  const [detection, setDetection] = useState(3);
  const [yokoten, setYokoten] = useState(false);

  // Modal and Confirmation Guard States
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmedAssignee, setConfirmedAssignee] = useState("");
  const [confirmedStatus, setConfirmedStatus] = useState<"todo" | "in_progress">("todo");
  const [statusGuardError, setStatusGuardError] = useState<string | null>(null);

  async function handleConfirmAndCreateRecord() {
    if (!token || isBusy) return;
    if (confirmedStatus === "in_progress" && !confirmedAssignee.trim()) {
      setStatusGuardError("Problem kaydını 'Devam Edenler'e taşımak için önce bir sorumlu atanması zorunludur.");
      return;
    }
    setStatusGuardError(null);
    setIsBusy(true);
    setError(null);

    try {
      if (session?.status === "active") {
        await completeSession(token, sessionId);
      }

      const answersMap = session?.answers || {};
      const record = await createRecord(token, {
        session_id: sessionId,
        title: title || session?.summary || session?.problem_description.slice(0, 50) || "Problem Kaydı",
        lessons_learned: lessonsLearned || "Kök neden tespiti yapıldı. Çözüm planlanmaktadır.",
        root_cause: rootCause || Object.values(answersMap).pop() as string || "Kök neden belirlendi.",
        corrective_actions: correctiveActions || undefined,
        industry,
        department,
        problem_category: category,
        severity,
        occurrence,
        detection,
        yokoten_applied: yokoten
      });

      if (confirmedAssignee.trim() || confirmedStatus) {
        try {
          const { listTasks, updateTask } = await import("@/lib/api");
          let taskList = await listTasks(token, { problem_record_id: record.id });
          if (!taskList || taskList.length === 0) {
            taskList = await listTasks(token, { session_id: sessionId });
          }
          if (taskList && taskList.length > 0) {
            await updateTask(token, taskList[0].id, {
              assignee_name: confirmedAssignee.trim() || undefined,
              status: confirmedStatus
            });
          }
        } catch (taskErr) {
          console.error("Task status update error:", taskErr);
        }
      }

      setShowConfirmModal(false);
      onFinalized(record.id);
    } catch (err: any) {
      setError(err.message || "Problem kaydı oluşturulamadı.");
    } finally {
      setIsBusy(false);
    }
  }

  const loadSession = useCallback(async () => {
    if (!token || !sessionId) return;
    try {
      const data = await getSession(token, sessionId);
      setSession(data);
    } catch (err: any) {
      setError("Oturum yüklenemedi.");
    }
  }, [token, sessionId]);

  useEffect(() => {
    setError(null);
    loadSession();
  }, [loadSession, sessionId]);

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">Metodoloji Yükleniyor...</p>
      </div>
    );
  }

  // Get current step configuration
  const steps = METHODOLOGY_STEPS[session.methodology] || [];
  const currentStepDef = steps[session.current_step];
  const minSteps = MIN_STEPS_TO_COMPLETE[session.methodology] || 3;

  const stepData = (session.step_data as Record<string, any> | undefined) || {};
  const aiSynthesizedRoot = stepData.ai_synthesized_root_cause || session.ai_synthesized_root_cause;

  // Safe extraction of answers for mapping
  const answersMap = session.answers || {};
  const answeredCount = Object.keys(answersMap).length;
  const canComplete = session.status === "active" && answeredCount >= minSteps;

  async function handleSubmitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !answer.trim() || isBusy) return;

    setIsBusy(true);
    setError(null);
    try {
      const updated = await submitStepResponse(token, sessionId, answer);
      setSession(updated);
      setAnswer("");
    } catch (err: any) {
      setError(err.message || "Yanıt gönderilemedi");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleGoBack() {
    if (!token || isBusy) return;
    setIsBusy(true);
    setError(null);
    try {
      const updated = await goBackStep(token, sessionId);
      setSession(updated);
      setAnswer("");
    } catch (err: any) {
      setError(err.message || "Geri gidilemedi.");
    } finally {
      setIsBusy(false);
    }
  }

  const getContextualSuggestions = () => {
    const desc = (session.problem_description || "").toLowerCase();
    const dept = (session.department || "").toLowerCase();
    const suggestions: { label: string; text: string }[] = [];

    // 1. Üretim / Makine / Kalıp / Robotik
    if (dept.includes("üretim") || desc.includes("cnc") || desc.includes("robot") || desc.includes("makine") || desc.includes("kalıp") || desc.includes("enjeksiyon") || desc.includes("tork")) {
      if (desc.includes("cnc") || desc.includes("spindle") || desc.includes("rulman")) {
        suggestions.push({
          label: "💡 Rulman Yağsızlaşması",
          text: "Otomatik greslama selonoid valfinin tıkanması nedeniyle rulman yatağında gres kuruma yapmış."
        });
        suggestions.push({
          label: "💡 Spindle Devir Sapması",
          text: "Yüksek devirde kesici mil eksen titreşim alarmı veriyor ve tolerans kayıyor."
        });
      } else if (desc.includes("enjeksiyon") || desc.includes("çapak") || desc.includes("plastik")) {
        suggestions.push({
          label: "💡 Hidrolik Valf Basınç Düşüşü",
          text: "Hidrolik kapama valfinde aşınma sonucu kalıp kapama basıncı düşmüş."
        });
        suggestions.push({
          label: "💡 Eriyik Sıcaklık Sapması",
          text: "Kalıp sıcaklık kontrol cihazında ayar sapması nedeniyle eriyik sıcaklığı yüksek kalmış."
        });
      } else {
        suggestions.push({
          label: "💡 Mekanik Aşınma & Sürtünme",
          text: "Motor redüktör dişli boşluğundaki aşınma nedeniyle mekanik sürtünme artmış."
        });
        suggestions.push({
          label: "💡 Pnömatik Basınç Düşüşü",
          text: "Regülatör filtresinin tıkanması anlık pnömatik basıncı düşürüyor."
        });
      }
    }
    // 2. Bilgi İşlem / Yazılım / Veritabanı / API
    else if (dept.includes("bilgi") || dept.includes("yazılım") || desc.includes("api") || desc.includes("db") || desc.includes("database") || desc.includes("sorgu") || desc.includes("mikroservis")) {
      suggestions.push({
        label: "💡 Eksik Veritabanı İndeksi",
        text: "Sorgu atılan tabloda eksik indeks nedeniyle Sequential Scan yapılıyor ve yanıt süresi uzuyor."
      });
      suggestions.push({
        label: "💡 Bağlantı Havuzu Tıkanması",
        text: "Yoğun saatlerde veritabanı max connection limitine ulaşılıyor ve zaman aşımı oluşuyor."
      });
    }
    // 3. Lojistik / Depo / Sensör / Soğuk Zincir / Konveyör
    else if (dept.includes("lojistik") || desc.includes("depo") || desc.includes("sensör") || desc.includes("soğuk") || desc.includes("konveyör")) {
      if (desc.includes("soğuk") || desc.includes("sıcaklık") || desc.includes("sensör")) {
        suggestions.push({
          label: "💡 PT100 Sensör Oksitlenmesi",
          text: "Sıcaklık sensör uçlarının nem korozyonuna uğraması sonucu direnç değeri kaymış."
        });
        suggestions.push({
          label: "💡 Kondanser Filtre Tıkanması",
          text: "Soğutma grubu kondanser filtrelerinin tozlanması ısı transferini engelliyor."
        });
      } else {
        suggestions.push({
          label: "💡 Konveyör Kasnak Aşınması",
          text: "Tahrik kasnağındaki kauçuk kaplama yıpranarak bandın kaçırmasına sebep oluyor."
        });
        suggestions.push({
          label: "💡 Gergi Tamburu Sapması",
          text: "Bant gergi tamburu ayarsızlığı nedeniyle bant sıkışması yaşanıyor."
        });
      }
    }
    // 4. Finans / ERP / Fatura
    else if (dept.includes("finans") || desc.includes("fatura") || desc.includes("erp") || desc.includes("ocr") || desc.includes("kur")) {
      suggestions.push({
        label: "💡 Kur Servisi Timeout Sapması",
        text: "Döviz kurları çekilirken API timeout durumunda varsayılan kur değerinin atanması."
      });
      suggestions.push({
        label: "💡 OCR Fatura Algoritma Uyuşmazlığı",
        text: "Tarama çözünürlüğü ve yazı karakteri uyuşmazlığı nedeniyle OCR eşleştirme hatası veriyor."
      });
    }
    // 5. Kalite / Boyahane / Ölçüm
    else if (dept.includes("kalite") || desc.includes("boya") || desc.includes("mikron") || desc.includes("ölçüm")) {
      suggestions.push({
        label: "💡 Voltaj Kaskad Kayması",
        text: "Elektrostatik tabanca yüksek voltaj kaskad ünitesindeki yıpranma nedeniyle mikron kalınlığı kaymış."
      });
      suggestions.push({
        label: "💡 Kalibrasyon Cihaz Sapması",
        text: "Ölçüm komparatörü sıfırlama kalibrasyonu standart dışı kalmış."
      });
    }

    return suggestions;
  };

  const contextualSuggestions = getContextualSuggestions();


  async function handleComplete() {
    if (!token || isBusy) return;
    setIsBusy(true);
    setError(null);
    try {
      const updated = await completeSession(token, sessionId);
      setSession(updated);
    } catch (err: any) {
      setError(err.message || "Oturum sonlandırılamadı.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAutoResolve() {
    if (!token || isBusy) return;
    setIsBusy(true);
    setError(null);
    try {
      const record = await agentResolve(token, sessionId);
      onFinalized(record.record_id);
    } catch (err: any) {
      setError(err.message || "Otomatik sentezleme başarısız oldu.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateRecord(e: React.FormEvent) {
    e.preventDefault();
    if (!token || isBusy) return;
    setIsBusy(true);
    setError(null);

    try {
      const record = await createRecord(token, {
        session_id: sessionId,
        title,
        lessons_learned: lessonsLearned,
        root_cause: rootCause || undefined,
        corrective_actions: correctiveActions || undefined,
        industry,
        department,
        problem_category: category,
        severity,
        occurrence,
        detection,
        yokoten_applied: yokoten
      });
      onFinalized(record.id);
    } catch (err: any) {
      setError(err.message || "A3 Raporu oluşturulamadı.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSendAgentChat(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!token || !answer.trim() || isBusy) return;

    const userMsg = answer.trim();
    const rewindIdx = editingMsgIndex;
    setAnswer("");
    setEditingMsgIndex(null);
    setIsBusy(true);
    setError(null);

    let baseHistory = session?.agent_chat_history || [];
    if (rewindIdx !== null && rewindIdx >= 0 && rewindIdx < baseHistory.length) {
      baseHistory = baseHistory.slice(0, rewindIdx);
    }

    const updatedHistory = [...baseHistory, { role: "user", content: userMsg }];
    setSession(prev => prev ? { ...prev, agent_chat_history: updatedHistory } : null);

    try {
      const res = await agentChat(token, sessionId, userMsg, rewindIdx ?? undefined);
      setSession(prev => prev ? {
        ...prev,
        agent_chat_history: [...updatedHistory, { role: "assistant", content: res.reply }]
      } : null);
    } catch (err: any) {
      console.error("Agent chat error:", err);
      try {
        const stepUpdated = await submitStepResponse(token, sessionId, userMsg);
        setSession(stepUpdated);
      } catch (stepErr: any) {
        setError(err.message || "AI Ajanı yanıt veremedi.");
      }
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Session Title Header */}
      <div className="flex items-center justify-between p-4 bg-[#061320] border border-[#10293f] rounded-xl shadow-lg">
        <div className="flex items-center gap-3">
          <span className="text-xs px-2.5 py-1 rounded bg-[#10293f] text-[#00e5ff] uppercase font-mono font-semibold flex items-center gap-1.5">
            <Sparkles size={12} className="text-[#00e5ff] animate-pulse" />
            AI Agent Kök Neden Analizi ({METHODOLOGY_LABELS[session.methodology as keyof typeof METHODOLOGY_LABELS] || session.methodology})
          </span>
          <p className="text-xs text-[#4f7b92] truncate max-w-xs md:max-w-md">
            {session.problem_description}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {session.status === "active" && (
            <button
              type="button"
              onClick={() => {
                const synth = aiSynthesizedRoot || rootCause || (Object.values(answersMap).pop() as string) || session.problem_description;
                setRootCause(synth);
                if (!title) {
                  setTitle(`Problem: ${session.problem_description.slice(0, 40)}...`);
                }
                setShowConfirmModal(true);
              }}
              className="px-3.5 py-1.5 bg-gradient-to-r from-[#00e5ff] to-[#7c4dff] text-[#030a10] font-bold rounded-lg text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 hover:scale-105 transition-all cursor-pointer shrink-0"
            >
              <Sparkles size={13} />
              <span>Oturumu Sonlandır & Havuza Gönder</span>
            </button>
          )}
          <span className={`text-[10px] px-2 py-0.5 rounded-full ${session.status === "active" ? "bg-green-500/10 text-green-400 font-semibold" : "bg-cyan-500/10 text-cyan-400"
            }`}>
            {session.status === "active" ? "Canlı AI Oturumu" : "Tamamlandı"}
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Side: Live AI Agent Chat */}
        <div className="md:col-span-2 space-y-4">
          {/* Live AI Agent Chat Messages */}
          {session.agent_chat_history && session.agent_chat_history.length > 0 ? (
            <div className="space-y-3.5 max-h-[500px] overflow-y-auto pr-1">
              {session.agent_chat_history.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 p-4 rounded-xl text-xs leading-relaxed transition-all ${
                    msg.role === "assistant"
                      ? "bg-[#061320] border border-[#00e5ff]/30 text-[#e0f7fa] shadow-md shadow-cyan-500/5"
                      : "bg-gradient-to-r from-blue-900/40 to-indigo-900/40 border border-blue-500/30 text-white ml-6"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-7 h-7 rounded-full bg-cyan-950 border border-[#00e5ff]/50 flex items-center justify-center shrink-0">
                      <Sparkles className="w-3.5 h-3.5 text-[#00e5ff] animate-pulse" />
                    </div>
                  )}
                  <div className="flex-1 space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className={msg.role === "assistant" ? "text-[#00e5ff] font-bold" : "text-blue-300 font-bold"}>
                        {msg.role === "assistant" ? "AI Kök Neden Uzmanı" : "Siz"}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.role === "user" && (
                      <button
                        type="button"
                        onClick={() => {
                          setAnswer(msg.content);
                          setEditingMsgIndex(idx);
                        }}
                        className="text-[10px] font-mono text-cyan-400/70 hover:text-cyan-300 underline flex items-center gap-1 mt-1"
                      >
                        ✏️ Bu Cevabı Düzenle
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Fallback Steps History */
            <div className="space-y-3">
              {steps.map((step, idx) => {
                const ans = answersMap[step.name] || answersMap[idx.toString()];
                if (!ans) return null;
                return (
                  <div key={step.name} className="p-4 bg-[#061320] border border-[#10293f] rounded-lg space-y-2 relative group">
                    <div className="flex justify-between items-center">
                      <p className="text-[11px] font-semibold text-[#80deea] uppercase font-mono">
                        {step.prompt}
                      </p>
                      <button
                        type="button"
                        onClick={() => setAnswer(ans)}
                        className="text-[10px] text-cyan-400/80 hover:text-cyan-300 font-mono flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ✏️ Düzenle
                      </button>
                    </div>
                    <p className="text-xs text-[#e0f7fa] leading-relaxed">{ans}</p>
                  </div>
                );
              })}
            </div>
          )}

          {/* Active AI Agent Interactive Input */}
          {session.status === "active" && (
            <form onSubmit={handleSendAgentChat} className="p-4 bg-[#061320] border border-[#10293f] rounded-xl space-y-3 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />

              {/* Contextual Copilot Smart Suggestions Chips */}
              {contextualSuggestions.length > 0 && (
                <div className="space-y-1.5 border-b border-[#10293f]/60 pb-2.5">
                  <div className="flex items-center gap-1.5 text-[10px] font-semibold text-cyan-300 uppercase tracking-wider font-mono">
                    <Sparkles className="w-3 h-3 text-cyan-400" />
                    <span>Akıllı Copilot İpuçları (Kontekstual Öneriler):</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {contextualSuggestions.map((sug, sIdx) => (
                      <button
                        key={sIdx}
                        type="button"
                        onClick={() => setAnswer(sug.text)}
                        className="text-[10px] bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-500/30 text-[#80deea] hover:text-white px-2.5 py-1 rounded-md transition-colors text-left font-mono"
                      >
                        {sug.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex flex-col gap-2 pt-1">
                <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                  <span>AI Ajanına Cevap Verin Veya Detay Belirtin:</span>
                </label>

                <textarea
                  required
                  rows={3}
                  placeholder="AI Ajanının sorularına yanıt verin veya yukarıdaki akıllı ipuçlarına tıklayın..."
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full p-3 bg-[#030a10] border border-[#10293f] rounded-lg text-[#e0f7fa] placeholder-[#4f7b92] text-xs focus:border-[#00e5ff]"
                />
              </div>

              {session.circular_logic_warning && (
                <div className="p-3.5 bg-yellow-950/20 border border-yellow-500/30 rounded-lg text-yellow-400 text-xs flex items-center gap-2 animate-pulse">
                  <AlertCircle size={14} />
                  <span>Döngüsel Mantık Uyarısı: Girdiğiniz yanıt önceki nedenlerle çok benziyor veya tekrara giriyor.</span>
                </div>
              )}

              <div className="flex justify-between items-center pt-1">
                <span className="text-[10px] text-[#4f7b92] font-mono">AI Agent Canlı Sohbet Oturumu</span>
                <button
                  type="submit"
                  disabled={isBusy || !answer.trim()}
                  className="btn btn-primary text-xs py-2 px-5 flex items-center gap-2 shadow-md shadow-cyan-500/10 hover:shadow-cyan-500/20"
                >
                  {isBusy ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                  <span>AI Ajanına Gönder</span>
                </button>
              </div>
            </form>
          )}

          {/* Dynamic AI Synthesized Root Cause Proposal Card (Always visible when active) */}
          {session.status === "active" && (
            <div className="p-4 bg-[#061320] border border-[#10293f] rounded-xl space-y-3 shadow-lg relative overflow-hidden animate-fade-in">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />
              
              <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-lg text-xs space-y-1.5">
                <span className="font-bold text-[#00e5ff] flex items-center gap-1.5 uppercase font-mono tracking-wider text-[10px]">
                  <Sparkles size={13} className="animate-pulse text-[#00e5ff]" />
                  AI Tarafından Sentezlenen Kök Neden Hipotezi / Durumu
                </span>
                <p className="text-[#e0f7fa] font-medium leading-relaxed">
                  {aiSynthesizedRoot || rootCause || (Object.values(answersMap).pop() as string) || "AI Ajanı ile görüşme devam ediyor. Kök nedene ulaşıldığında aşağıdaki butona basarak oturumu sonlandırabilirsiniz."}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const synth = aiSynthesizedRoot || rootCause || (Object.values(answersMap).pop() as string) || session.problem_description;
                    setRootCause(synth);
                    if (!title) {
                      setTitle(`Problem: ${session.problem_description.slice(0, 40)}...`);
                    }
                    setShowConfirmModal(true);
                  }}
                  className="w-full py-2.5 bg-gradient-to-r from-[#00e5ff] to-[#7c4dff] text-[#030a10] font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/10 hover:shadow-cyan-500/25 transition-all"
                >
                  <Sparkles size={14} />
                  <span>Kök Nedeni Onayla ve Havuza Gönder</span>
                </button>

                <button
                  onClick={handleComplete}
                  disabled={isBusy}
                  className="w-full py-2.5 bg-[#0a1f33] border border-[#10293f] text-[#80deea] hover:text-white rounded-lg text-xs hover:bg-[#10293f] transition-all font-medium"
                >
                  Manuel Detaylı A3 Raporu Doldur
                </button>
              </div>
            </div>
          )}

          {/* Modal: Root Cause Confirmation & Task Creation */}
          {showConfirmModal && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
              <div className="w-full max-w-lg bg-[#061320] border border-[#10293f] rounded-2xl overflow-hidden shadow-2xl relative space-y-4 p-6">
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />

                <div className="flex items-center justify-between border-b border-[#10293f] pb-3">
                  <div>
                    <h3 className="font-bold text-sm text-[#e0f7fa]">Problem Kaydı Onayı & DevOps Ataması</h3>
                    <p className="text-[10px] text-[#4f7b92] font-mono mt-0.5">KAYIT ID: {sessionId}</p>
                  </div>
                  <button onClick={() => setShowConfirmModal(false)} className="text-[#4f7b92] hover:text-red-500">
                    <X size={16} />
                  </button>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg space-y-1">
                    <span className="text-[9px] text-[#4f7b92] uppercase font-mono">Tahmin Edilen Departman</span>
                    <p className="font-semibold text-cyan-400">{department || "Üretim"}</p>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="font-semibold text-[#80deea]">Problem Başlığı *</label>
                    <input
                      type="text"
                      value={title || `Problem: ${session.problem_description.slice(0, 40)}`}
                      onChange={(e) => setTitle(e.target.value)}
                      className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="font-semibold text-[#80deea]">Kök Neden *</label>
                    <textarea
                      rows={2}
                      value={rootCause}
                      onChange={(e) => setRootCause(e.target.value)}
                      className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="font-semibold text-[#80deea]">Otomatik Keywords / Tags</label>
                    <div className="flex flex-wrap gap-1.5 p-2 bg-[#030a10] border border-[#10293f] rounded text-[10px] text-cyan-400 font-mono">
                      {(session.tags || ["problem", session.methodology, "root-cause"]).map((t, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-[#10293f] text-[#80deea]">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[#10293f]">
                    <div className="flex flex-col gap-1">
                      <label className="font-semibold text-[#80deea]">DevOps Aksiyon Durumu</label>
                      <select
                        value={confirmedStatus}
                        onChange={(e) => setConfirmedStatus(e.target.value as "todo" | "in_progress")}
                        className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                      >
                        <option value="todo">Yapılacaklar (Default)</option>
                        <option value="in_progress">Devam Edenler</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="font-semibold text-[#80deea]">Sorumlu Kişi (Assignee)</label>
                      <input
                        type="text"
                        placeholder="İsim soyisim..."
                        value={confirmedAssignee}
                        onChange={(e) => {
                          setConfirmedAssignee(e.target.value);
                          if (statusGuardError) setStatusGuardError(null);
                        }}
                        className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                      />
                    </div>
                  </div>

                  {(statusGuardError || error) && (
                    <div className="p-2.5 bg-red-950/30 border border-red-500/40 rounded-lg text-red-400 text-[11px] flex items-center gap-2 font-medium">
                      <AlertCircle size={14} />
                      <span>{statusGuardError || error}</span>
                    </div>
                  )}

                  {/* Interactive FMEA Risk Analysis Approval */}
                  <div className="p-3 bg-[#030a10] border border-cyan-500/20 rounded-lg space-y-2">
                    <p className="text-[10px] font-bold text-cyan-400 uppercase font-mono">
                      FMEA Risk Analizi Değerlendirmesi & Onayı
                    </p>
                    <p className="text-[9px] text-[#4f7b92]">
                      Geçmiş vakalara göre önerilen değerler aşağıdaki gibidir. Lütfen inceleyip onaylayın.
                    </p>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="flex flex-col">
                        <span className="text-[8px] text-[#4f7b92]">Şiddet (S)</span>
                        <input
                          type="number"
                          min={1}
                          max={10}
                          value={severity}
                          onChange={(e) => setSeverity(Number(e.target.value))}
                          className="p-1 text-center bg-[#061320] border border-[#10293f] rounded text-xs mt-1 text-[#e0f7fa]"
                        />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[8px] text-[#4f7b92]">Sıklık (O)</span>
                        <input
                          type="number"
                          min={1}
                          max={10}
                          value={occurrence}
                          onChange={(e) => setOccurrence(Number(e.target.value))}
                          className="p-1 text-center bg-[#061320] border border-[#10293f] rounded text-xs mt-1 text-[#e0f7fa]"
                        />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[8px] text-[#4f7b92]">Tespit (D)</span>
                        <input
                          type="number"
                          min={1}
                          max={10}
                          value={detection}
                          onChange={(e) => setDetection(Number(e.target.value))}
                          className="p-1 text-center bg-[#061320] border border-[#10293f] rounded text-xs mt-1 text-[#e0f7fa]"
                        />
                      </div>
                    </div>
                    <div className="text-[9px] text-right text-cyan-500 font-mono">
                      RPN: {severity * occurrence * detection}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 pt-2 border-t border-[#10293f]">
                  <button
                    type="button"
                    onClick={handleConfirmAndCreateRecord}
                    disabled={isBusy}
                    className="btn btn-primary flex-1 py-3 text-xs font-bold"
                  >
                    {isBusy ? "Kaydediliyor..." : "Kök Nedeni Onayla & Kaydı Oluştur"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowConfirmModal(false)}
                    className="btn btn-secondary py-3 text-xs"
                  >
                    İptal
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Side: A3 Synthesis Form (visible when session is completed) */}
        <div className="md:col-span-1">
          {session.status === "completed" ? (
            <form onSubmit={handleCreateRecord} className="p-5 bg-[#061320] border border-[#10293f] rounded-xl space-y-4 relative overflow-hidden animate-fade-in">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />

              <h3 className="text-sm font-semibold text-[#e0f7fa]">A3 Belgesini Tamamla</h3>
              <p className="text-[11px] text-[#4f7b92]">Analiz bitti! Şimdi veritabanı ve A3 çıktısı için detayları doldurun.</p>

              <button
                type="button"
                onClick={handleAutoResolve}
                disabled={isBusy}
                className="w-full py-2 bg-cyan-500/10 border border-cyan-500/30 text-[#00e5ff] rounded text-xs flex items-center justify-center gap-1.5 hover:bg-cyan-500/20 transition-all font-semibold"
              >
                <Sparkles size={12} />
                <span>AI ile Otomatik Sentezle ve Kapat</span>
              </button>

              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-[#10293f]/30"></div>
                <span className="flex-shrink mx-2 text-[#4f7b92] text-[9px]">Veya Manuel</span>
                <div className="flex-grow border-t border-[#10293f]/30"></div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-[#80deea]">1. Rapor Başlığı</label>
                <input
                  required
                  type="text"
                  placeholder="Kısa başlık..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="p-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-[#80deea]">2. Kök Neden</label>
                <textarea
                  rows={2}
                  placeholder="Kök neden tespiti..."
                  value={rootCause}
                  onChange={(e) => setRootCause(e.target.value)}
                  className="p-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-[#80deea]">3. Kalıcı Eylemler</label>
                <textarea
                  rows={2}
                  placeholder="Alınan aksiyonlar..."
                  value={correctiveActions}
                  onChange={(e) => setCorrectiveActions(e.target.value)}
                  className="p-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-[#80deea]">4. Öğrenilen Dersler</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Elde edilen kazanımlar..."
                  value={lessonsLearned}
                  onChange={(e) => setLessonsLearned(e.target.value)}
                  className="p-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] text-[#4f7b92]">Departman</label>
                  <select value={department} onChange={(e) => setDepartment(e.target.value)} className="p-1.5 bg-[#030a10] border border-[#10293f] rounded text-[11px]">
                    <option value="Üretim">Üretim</option>
                    <option value="Lojistik">Lojistik</option>
                    <option value="Kalite">Kalite</option>
                    <option value="Bilgi İşlem">Bilgi İşlem</option>
                    <option value="Finans">Finans</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] text-[#4f7b92]">Kategori</label>
                  <select value={category} onChange={(e) => setCategory(e.target.value)} className="p-1.5 bg-[#030a10] border border-[#10293f] rounded text-[11px]">
                    <option value="Kalite Hatası">Kalite Hatası</option>
                    <option value="Makine Arızası">Makine Arızası</option>
                    <option value="İş Güvenliği">İş Güvenliği</option>
                    <option value="Lojistik Gecikme">Lojistik Gecikme</option>
                    <option value="Diğer">Diğer</option>
                  </select>
                </div>
              </div>

              {/* FMEA Assessment */}
              <div className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg space-y-2">
                <p className="text-[10px] font-semibold text-cyan-400">FMEA Risk Puanlama (1-10)</p>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="flex flex-col">
                    <span className="text-[8px] text-[#4f7b92]">Şiddet (S)</span>
                    <input type="number" min={1} max={10} value={severity} onChange={(e) => setSeverity(Number(e.target.value))} className="p-1 text-center bg-[#061320] border border-[#10293f] rounded text-xs mt-1" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[8px] text-[#4f7b92]">Sıklık (O)</span>
                    <input type="number" min={1} max={10} value={occurrence} onChange={(e) => setOccurrence(Number(e.target.value))} className="p-1 text-center bg-[#061320] border border-[#10293f] rounded text-xs mt-1" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[8px] text-[#4f7b92]">Tespit (D)</span>
                    <input type="number" min={1} max={10} value={detection} onChange={(e) => setDetection(Number(e.target.value))} className="p-1 text-center bg-[#061320] border border-[#10293f] rounded text-xs mt-1" />
                  </div>
                </div>
                <div className="text-[9px] text-right text-cyan-500 font-mono pt-1">
                  RPN: {severity * occurrence * detection}
                </div>
              </div>

              {/* Yokoten */}
              <label className="flex items-center gap-2 cursor-pointer text-xs text-[#80deea] py-1">
                <input type="checkbox" checked={yokoten} onChange={(e) => setYokoten(e.target.checked)} className="rounded bg-[#030a10] border-[#10293f]" />
                <span>Yokoten Uygulandı (Yatay Paylaşım)</span>
              </label>

              {error && (
                <div className="p-2 bg-red-950/20 border border-red-500/30 rounded text-red-400 text-[10px]">
                  {error}
                </div>
              )}

              <button type="submit" disabled={isBusy || !title || !lessonsLearned} className="btn btn-primary w-full py-2.5 text-xs">
                {isBusy ? "Kaydediliyor..." : "A3 Raporunu Kaydet ve Bitir"}
              </button>
            </form>
          ) : (
            <div className="p-5 bg-[#061320] border border-[#10293f] rounded-xl text-center text-xs text-[#4f7b92] leading-relaxed">
              <HelpCircle size={22} className="mx-auto text-cyan-500/50 mb-2" />
              Süreç içerisindeki tüm adımları doldurduğunuzda A3 Raporunu kaydetme seçeneği açılacaktır.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
