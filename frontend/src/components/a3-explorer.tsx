"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { listRecords } from "@/lib/api";
import { RecordResponse } from "@/lib/types";

import { Loader2, Search, ArrowRight, ShieldAlert, Sparkles, Filter } from "lucide-react";

interface A3ExplorerProps {
  onViewDetail: (recordId: string) => void;
}

export default function A3Explorer({ onViewDetail }: A3ExplorerProps) {
  const { token } = useAuth();
  const [records, setRecords] = useState<RecordResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Local Filtering
  const [searchQuery, setSearchQuery] = useState("");
  const [methodologyFilter, setMethodologyFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");

  const loadRecords = useCallback(async () => {
    if (!token) return;
    try {
      const data = await listRecords(token, 1, 100);
      setRecords(data.items || []);
    } catch (err) {
      console.error("Failed to load problem records:", err);
      setError("Raporlar yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  const filteredRecords = records.filter((rec) => {
    const titleMatch = rec.title.toLowerCase().includes(searchQuery.toLowerCase());
    const descMatch = rec.description.toLowerCase().includes(searchQuery.toLowerCase());
    const queryMatch = titleMatch || descMatch;
    
    const methodMatch = methodologyFilter === "" || rec.methodology === methodologyFilter;
    const deptMatch = departmentFilter === "" || rec.department === departmentFilter;

    return queryMatch && methodMatch && deptMatch;
  });

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">A3 Raporları Yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="w-full flex-1 flex flex-col space-y-6 overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="shrink-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[#e0f7fa]">Problem & A3 Belge Havuzu</h2>
          <p className="text-xs text-[#80deea]">Kurumsal bilgi hafızasına kaydedilmiş problem çözme raporlarını inceleyin.</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-[#061320] border border-[#10293f] rounded-xl flex flex-col sm:flex-row gap-3 shrink-0 items-center">
        {/* Search */}
        <div className="relative w-full sm:flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-[#4f7b92]" />
          <input
            type="text"
            placeholder="Başlık veya açıklamada ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 py-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
          />
        </div>
        
        {/* Methodology */}
        <select
          value={methodologyFilter}
          onChange={(e) => setMethodologyFilter(e.target.value)}
          className="w-full sm:w-[160px] p-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
        >
          <option value="">Tüm Metodolojiler</option>
          <option value="AGENT">AI Danışman</option>
          <option value="5why">5 Why</option>
          <option value="ishikawa">Ishikawa</option>
          <option value="8d">8D</option>
          <option value="pdca">PDCA</option>
        </select>

        {/* Department */}
        <select
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="w-full sm:w-[160px] p-2 bg-[#030a10] border border-[#10293f] rounded text-xs"
        >
          <option value="">Tüm Departmanlar</option>
          <option value="Üretim">Üretim</option>
          <option value="Lojistik">Lojistik</option>
          <option value="Kalite">Kalite</option>
          <option value="Bilgi İşlem">Bilgi İşlem</option>
          <option value="Finans">Finans</option>
        </select>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg text-xs text-red-400 shrink-0">
          {error}
        </div>
      )}

      {/* Grid Stack */}
      <div className="flex-1 overflow-y-auto pr-1">
        {filteredRecords.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-[#10293f] rounded-xl text-xs text-[#4f7b92]">
            Kayıtlı problem raporu bulunamadı.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRecords.map((rec) => {
              const rpn = rec.rpn || 1;
              const severityColor = rpn > 100 ? "text-[#ff1744]" : rpn > 40 ? "text-[#ffea00]" : "text-[#00e676]";
              
              return (
                <div
                  key={rec.id}
                  onClick={() => onViewDetail(rec.id)}
                  className="p-5 bg-[#061320] border border-[#10293f] rounded-xl hover:border-[#00e5ff] transition-all cursor-pointer flex flex-col justify-between group relative overflow-hidden"
                >
                  {/* Decorative glowing gradient overlay */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[rgba(0,229,255,0.01)] pointer-events-none" />

                  {/* Header tags */}
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-[9px] px-2 py-0.5 rounded bg-[#10293f] text-cyan-400 font-mono uppercase tracking-wider font-semibold">
                      {rec.methodology}
                    </span>
                    <span className="text-[10px] text-[#4f7b92] font-mono">
                      {rec.department || "Diğer"}
                    </span>
                  </div>

                  {/* Body Content */}
                  <div className="space-y-2 mb-4">
                    <h3 className="text-sm font-semibold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors line-clamp-1">
                      {rec.title}
                    </h3>
                    <p className="text-[11px] text-[#4f7b92] line-clamp-3 leading-relaxed">
                      {rec.description}
                    </p>
                  </div>

                  {/* Footer Stats */}
                  <div className="pt-3 border-t border-[#10293f] flex items-center justify-between">
                    {/* RPN rating */}
                    <div className="flex items-center gap-1.5">
                      <ShieldAlert size={12} className={severityColor} />
                      <span className="text-[10px] text-[#4f7b92]">RPN:</span>
                      <span className={`text-xs font-bold font-mono ${severityColor}`}>
                        {rpn}
                      </span>
                    </div>

                    {/* Yokoten state */}
                    {rec.yokoten_applied ? (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-green-500/10 text-[#00e676] flex items-center gap-1 font-semibold">
                        <Sparkles size={9} className="dot-pulse" />
                        Yokoten
                      </span>
                    ) : (
                      <span className="text-[9px] text-[#4f7b92]">Lokal</span>
                    )}

                    <div className="text-[#00e5ff] hover:translate-x-0.5 transition-transform flex items-center gap-0.5 text-[10px] font-bold uppercase">
                      <span>Aç</span>
                      <ArrowRight size={10} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
