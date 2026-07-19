"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { listSessions } from "@/lib/api";
import { SessionResponse, METHODOLOGY_LABELS } from "@/lib/types";
import { Inbox, ArrowRight, User, Building2, Tag, Loader2, Calendar } from "lucide-react";

interface ProblemPoolProps {
  onViewDetail: (sessionId: string) => void;
}

export default function ProblemPool({ onViewDetail }: ProblemPoolProps) {
  const { token } = useAuth();
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPoolSessions = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const allSessions = await listSessions(token);
      setSessions(allSessions.filter((s) => s.status === "pool"));
    } catch (err: any) {
      console.error(err);
      setError("Havuzdaki oturumlar yüklenemedi.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchPoolSessions();
  }, [fetchPoolSessions]);

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">Problem Havuzu Yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between border-b border-[#10293f] pb-4">
        <div>
          <h2 className="text-2xl font-bold text-[#e0f7fa] tracking-wide flex items-center gap-2">
            <Inbox className="text-[#00e5ff] w-6 h-6" />
            Problem Havuzu (Pool)
          </h2>
          <p className="text-xs text-[#4f7b92] mt-1">
            Kök nedeni belirlenmiş ve çözüm planı bekleyen aktif problem seansları.
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded bg-[#0a1f33] text-[#00e5ff] font-mono border border-cyan-500/20">
          {sessions.length} Bekleyen Vaka
        </span>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 rounded-xl text-xs text-red-400">
          {error}
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 bg-[#061320] border border-[#10293f] rounded-2xl text-center space-y-4 shadow-lg">
          <Inbox className="w-12 h-12 text-[#4f7b92] opacity-50" />
          <div>
            <h3 className="text-md font-bold text-[#e0f7fa]">Havuzda Problem Yok</h3>
            <p className="text-xs text-[#4f7b92] max-w-sm mt-1">
              Kök neden analizi tamamlanan tüm problem seansları başarıyla çözüldü veya henüz analizi tamamlanan bir oturum yok.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="bg-[#061320] border border-[#10293f] hover:border-[#00e5ff]/50 rounded-2xl p-5 flex flex-col justify-between shadow-xl transition-all duration-300 group hover:-translate-y-1 relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff] opacity-40 group-hover:opacity-100 transition-opacity" />
              
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950/40 text-[#00e5ff] font-mono uppercase">
                    {METHODOLOGY_LABELS[s.methodology]}
                  </span>
                  <span className="text-[9px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                    Çözüm Bekliyor
                  </span>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-sm font-bold text-[#e0f7fa] line-clamp-1 group-hover:text-[#00e5ff] transition-colors">
                    {s.summary || "Analiz Özeti Oluşturuluyor..."}
                  </h4>
                  <p className="text-xs text-[#80deea] opacity-80 mt-1 line-clamp-3 leading-relaxed">
                    {s.problem_description}
                  </p>
                </div>

                {/* Meta details */}
                <div className="pt-3 border-t border-[#10293f]/50 space-y-2 text-[11px] text-[#4f7b92]">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-3.5 h-3.5 text-[#80deea]" />
                    <span>Departman: <strong className="text-[#e0f7fa]">{s.department || "Atanacak"}</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="w-3.5 h-3.5 text-[#80deea]" />
                    <span>Sorumlu: <strong className="text-[#e0f7fa]">{s.assignee_name || "Atanacak"}</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-[#80deea]" />
                    <span>Takipçi: <strong className="text-[#e0f7fa]">{s.tracker_name || "Atanacak"}</strong></span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => onViewDetail(s.id)}
                className="mt-5 w-full py-2.5 bg-[#0a1f33] hover:bg-[#00e5ff] hover:text-[#030a10] text-[#00e5ff] text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition-all duration-200 border border-cyan-500/20 hover:border-transparent group-hover:shadow-lg group-hover:shadow-cyan-500/5"
              >
                <span>Ajan ile Çözüme Ulaş</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
