"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { searchKnowledge, getRecord } from "@/lib/api";
import { KnowledgeSearchResult, RecordResponse } from "@/lib/types";

import { Search, Loader2, BookOpen, Star, Sparkles, Filter, ChevronRight, X } from "lucide-react";
import UnifiedRecordDetail from "./unified-record-detail";

export default function KnowledgeSearch() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [methodology, setMethodology] = useState("");
  const [department, setDepartment] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !query.trim()) return;

    setLoading(true);
    setError(null);

    const filters: Record<string, string> = {};
    if (methodology) filters.methodology = methodology;
    if (department) filters.department = department;

    try {
      const data = await searchKnowledge(token, query, filters);
      setResults(data);
    } catch (err: any) {
      console.error("Semantic search error:", err);
      setError("Semantik arama gerçekleştirilemedi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full flex-1 flex flex-col space-y-6 overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="shrink-0">
        <h2 className="text-2xl font-bold text-[#e0f7fa]">Semantik Bilgi Bankası</h2>
        <p className="text-xs text-[#80deea]">Qdrant vektör veritabanı ile dökümanlar arasında anlamsal (semantic) benzerlik araması yapın.</p>
      </div>

      {/* Search & Filter Form */}
      <form onSubmit={handleSearch} className="p-4 bg-[#061320] border border-[#10293f] rounded-xl space-y-4 shrink-0">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 w-4.5 h-4.5 text-[#4f7b92]" />
            <input
              required
              type="text"
              placeholder="Hata kodları, arıza tipleri veya semptomları girin (örn: 'motorda aşırı ısınma ve yağ kaçağı')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-11 py-3 bg-[#030a10] border border-[#10293f] rounded-lg text-sm text-[#e0f7fa] placeholder-[#4f7b92] focus:border-[#00e5ff] transition"
            />
          </div>
          <button type="submit" disabled={loading || !query.trim()} className="btn btn-primary px-6 py-3 font-semibold text-sm">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Semantik Ara"}
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center pt-2 border-t border-[#10293f]/50">
          <span className="text-[10px] text-[#4f7b92] font-semibold uppercase flex items-center gap-1.5">
            <Filter size={11} />
            Kısıtlar:
          </span>
          <select value={methodology} onChange={(e) => setMethodology(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[11px]">
            <option value="">Tüm Metodolojiler</option>
            <option value="AGENT">AI Danışman</option>
            <option value="5why">5 Why</option>
            <option value="ishikawa">Ishikawa</option>
            <option value="8d">8D</option>
            <option value="pdca">PDCA</option>
          </select>
          <select value={department} onChange={(e) => setDepartment(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[11px]">
            <option value="">Tüm Departmanlar</option>
            <option value="Üretim">Üretim</option>
            <option value="Lojistik">Lojistik</option>
            <option value="Kalite">Kalite</option>
            <option value="Bilgi İşlem">Bilgi İşlem</option>
            <option value="Finans">Finans</option>
          </select>
        </div>
      </form>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg text-xs text-red-400 shrink-0">
          {error}
        </div>
      )}

      {/* Results Container */}
      <div className="flex-1 overflow-y-auto pr-1">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 text-[#80deea] gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-[#00e5ff]" />
            <p className="text-xs font-mono">Qdrant vektörleri eşleştiriliyor...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-[#10293f] rounded-xl text-xs text-[#4f7b92] leading-relaxed">
            <BookOpen className="mx-auto text-cyan-500/30 mb-3" size={24} />
            Problem semptomlarını yazıp arayarak benzer vakaları eşleştirin.
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-[11px] text-cyan-400 font-mono">EN YAKIN {results.length} EŞLEŞEN KAYIT BULUNDU:</p>
            
            {results.map((res) => {
              const matchPercentage = res.score ? (res.score * 100).toFixed(0) : "0";
              const scoreVal = res.score || 0;
              const badgeColor = scoreVal > 0.8 ? "border-green-500/30 text-green-400" : scoreVal > 0.5 ? "border-cyan-500/30 text-cyan-400" : "border-yellow-500/30 text-yellow-400";
              
              return (
                <div
                  key={res.id}
                  onClick={() => setSelectedRecordId(res.id)}
                  className="p-4 bg-[#061320] border border-[#10293f] hover:border-[#00e5ff] rounded-xl cursor-pointer transition-all flex items-center justify-between group"
                >
                  <div className="space-y-1.5 overflow-hidden pr-4">
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border ${badgeColor} font-mono font-bold flex items-center gap-1`}>
                        <Star size={8} />
                        {matchPercentage}% Benzerlik
                      </span>
                      <span className="text-[9px] px-2 py-0.5 rounded bg-[#10293f] text-[#4f7b92] uppercase font-mono">
                        {res.methodology}
                      </span>
                    </div>
                    <h3 className="text-xs font-semibold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors truncate">
                      {res.title || "Başlıksız Kayıt"}
                    </h3>
                    <p className="text-[10px] text-[#4f7b92]">
                      Departman: {res.department || "Belirtilmedi"} | Sektör: {res.industry || "Belirtilmedi"}
                    </p>
                  </div>
                  <ChevronRight className="text-[#4f7b92] group-hover:text-[#00e5ff] transition-colors shrink-0" size={16} />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Record Detail Modal */}
      {selectedRecordId && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm p-6 overflow-y-auto z-50 animate-fade-in flex items-center justify-center">
          <div className="w-full max-w-5xl h-full flex flex-col relative bg-[#030a10] rounded-2xl border border-[#10293f] overflow-hidden">
            {/* Close Button overlay */}
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
