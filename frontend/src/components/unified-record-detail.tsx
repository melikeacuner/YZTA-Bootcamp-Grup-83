"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { getRecord, listTasks } from "@/lib/api";
import { RecordResponse, TaskResponse } from "@/lib/types";
import { Loader2, ArrowLeft, Printer, ShieldAlert, Sparkles, AlertCircle, FileText, CheckCircle, Clock, ListTodo } from "lucide-react";



interface UnifiedRecordDetailProps {
  recordId: string;
  onClose: () => void;
}

export default function UnifiedRecordDetail({ recordId, onClose }: UnifiedRecordDetailProps) {
  const { token } = useAuth();
  const [record, setRecord] = useState<RecordResponse | null>(null);
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRecordData = useCallback(async () => {
    if (!token || !recordId) return;
    try {
      const rec = await getRecord(token, recordId);
      setRecord(rec);
      // Load action plan tasks linked to this record
      const taskList = await listTasks(token, { problem_record_id: recordId });
      setTasks(taskList);
    } catch (err) {
      console.error("Failed to load record details:", err);
      setError("Rapor detayları yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [token, recordId]);

  useEffect(() => {
    loadRecordData();
  }, [loadRecordData, recordId]);

  function handlePrint() {
    window.print();
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">A3 Belgesi Yükleniyor...</p>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="p-4 bg-red-950/20 border border-red-500/30 rounded-xl text-red-400 text-xs text-center max-w-md mx-auto mt-12">
        {error || "Rapor bulunamadı."}
      </div>
    );
  }

  const rpn = record.rpn || 1;
  const severityColor = rpn > 100 ? "text-[#ff1744]" : rpn > 40 ? "text-[#ffea00]" : "text-[#00e676]";

  // Helper to render root cause visualization
  const renderRootCauseVisualization = () => {
    const methodologyLower = (record.methodology || "").toLowerCase();
    const responses = { ...(record.methodology_data || {}), ...(record.step_responses || {}) };

    // --- 5-WHY VISUAL LADDER ---
    if (methodologyLower === "5why" || Object.keys(responses).some(k => k.toLowerCase().includes("neden") || k.toLowerCase().includes("why"))) {
      const steps: Array<{ title: string; text: string }> = [];

      Object.entries(responses).forEach(([k, v]) => {
        if (typeof v === "string" && v.trim()) {
          steps.push({ title: k.replace(/_/g, " "), text: v });
        }
      });

      if (steps.length === 0 && record.root_cause) {
        steps.push({ title: "Kök Neden Tespiti", text: record.root_cause });
      }

      return (
        <div className="space-y-3 pt-2">
          <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest font-bold">
            🔗 5-Neden (5-Why) Görsel Neden Zinciri
          </div>
          <div className="relative border-l-2 border-cyan-500/40 pl-4 space-y-3 ml-2">
            {steps.map((step, idx) => (
              <div key={idx} className="relative group animate-fade-in">
                {/* Connector Dot */}
                <div className="absolute -left-[23px] top-2.5 w-3 h-3 rounded-full bg-[#00e5ff] border-2 border-[#030a10] shadow-sm shadow-cyan-500/50" />
                <div className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl space-y-1 hover:border-[#00e5ff]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-cyan-400 uppercase font-mono tracking-wide">
                      {step.title}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#10293f] text-[#4f7b92] font-mono">Adım {idx + 1}</span>
                  </div>
                  <p className="text-xs text-[#e0f7fa] leading-relaxed">{step.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // --- ISHIKAWA (FISHBONE) VISUAL DIAGRAM ---
    if (methodologyLower === "ishikawa" || Object.keys(responses).some(k => ["man", "machine", "method", "material", "measurement", "environment", "makine", "insan", "metot", "malzeme"].some(cat => k.toLowerCase().includes(cat)))) {
      const ishikawaCategories = [
        { key: "machine", label: "⚙️ Makine (Machine)", aliases: ["makine", "machine"] },
        { key: "man", label: "👤 İnsan (Man)", aliases: ["insan", "man"] },
        { key: "method", label: "📜 Metot (Method)", aliases: ["metot", "method"] },
        { key: "material", label: "📦 Malzeme (Material)", aliases: ["malzeme", "material"] },
        { key: "measurement", label: "📏 Ölçüm (Measurement)", aliases: ["ölçüm", "olcum", "measurement"] },
        { key: "environment", label: "🌍 Çevre (Environment)", aliases: ["çevre", "cevre", "environment"] }
      ];

      return (
        <div className="space-y-3 pt-2">
          <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest font-bold">
            🐟 Ishikawa (Balık Kılçığı) Görsel Analiz Şeması
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {ishikawaCategories.map((cat) => {
              // Find matching entry from responses
              let valText = "";
              Object.entries(responses).forEach(([k, v]) => {
                if (cat.aliases.some(a => k.toLowerCase().includes(a))) {
                  if (typeof v === "string") valText = v;
                  else if (Array.isArray(v)) valText = v.join(", ");
                }
              });

              return (
                <div key={cat.key} className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl space-y-1.5 relative overflow-hidden group hover:border-[#00e5ff]/40 transition-all">
                  <div className="text-[11px] font-bold text-cyan-400 tracking-wide border-b border-[#10293f] pb-1">
                    {cat.label}
                  </div>
                  {valText ? (
                    <p className="text-xs text-[#e0f7fa] leading-relaxed opacity-95">{valText}</p>
                  ) : (
                    <span className="text-[10px] text-[#4f7b92] italic">Normal / Faktör Saptanmadı</span>
                  )}
                </div>
              );
            })}
          </div>

          {record.root_cause && (
            <div className="p-3 bg-cyan-950/30 border border-cyan-500/40 rounded-xl space-y-1">
              <span className="text-[10px] font-bold text-cyan-400 uppercase font-mono tracking-wide">🎯 Sentezlenen Balık Kılçığı Kök Nedeni</span>
              <p className="text-xs text-[#e0f7fa] leading-relaxed">{record.root_cause}</p>
            </div>
          )}
        </div>
      );
    }

    // --- DEFAULT / STEP RESPONSES VISUALIZATION ---
    return (
      <div className="space-y-3 pt-2">
        <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest font-bold">
          📊 Metodoloji Analiz Adımları & Görselleştirme
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(responses).map(([k, v], idx) => (
            <div key={idx} className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl space-y-1">
              <div className="text-[10px] font-bold text-cyan-400 uppercase font-mono tracking-wide">
                {k.replace(/_/g, " ")}
              </div>
              <p className="text-xs text-[#e0f7fa] leading-relaxed">{typeof v === "string" ? v : JSON.stringify(v)}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full flex-1 flex flex-col space-y-6 overflow-hidden animate-fade-in pb-8">
      {/* Top action header (Hidden on print) */}
      <div className="flex items-center justify-between shrink-0 no-print">
        <button onClick={onClose} className="btn btn-secondary text-xs py-2 px-3 flex items-center gap-1.5">
          <ArrowLeft size={14} />
          <span>Gezgine Dön</span>
        </button>

        <button onClick={handlePrint} className="btn btn-primary text-xs py-2 px-4 flex items-center gap-1.5">
          <Printer size={14} />
          <span>Rapor Yazdır (A4 PDF)</span>
        </button>
      </div>

      {/* Toyota A3 Document Sheet Layout */}
      <div className="flex-1 bg-[#061320] border border-[#10293f] rounded-2xl overflow-y-auto p-6 md:p-8 flex flex-col space-y-6 relative print-container A3-print-sheet">
        {/* Glowing border top decor */}
        <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />

        {/* Sheet Title Section */}
        <div className="border-b border-[#10293f] pb-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#00e5ff] to-[#7c4dff] flex items-center justify-center font-bold text-[#030a10] text-xl shadow-lg shrink-0">
              A3
            </div>
            <div>
              <h2 className="text-xl font-bold text-[#e0f7fa] font-sans tracking-wide uppercase">{record.title}</h2>
              <p className="text-xs text-[#80deea] font-mono mt-0.5 uppercase tracking-widest">
                Metodoloji: {record.methodology}
              </p>
            </div>
          </div>

          {/* Document metadata block */}
          <div className="text-right text-[10px] text-[#4f7b92] font-mono space-y-0.5 border-l md:border-l-0 md:border-r border-[#10293f] pl-4 md:pl-0 md:pr-4">
            <p>SEKTÖR: {record.industry || "Diğer"}</p>
            <p>DEPARTMAN: {record.department || "Kalite"}</p>
            <p>TARİH: {record.created_at ? new Date(record.created_at).toLocaleDateString("tr-TR") : "Bilinmiyor"}</p>
          </div>
        </div>

        {/* 2-Column Toyota A3 grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          
          {/* LEFT COLUMN: Problem and Root Cause */}
          <div className="space-y-6">
            
            {/* Box 1: Problem Background & Description */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest border-b border-[#10293f] pb-1.5 flex items-center gap-2">
                <FileText size={13} />
                1. Problem Geçmişi ve Açıklama
              </h3>
              <div className="p-4 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] leading-relaxed whitespace-pre-line">
                {record.description}
              </div>
            </div>

            {/* Box 2: RPN Assessment */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest border-b border-[#10293f] pb-1.5 flex items-center gap-2">
                <ShieldAlert size={13} />
                2. Risk Analizi (FMEA)
              </h3>
              <div className="p-4 bg-[#030a10] border border-[#10293f] rounded-xl grid grid-cols-4 gap-2 text-center items-center">
                <div>
                  <p className="text-[9px] text-[#4f7b92]">Şiddet (S)</p>
                  <p className="text-lg font-bold font-mono text-[#e0f7fa] mt-1">{record.severity || 1}</p>
                </div>
                <div>
                  <p className="text-[9px] text-[#4f7b92]">Sıklık (O)</p>
                  <p className="text-lg font-bold font-mono text-[#e0f7fa] mt-1">{record.occurrence || 1}</p>
                </div>
                <div>
                  <p className="text-[9px] text-[#4f7b92]">Tespit (D)</p>
                  <p className="text-lg font-bold font-mono text-[#e0f7fa] mt-1">{record.detection || 1}</p>
                </div>
                <div className="border-l border-[#10293f] pl-2">
                  <p className="text-[9px] text-[#4f7b92]">Risk Skoru (RPN)</p>
                  <p className={`text-xl font-extrabold font-mono mt-1 ${severityColor}`}>{rpn}</p>
                </div>
              </div>
            </div>

            {/* Box 3: Root Cause Analysis (Ishikawa / 5-Why visualizer) */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest border-b border-[#10293f] pb-1.5 flex items-center gap-2">
                <Sparkles size={13} />
                3. Kök Neden Analizi Görselleştirme
              </h3>
              {renderRootCauseVisualization()}
            </div>
          </div>

          {/* RIGHT COLUMN: Actions, Yokoten, Lessons */}
          <div className="space-y-6">
            
            {/* Box 4: Target condition & corrective actions */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest border-b border-[#10293f] pb-1.5 flex items-center gap-2">
                <CheckCircle size={13} />
                4. Hedeflenen Eylemler & Önleyici Tedbirler
              </h3>
              <div className="p-4 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] leading-relaxed whitespace-pre-line">
                {record.corrective_actions || "Kalıcı düzeltici ve önleyici eylemler belirtilmemiş."}
              </div>
            </div>

            {/* Box 5: Lessons Learned */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest border-b border-[#10293f] pb-1.5 flex items-center gap-2">
                <Sparkles size={13} />
                5. Kurumsal Alınan Dersler (Lessons Learned)
              </h3>
              <div className="p-4 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#80deea] leading-relaxed whitespace-pre-line">
                {record.lessons_learned}
              </div>
            </div>

            {/* Box 6: Yokoten & Checklist */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest border-b border-[#10293f] pb-1.5 flex items-center gap-2">
                <Sparkles size={13} />
                6. Yatay Paylaşım (Yokoten) & Kapatma Kontrolü
              </h3>
              <div className="p-4 bg-[#030a10] border border-[#10293f] rounded-xl space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#4f7b92]">Yokoten Durumu:</span>
                  {record.yokoten_applied ? (
                    <span className="text-[10px] px-2.5 py-0.5 rounded bg-green-500/10 text-[#00e676] font-bold border border-green-500/30">
                      YAYGINLAŞTIRILDI
                    </span>
                  ) : (
                    <span className="text-[10px] px-2.5 py-0.5 rounded bg-[#10293f] text-[#4f7b92]">
                      LOKAL UYGULAMA
                    </span>
                  )}
                </div>

                {record.closure_checklist?.yokoten_scope && (
                  <div className="text-[11px] text-[#80deea] bg-cyan-950/30 p-2.5 rounded-lg border border-cyan-500/30">
                    <strong className="text-white block mb-0.5 font-mono text-[10px] uppercase">🌐 Yaygınlaştırma Kapsamı (Yokoten Target):</strong>
                    {record.closure_checklist.yokoten_scope}
                  </div>
                )}

                <div className="pt-2 border-t border-[#10293f]/50 space-y-2">
                  <p className="text-[10px] text-[#4f7b92] font-mono uppercase font-bold">KAPATMA KONTROL LİSTESİ:</p>
                  {record.closure_checklist?.checklist && Array.isArray(record.closure_checklist.checklist) ? (
                    record.closure_checklist.checklist.map((item: string, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 text-[#e0f7fa]">
                        <span className="w-3.5 h-3.5 rounded-full bg-green-500/20 text-[#00e676] border border-green-500/40 flex items-center justify-center text-[9px] font-bold shrink-0">✓</span>
                        <span className="leading-snug">{item}</span>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="flex items-center gap-2 text-[#e0f7fa]">
                        <span className="w-3.5 h-3.5 rounded-full bg-green-500/20 text-[#00e676] border border-green-500/40 flex items-center justify-center text-[9px] font-bold shrink-0">✓</span>
                        <span>Kök neden analizi ve saha doğrulaması tamamlandı</span>
                      </div>
                      <div className="flex items-center gap-2 text-[#e0f7fa]">
                        <span className="w-3.5 h-3.5 rounded-full bg-green-500/20 text-[#00e676] border border-green-500/40 flex items-center justify-center text-[9px] font-bold shrink-0">✓</span>
                        <span>Kalıcı düzeltici ve önleyici faaliyetler uygulandı</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Plan Tasks Section (at the bottom) */}
        {tasks.length > 0 && (
          <div className="pt-6 border-t border-[#10293f] space-y-3 no-print">
            <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2">
              <ListTodo size={13} />
              Bağlı Aksiyon Planı Görevleri
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {tasks.map((task) => {
                const completed = task.status === "completed";
                return (
                  <div key={task.id} className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-[#e0f7fa]">{task.title}</p>
                      <p className="text-[9px] text-[#4f7b92] mt-0.5">Sorumlu: {task.assignee_name || "Atanmamış"}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] px-2 py-0.5 rounded font-mono ${
                        completed ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
                      }`}>
                        {task.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
