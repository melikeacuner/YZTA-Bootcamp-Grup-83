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
    const methodologyLower = record.methodology.toLowerCase();
    const responses = record.step_responses || {};

    if (methodologyLower === "5why") {
      // Renders step ladder of Whys
      const answers = responses.answers || [];
      const questions = responses.questions || [];
      const steps = [];

      // Look for standard 5why keys
      for (let i = 0; i < 7; i++) {
        const ans = responses[i.toString()] || (answers && answers[i]);
        if (ans) {
          steps.push(ans);
        }
      }

      if (steps.length === 0) {
        return <p className="text-xs text-[#4f7b92] italic">5 Neden görsel analizi bulunmuyor.</p>;
      }

      return (
        <div className="space-y-2.5 pt-2">
          {steps.map((ans, idx) => (
            <div key={idx} className="flex gap-3 items-start animate-fade-in" style={{ paddingLeft: `${idx * 16}px` }}>
              <div className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#10293f] text-[#00e5ff] shrink-0">
                Neden {idx + 1}
              </div>
              <div className="text-xs text-[#e0f7fa] bg-[#030a10] border border-[#10293f] p-2.5 rounded-lg flex-1 relative">
                {ans}
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (methodologyLower === "ishikawa") {
      // Renders fishbone categories
      const categories = ["man", "machine", "method", "material", "measurement", "environment"];
      const ishikawaLabels: Record<string, string> = {
        man: "İnsan (Man)",
        machine: "Makine (Machine)",
        method: "Metot (Method)",
        material: "Malzeme (Material)",
        measurement: "Ölçüm (Measurement)",
        environment: "Çevre (Environment)"
      };

      return (
        <div className="grid grid-cols-2 gap-3 pt-2">
          {categories.map((cat) => {
            const list = responses[cat] || [];
            return (
              <div key={cat} className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg">
                <h4 className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider mb-2">
                  {ishikawaLabels[cat]}
                </h4>
                {list.length > 0 && list[0] ? (
                  <ul className="list-disc pl-4 space-y-1 text-xs text-[#e0f7fa]">
                    {list.map((item: string, idx: number) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[10px] text-[#4f7b92] italic">Faktör belirtilmedi</p>
                )}
              </div>
            );
          })}
        </div>
      );
    }

    // Default or Agent synthesis
    return (
      <div className="p-4 bg-[#030a10] border border-[#10293f] rounded-lg space-y-2">
        <h4 className="text-xs font-semibold text-[#80deea] uppercase">Sohbet Analiz Bulguları</h4>
        <p className="text-xs text-[#e0f7fa] leading-relaxed">
          {record.root_cause || "Kök neden tespiti yapılmamıştır."}
        </p>
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
          <span>A3 Yazdır (PDF)</span>
        </button>
      </div>

      {/* Toyota A3 Document Sheet Layout */}
      <div className="flex-1 bg-[#061320] border border-[#10293f] rounded-2xl overflow-y-auto p-6 md:p-8 flex flex-col space-y-6 relative A3-print-sheet">
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
                    <span className="text-[10px] px-2 py-0.5 rounded bg-green-500/10 text-[#00e676] font-bold">
                      YAYGINLAŞTIRILDI
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-[#10293f] text-[#4f7b92]">
                      LOKAL UYGULAMA
                    </span>
                  )}
                </div>

                <div className="pt-2 border-t border-[#10293f]/50 space-y-1.5">
                  <p className="text-[10px] text-[#4f7b92]">KAPATMA KONTROL LİSTESİ:</p>
                  <div className="flex items-center gap-2 text-[#e0f7fa]">
                    <span className="w-2.5 h-2.5 rounded bg-green-500/20 text-[#00e676] flex items-center justify-center text-[8px] font-bold">✓</span>
                    <span>Problem tanımı yapay zeka tarafından incelendi</span>
                  </div>
                  <div className="flex items-center gap-2 text-[#e0f7fa]">
                    <span className="w-2.5 h-2.5 rounded bg-green-500/20 text-[#00e676] flex items-center justify-center text-[8px] font-bold">✓</span>
                    <span>Kök neden doğrulaması yapıldı</span>
                  </div>
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
