"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { createSession, searchKnowledge } from "@/lib/api";
import { METHODOLOGY_LABELS, MethodologyType, SessionResponse, KnowledgeSearchResult } from "@/lib/types";

import { HelpCircle, ChevronRight, AlertCircle, ArrowRight, Eye, X } from "lucide-react";
import UnifiedRecordDetail from "./unified-record-detail";

interface NewSessionProps {
  onSessionCreated: (session: SessionResponse) => void;
  onViewReport?: (recordId: string) => void;
}

export default function NewSession({ onSessionCreated, onViewReport }: NewSessionProps) {
  const { token } = useAuth();
  const [description, setDescription] = useState("");
  const [methodology, setMethodology] = useState<MethodologyType>("5why");
  const [similarRecords, setSimilarRecords] = useState<KnowledgeSearchResult[]>([]);
  const [previewRecordId, setPreviewRecordId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dynamic similarity search as the user writes the description
  useEffect(() => {
    if (!token || description.trim().length < 10) {
      setSimilarRecords([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const results = await searchKnowledge(token, description);
        setSimilarRecords(results.slice(0, 3));
      } catch (err) {
        console.error("Failed to fetch similar records:", err);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [description, token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !description.trim()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const session = await createSession(token, methodology, description);
      onSessionCreated(session);
    } catch (err: any) {
      setError(err.message || "Problem başlatılamadı");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleRecordClick(recordId: string) {
    if (onViewReport) {
      onViewReport(recordId);
    } else {
      setPreviewRecordId(recordId);
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Modal for viewing clicked similar record */}
      {previewRecordId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="w-full max-w-4xl max-h-[90vh] bg-[#061320] border border-[#10293f] rounded-2xl flex flex-col overflow-hidden shadow-2xl p-4">
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

      {/* Introduction Header */}
      <div>
        <h2 className="text-2xl font-bold text-[#e0f7fa]">Yeni Problem Analiz Seansı Başlat</h2>
        <p className="text-sm text-[#80deea] mt-1">
          Problemi yapay zeka ajanı rehberliğinde çözebilir veya yapılandırılmış endüstriyel problem çözme metodolojilerini seçebilirsiniz.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left / Center - Form */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleSubmit} className="p-6 glass rounded-xl space-y-6 relative overflow-hidden shadow-lg shadow-cyan-500/5">
            {/* Corner cyan glowing stripe */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />
            
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-[#80deea]">1. Problemi Açıklayın</label>
              <textarea
                required
                minLength={10}
                rows={6}
                placeholder="Örn: CNC torna tezgahının X ekseninde 0.2mm sapma oluşuyor. Sürekli hata kodu E-34 veriyor ve duraksama yapıyor."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full p-4 bg-[#030a10] border border-[#10293f] rounded-lg text-[#e0f7fa] placeholder-[#4f7b92] text-sm focus:border-[#00e5ff] transition"
              />
              <span className="text-[11px] text-[#4f7b92] self-end">
                En az 10 karakter girilmelidir.
              </span>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-[#80deea]">2. Analiz Metodolojisi Seçin</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(METHODOLOGY_LABELS).map(([key, label]) => {
                  const isAgent = key === "agent";
                  const selected = methodology === key;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setMethodology(key as MethodologyType)}
                      className={`p-4 rounded-lg border text-left transition-all ${
                        selected
                          ? "bg-gradient-to-br from-[#0a1f33] to-[#061320] border-[#00e5ff] text-[#00e5ff] shadow-md shadow-cyan-500/5"
                          : "bg-[#030a10] border-[#10293f] text-[#80deea] hover:border-[#194063]"
                      }`}
                    >
                      <div className="font-semibold text-sm flex items-center justify-between">
                        <span>{label}</span>
                        {isAgent && (
                          <span className="text-[9px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 uppercase tracking-widest font-mono">
                            Önerilen
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#4f7b92] mt-2">
                        {key === "agent" && "Yapay zeka problem çözme danışmanıyla interaktif sohbet ve otomatik sentezleme."}
                        {key === "5why" && "5 Neden analiz yöntemiyle kök nedene kadar soru-cevap."}
                        {key === "ishikawa" && "Balık kılçığı yöntemi ile 6 ana kategori altında nedenleri sorgulama."}
                        {key === "8d" && "Müşteri ve operasyonel problemler için 8 disiplinli standart analiz."}
                        {key === "pdca" && "Planla - Uygula - Kontrol Et - Önlem Al döngüsüyle iyileştirme planı."}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400 text-xs">
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting || description.trim().length < 10}
              className="btn btn-primary w-full py-3.5"
            >
              {isSubmitting ? "Analiz Başlatılıyor..." : "Analiz Seansını Başlat"}
            </button>
          </form>
        </div>

        {/* Right - Dynamic recommendations */}
        <div className="space-y-6">
          <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
            <h3 className="text-sm font-semibold text-[#80deea] flex items-center gap-2">
              <HelpCircle size={16} className="text-[#00e5ff]" />
              Anlık Benzer Vaka Önerileri
            </h3>
            
            {description.trim().length < 10 ? (
              <p className="text-xs text-[#4f7b92] leading-relaxed">
                Yazmaya başladığınızda, yapay zeka semantik arama yaparak geçmişte çözülmüş benzer problemleri buraya önerecektir. Bu sayede tekerleği yeniden icat etmekten kurtulursunuz.
              </p>
            ) : similarRecords.length === 0 ? (
              <p className="text-xs text-[#4f7b92] leading-relaxed">
                Semantik eşleşme bulunamadı. Yeni bir vaka oluşturmaya devam edebilirsiniz.
              </p>
            ) : (
              <div className="space-y-3">
                <p className="text-[11px] text-cyan-400 font-medium">Şu vakalar ilginizi çekebilir:</p>
                {similarRecords.map((rec) => (
                  <div
                    key={rec.id}
                    onClick={() => handleRecordClick(rec.id)}
                    className="p-3.5 bg-[#030a10] border border-[#10293f] rounded-xl hover:border-[#00e5ff] hover:bg-[#061320] transition-all cursor-pointer group space-y-2"
                  >
                    <div className="flex justify-between items-start gap-1">
                      <h4 className="text-xs font-semibold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors truncate">
                        {rec.title || "Başlıksız Kayıt"}
                      </h4>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-950/50 text-[#00e5ff] border border-cyan-500/20 font-mono">
                        %{rec.score ? (rec.score * 100).toFixed(0) : "0"} Benzer
                      </span>
                    </div>
                    {rec.root_cause && (
                      <p className="text-[10px] text-[#80deea] opacity-90 line-clamp-2 bg-[#061320] p-2 rounded border border-[#10293f]/40">
                        <strong className="text-[#00e5ff]">Kök Neden:</strong> {rec.root_cause}
                      </p>
                    )}
                    <div className="flex items-center justify-between text-[9px] text-[#4f7b92] pt-1.5 border-t border-[#10293f]/50">
                      <span>Birim: {rec.department || "Genel"}</span>
                      <span className="text-[#00e5ff] font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform font-mono">
                        <span>Raporu İncele</span>
                        <ArrowRight size={10} />
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
