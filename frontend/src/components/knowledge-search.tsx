"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { searchKnowledge, askCorporateBrain } from "@/lib/api";
import { KnowledgeSearchResult } from "@/lib/types";

import { Search, Loader2, BookOpen, Star, Sparkles, Filter, ChevronRight, X } from "lucide-react";
import UnifiedRecordDetail from "./unified-record-detail";

export default function KnowledgeSearch() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<"search" | "ask">("search");
  const [query, setQuery] = useState("");
  const [methodology, setMethodology] = useState("");
  const [department, setDepartment] = useState("");
  const [assigneeName, setAssigneeName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ask Corporate Brain States
  const [askQuery, setAskQuery] = useState("");
  const [aiAnswer, setAiAnswer] = useState<{ answer: string; sources: any[] } | null>(null);
  const [askLoading, setAskLoading] = useState(false);

  // Detail Modal
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);

  async function handleAskSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !askQuery.trim()) return;
    setAskLoading(true);
    setAiAnswer(null);
    try {
      const res = await askCorporateBrain(token, askQuery.trim(), department || undefined);
      setAiAnswer(res);
    } catch (err: any) {
      console.error("Ask Corporate Brain error:", err);
      setAiAnswer({
        answer: "Kurumsal Beyin yanıt veremedi. Lütfen sorunuzu kontrol edip tekrar deneyin.",
        sources: []
      });
    } finally {
      setAskLoading(false);
    }
  }

  const fetchKnowledge = useCallback(async (qVal: string) => {
    if (!token) return;
    setLoading(true);
    setError(null);

    const filters: Record<string, string> = {};
    if (methodology) filters.methodology = methodology;
    if (department) filters.department = department;
    if (assigneeName) filters.assignee_name = assigneeName;
    if (startDate) filters.start_date = startDate;
    if (endDate) filters.end_date = endDate;

    try {
      const data = await searchKnowledge(token, qVal, filters);
      setResults(data);
    } catch (err: any) {
      console.error("Semantic search error:", err);
      setError("Bilgi bankası araması gerçekleştirilemedi.");
    } finally {
      setLoading(false);
    }
  }, [token, methodology, department, assigneeName, startDate, endDate]);

  // Live debounced search effect
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchKnowledge(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query, fetchKnowledge]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    fetchKnowledge(query);
  }

  function handleClear() {
    setQuery("");
    setMethodology("");
    setDepartment("");
    setAssigneeName("");
    setStartDate("");
    setEndDate("");
    fetchKnowledge("");
  }

  const hasActiveFilters = Boolean(query || methodology || department || assigneeName || startDate || endDate);

  return (
    <div className="w-full flex-1 flex flex-col space-y-6 overflow-hidden animate-fade-in">
      {/* Header & Mode Tabs */}
      <div className="shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#10293f] pb-4">
        <div>
          <h2 className="text-2xl font-bold text-[#e0f7fa]">Bilgi Bankası & AI Kurumsal Beyin</h2>
          <p className="text-xs text-[#80deea] mt-0.5">Semantik vektör araması yapın veya kurumsal hafızaya yapay zeka ile doğrudan sorular sorun.</p>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1.5 bg-[#061320] border border-[#10293f] p-1.5 rounded-xl">
          <button
            type="button"
            onClick={() => setActiveTab("search")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === "search"
                ? "bg-[#00e5ff] text-[#030a10] shadow-md shadow-cyan-500/20"
                : "text-[#80deea] hover:bg-[#10293f]/40"
            }`}
          >
            <Search size={14} />
            <span>Semantik Vaka Arama</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("ask")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === "ask"
                ? "bg-gradient-to-r from-purple-500 to-cyan-500 text-white shadow-md shadow-purple-500/20"
                : "text-[#80deea] hover:bg-[#10293f]/40"
            }`}
          >
            <Sparkles size={14} className="text-yellow-300 animate-pulse" />
            <span>🤖 Kurumsal Beyne Sor (RAG AI)</span>
          </button>
        </div>
      </div>

      {activeTab === "ask" ? (
        /* Ask Corporate Brain Mode */
        <div className="space-y-6 overflow-y-auto pr-1 flex-1">
          <form onSubmit={handleAskSubmit} className="p-5 bg-gradient-to-r from-purple-950/20 to-cyan-950/20 border border-purple-500/30 rounded-2xl space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-purple-300">
              <Sparkles size={16} className="text-cyan-400 animate-pulse" />
              <span>Yapay Zeka Kurumsal Soru-Cevap Asistanı</span>
            </div>
            
            <div className="flex gap-3">
              <textarea
                required
                rows={2}
                placeholder="Örn: 'CNC tezgahlarında ve enjeksiyon kalıplama makinelerinde en sık yaşanan 3 kök neden neydi ve nasıl çözüldü?'"
                value={askQuery}
                onChange={(e) => setAskQuery(e.target.value)}
                className="flex-1 p-3.5 bg-[#030a10] border border-[#10293f] rounded-xl text-sm text-[#e0f7fa] placeholder-[#4f7b92] focus:border-purple-400 transition"
              />
              <button
                type="submit"
                disabled={askLoading || !askQuery.trim()}
                className="btn bg-gradient-to-r from-purple-600 to-cyan-500 text-white font-bold px-6 py-3 rounded-xl flex items-center gap-2 shadow-lg shadow-purple-500/20 hover:opacity-90 transition-opacity"
              >
                {askLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                <span>Kurumsal Beyne Sor</span>
              </button>
            </div>
          </form>

          {/* AI Response Card */}
          {aiAnswer && (
            <div className="p-6 glass rounded-2xl border border-cyan-500/30 space-y-4 animate-fade-in shadow-xl shadow-cyan-500/5">
              <div className="flex items-center justify-between border-b border-[#10293f] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-purple-950 border border-cyan-400 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
                  </div>
                  <h3 className="text-sm font-bold text-[#e0f7fa]">Yapay Zeka Analitik Sentez Yanıtı</h3>
                </div>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-md border border-cyan-500/20">
                  RAG Kurumsal Beyin Entegrasyonu
                </span>
              </div>

              <div className="text-xs text-[#e0f7fa] leading-relaxed whitespace-pre-wrap font-sans bg-[#030a10]/60 p-4 rounded-xl border border-[#10293f]">
                {aiAnswer.answer}
              </div>

              {/* Referenced Corporate Sources */}
              {aiAnswer.sources && aiAnswer.sources.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-[#10293f]">
                  <span className="text-[10px] font-mono text-[#80deea] font-semibold uppercase tracking-wider block">
                    📌 Referans Alınan Kurumsal Vaka Kaynakları ({aiAnswer.sources.length}):
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {aiAnswer.sources.map((src: any) => (
                      <div key={src.id} className="p-3 bg-[#061320] border border-[#10293f] rounded-lg text-xs space-y-1">
                        <span className="font-bold text-cyan-300 block truncate">{src.title}</span>
                        <span className="text-[10px] text-[#4f7b92] block">Departman: {src.department}</span>
                        <p className="text-[11px] text-[#80deea] line-clamp-1">Kök Neden: {src.root_cause}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Semantic Search Mode */
        <div className="space-y-6 flex-1 flex flex-col overflow-hidden">
          {/* Search & Filter Form */}
          <form onSubmit={handleSearch} className="p-4 bg-[#061320] border border-[#10293f] rounded-xl space-y-4 shrink-0">
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-3.5 w-4.5 h-4.5 text-[#4f7b92]" />
                <input
                  type="text"
                  placeholder="Hata kodları, arıza tipleri veya semptomları girin (canlı arama yapar, örn: 'motorda aşırı ısınma ve yağ kaçağı')..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-11 pr-10 py-3 bg-[#030a10] border border-[#10293f] rounded-lg text-sm text-[#e0f7fa] placeholder-[#4f7b92] focus:border-[#00e5ff] transition"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => setQuery("")}
                    className="absolute right-3 top-3.5 text-[#4f7b92] hover:text-[#00e5ff] transition-colors"
                    title="Aramayı Temizle"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
              <button type="submit" disabled={loading} className="btn btn-primary px-6 py-3 font-semibold text-sm flex items-center gap-1.5">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>Semantik Ara</span>
              </button>
              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="btn btn-secondary px-4 py-3 text-xs text-red-400 border-red-500/30 hover:bg-red-950/30 flex items-center gap-1.5"
                  title="Tüm Filtreleri İptal Et ve Sıfırla"
                >
                  <X size={14} />
                  <span>Filtreleri Temizle</span>
                </button>
              )}
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-4 items-center pt-2 border-t border-[#10293f]/50">
              <span className="text-[10px] text-[#4f7b92] font-semibold uppercase flex items-center gap-1.5">
                <Filter size={11} />
                Filtreler:
              </span>
              <select value={methodology} onChange={(e) => setMethodology(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[11px] text-[#e0f7fa]">
                <option value="">Tüm Metodolojiler</option>
                <option value="AGENT">AI Danışman</option>
                <option value="5why">5 Why</option>
                <option value="ishikawa">Ishikawa</option>
                <option value="8d">8D</option>
                <option value="pdca">PDCA</option>
              </select>
              <select value={department} onChange={(e) => setDepartment(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[11px] text-[#e0f7fa]">
                <option value="">Tüm Departmanlar</option>
                <option value="Üretim">Üretim</option>
                <option value="Lojistik">Lojistik</option>
                <option value="Kalite">Kalite</option>
                <option value="Bilgi İşlem">Bilgi İşlem</option>
                <option value="Finans">Finans</option>
              </select>
              <input
                type="text"
                placeholder="Sorumlu Kişi"
                value={assigneeName}
                onChange={(e) => setAssigneeName(e.target.value)}
                className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[11px] text-[#e0f7fa] placeholder-[#4f7b92]"
              />
              <div className="flex items-center gap-1 text-[11px] text-[#4f7b92]">
                <span>Tarih:</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="p-1.5 bg-[#030a10] border border-[#10293f] rounded text-[10px] text-[#e0f7fa]"
                />
                <span>-</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="p-1.5 bg-[#030a10] border border-[#10293f] rounded text-[10px] text-[#e0f7fa]"
                />
              </div>
            </div>
          </form>

          {/* Results List */}
          {error ? (
            <div className="p-4 bg-red-950/20 border border-red-500/30 rounded-xl text-red-400 text-xs text-center">
              {error}
            </div>
          ) : results.length === 0 ? (
            <div className="p-12 text-center text-[#4f7b92] bg-[#061320]/40 border border-[#10293f] rounded-xl space-y-2">
              <BookOpen size={32} className="mx-auto text-[#10293f]" />
              <p className="text-sm font-medium">Arama kriterlerine uygun vaka bulunamadı.</p>
              <p className="text-xs">Filtreleri değiştirebilir veya arama sorgusunu genişletebilirsiniz.</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {results.map((res) => {
                const tagsList = typeof res.tags === "string" ? JSON.parse(res.tags) : res.tags || [];
                return (
                  <div
                    key={res.id}
                    onClick={() => setSelectedRecordId(res.id)}
                    className="p-4 bg-[#061320] border border-[#10293f] hover:border-[#00e5ff]/50 rounded-xl transition-all cursor-pointer flex items-center justify-between group shadow-sm hover:shadow-cyan-500/10"
                  >
                    <div className="space-y-1.5 flex-1 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold text-[#00e5ff] bg-cyan-950/60 border border-cyan-500/30 px-2 py-0.5 rounded uppercase">
                          {res.methodology}
                        </span>
                        <span className="text-[10px] font-mono text-[#80deea]">
                          {res.department || "Belirtilmedi"}
                        </span>
                      </div>

                      <h3 className="text-xs font-bold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors line-clamp-1">
                        {res.title || "Başlıksız Kayıt"}
                      </h3>

                      {res.root_cause && (
                        <p className="text-[10px] text-[#4f7b92] line-clamp-1">
                          <strong className="text-[#80deea]">Kök Neden:</strong> {res.root_cause}
                        </p>
                      )}

                      {tagsList.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {tagsList.map((tag: string, tIdx: number) => (
                            <span key={tIdx} className="text-[8px] px-1.5 py-0.5 rounded bg-cyan-950/40 border border-cyan-500/20 text-[#00e5ff] font-mono">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <ChevronRight className="text-[#4f7b92] group-hover:text-[#00e5ff] transition-colors shrink-0" size={16} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Record Detail Modal */}
      {selectedRecordId && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm p-6 overflow-y-auto z-50 animate-fade-in flex items-center justify-center">
          <div className="w-full max-w-5xl h-full flex flex-col relative bg-[#030a10] rounded-2xl border border-[#10293f] overflow-hidden">
            <button
              onClick={() => setSelectedRecordId(null)}
              className="absolute right-4 top-4 text-[#4f7b92] hover:text-red-500 z-50 p-2 rounded-lg bg-[#061320] border border-[#10293f]"
            >
              <X size={16} />
            </button>
            <div className="flex-1 overflow-y-auto p-4 md:p-6">
              <UnifiedRecordDetail recordId={selectedRecordId} onClose={() => setSelectedRecordId(null)} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
