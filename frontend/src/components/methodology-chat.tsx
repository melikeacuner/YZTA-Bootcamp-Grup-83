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
  agentResolve
} from "@/lib/api";
import { METHODOLOGY_STEPS, MIN_STEPS_TO_COMPLETE } from "@/lib/methodology-steps";
import { METHODOLOGY_LABELS, SessionResponse } from "@/lib/types";
import { AlertCircle, HelpCircle, ArrowLeft, ArrowRight, Loader2, Sparkles } from "lucide-react";

interface MethodologyChatProps {
  sessionId: string;
  onFinalized: (recordId: string) => void;
}

export default function MethodologyChat({ sessionId, onFinalized }: MethodologyChatProps) {
  const { token } = useAuth();
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [followUpQuestion, setFollowUpQuestion] = useState<string | null>(null);
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
      setFollowUpQuestion(null);
    } catch (err: any) {
      setError(err.message || "Yanıt gönderilemedi");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleFollowUp() {
    if (!token || isBusy) return;
    setIsBusy(true);
    setError(null);
    try {
      const question = await requestFollowUp(token, sessionId);
      setFollowUpQuestion(question);
    } catch (err: any) {
      setError(err.message || "Takip sorusu alınamadı.");
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
      setFollowUpQuestion(null);
    } catch (err: any) {
      setError(err.message || "Geri gidilemedi.");
    } finally {
      setIsBusy(false);
    }
  }

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

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Session Title Header */}
      <div className="flex items-center justify-between p-4 bg-[#061320] border border-[#10293f] rounded-xl shadow-lg">
        <div className="flex items-center gap-3">
          <span className="text-xs px-2.5 py-1 rounded bg-[#10293f] text-[#00e5ff] uppercase font-mono font-semibold">
            {METHODOLOGY_LABELS[session.methodology]}
          </span>
          <p className="text-xs text-[#4f7b92] truncate max-w-xs md:max-w-md">
            {session.problem_description}
          </p>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full ${
          session.status === "active" ? "bg-green-500/10 text-green-400" : "bg-cyan-500/10 text-cyan-400"
        }`}>
          {session.status === "active" ? "Aktif" : "Tamamlandı"}
        </span>
      </div>

      {/* Main Container */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Side: Steps History and Input */}
        <div className="md:col-span-2 space-y-4">
          {/* History */}
          <div className="space-y-3">
            {steps.map((step, idx) => {
              const ans = answersMap[step.name] || answersMap[idx.toString()];
              if (!ans) return null;
              return (
                <div key={step.name} className="p-4 bg-[#061320] border border-[#10293f] rounded-lg space-y-2">
                  <p className="text-[11px] font-semibold text-[#80deea] uppercase font-mono">
                    {step.prompt}
                  </p>
                  <p className="text-xs text-[#e0f7fa] leading-relaxed">{ans}</p>
                </div>
              );
            })}
          </div>

          {/* Active Question input */}
          {session.status === "active" && currentStepDef && (
            <form onSubmit={handleSubmitAnswer} className="p-5 bg-[#061320] border border-[#10293f] rounded-xl space-y-4 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />
              
              <div className="flex justify-between items-center text-[10px] text-[#4f7b92] font-mono">
                <span>ADIM {session.current_step + 1} / {steps.length}</span>
                <span>En az 10 karakter</span>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
                  {session.next_prompt ? (
                    <>
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                      <span>{session.next_prompt}</span>
                    </>
                  ) : (
                    <span>{currentStepDef.prompt}</span>
                  )}
                </label>

                <textarea
                  required
                  minLength={10}
                  rows={4}
                  placeholder="Yanıtınızı buraya girin..."
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full p-3 bg-[#030a10] border border-[#10293f] rounded-lg text-[#e0f7fa] placeholder-[#4f7b92] text-xs focus:border-[#00e5ff]"
                />
              </div>

              {followUpQuestion && (
                <div className="p-3 bg-cyan-950/20 border border-cyan-500/30 rounded-lg text-xs text-[#80deea]">
                  <p className="font-semibold flex items-center gap-1.5 text-[#00e5ff]">
                    <Sparkles size={12} className="dot-pulse" />
                    AI Takip Sorusu:
                  </p>
                  <p className="mt-1">{followUpQuestion}</p>
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400 text-xs">
                  <AlertCircle size={14} />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex flex-wrap gap-2 pt-2">
                <button type="submit" disabled={isBusy || answer.trim().length < 10} className="btn btn-primary text-xs py-2 px-4 flex items-center gap-1">
                  <span>Yanıtla</span>
                  <ArrowRight size={13} />
                </button>
                <button type="button" onClick={handleFollowUp} disabled={isBusy || answer.trim().length < 10} className="btn btn-secondary text-xs py-2 px-3">
                  AI Takip Sorusu
                </button>
                {session.current_step > 0 && (
                  <button type="button" onClick={handleGoBack} disabled={isBusy} className="btn btn-secondary text-xs py-2 px-3 flex items-center gap-1">
                    <ArrowLeft size={13} />
                    <span>Geri</span>
                  </button>
                )}
              </div>
            </form>
          )}

          {canComplete && (
            <div className="flex flex-col gap-2.5">
              <button
                type="button"
                onClick={handleAutoResolve}
                disabled={isBusy}
                className="w-full py-3 bg-gradient-to-r from-[#00e5ff] to-[#7c4dff] text-[#030a10] font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/10 hover:shadow-cyan-500/20 transition-all duration-200"
              >
                <Sparkles size={14} className="animate-pulse" />
                <span>AI ile Rapor Sentezle & Kapat</span>
              </button>
              <button onClick={handleComplete} disabled={isBusy} className="w-full py-3 bg-[#0a1f33] border border-[#10293f] text-[#80deea] rounded-lg text-xs hover:bg-[#10293f] transition-all">
                Manuel A3 Raporu Doldur
              </button>
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
