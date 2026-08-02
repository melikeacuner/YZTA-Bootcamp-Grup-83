"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardStats, listTasks, updateTask } from "@/lib/api";
import { DashboardStats, TaskResponse } from "@/lib/types";
import { DEPARTMENT_PERSONNEL } from "./devops-board";
import { 
  Loader2, Activity, ShieldAlert, CheckCircle2, TrendingUp, Building2, Filter, 
  AlertCircle, Clock, UserCheck, Calendar, Edit3, X, Check, UserX, ChevronDown, ChevronUp 
} from "lucide-react";

export default function ManagerDashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDept, setSelectedDept] = useState<string>("Tüm Şirket");
  const [error, setError] = useState<string | null>(null);
  const [isCategoryOpen, setIsCategoryOpen] = useState(true);

  // Modal State for Task Assignment / Edit
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);
  const [editAssignee, setEditAssignee] = useState("");
  const [editDept, setEditDept] = useState("Kalite");
  const [editDeadline, setEditDeadline] = useState("");
  const [editStatus, setEditStatus] = useState("todo");
  const [editPriority, setEditPriority] = useState("medium");
  const [editReason, setEditReason] = useState("");
  const [modalError, setModalError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const loadData = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [statsData, taskList] = await Promise.all([
        getDashboardStats(token, selectedDept),
        listTasks(token)
      ]);
      setStats(statsData);
      setTasks(taskList);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setError("İstatistikler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [token, selectedDept]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function openAssignmentModal(task: TaskResponse) {
    setSelectedTask(task);
    setEditAssignee(task.assignee_name || "");
    setEditDept(task.department || "Kalite");
    setEditDeadline(task.deadline ? task.deadline.slice(0, 16) : "");
    setEditStatus(task.status === "delayed" || task.status === "completed" ? "todo" : task.status);
    setEditPriority(task.priority || "medium");
    setEditReason(task.proof_description || "");
    setModalError(null);
  }

  async function handleSaveAssignment(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !selectedTask) return;

    if (editStatus === "in_progress" || editStatus === "completed") {
      if (!editAssignee.trim() || !editDept.trim() || !editDeadline) {
        setModalError("Görevi 'Devam Edenler' durumuna almak için İsim (Sorumlu), Departman ve Termin Tarihi atanmalıdır.");
        return;
      }
    }

    if (editStatus === "on_hold" && !editReason.trim()) {
      setModalError("Görevi 'Beklemede (On Hold)' durumuna almak için konunun nerede beklediğine dair bir açıklama girilmelidir.");
      return;
    }

    setIsSaving(true);
    setModalError(null);
    try {
      await updateTask(token, selectedTask.id, {
        assignee_name: editAssignee || undefined,
        department: editDept || undefined,
        deadline: editDeadline || undefined,
        status: editStatus,
        priority: editPriority,
        proof_description: editReason || undefined
      });
      setSelectedTask(null);
      await loadData();
    } catch (err: any) {
      setModalError(err.message || "Görev ataması kaydedilemedi.");
    } finally {
      setIsSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">Yönetici Analitiği Yükleniyor...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-4 bg-red-950/20 border border-red-500/30 rounded-xl text-red-400 text-xs text-center max-w-md mx-auto mt-12">
        {error || "İstatistik verisi bulunmuyor."}
      </div>
    );
  }

  // Filter tasks based on selected department
  const filteredTasks = selectedDept === "Tüm Şirket" 
    ? tasks 
    : tasks.filter(t => t.department === selectedDept);

  // Unassigned tasks: missing assignee OR department OR deadline
  const unassignedTasks = filteredTasks.filter(
    (t) => !t.assignee_name || !t.department || !t.deadline
  );

  // Overdue tasks: status is delayed OR (past deadline AND not completed)
  const nowStr = new Date().toISOString();
  const overdueTasks = filteredTasks.filter(
    (t) => t.status === "delayed" || (t.deadline && t.deadline < nowStr && t.status !== "completed")
  );

  const completionRate = stats.total_problems > 0
    ? (stats.closed_problems / stats.total_problems) * 100
    : 0;

  // Helper to render customized CSS progress bars representing distribution percentages
  const renderBarChart = (data: Record<string, number> | undefined | null, color: string) => {
    const safeData = data || {};
    const total = Object.values(safeData).reduce((a, b) => a + b, 0);
    if (total === 0) return <p className="text-[10px] text-[#4f7b92] italic mt-2">Veri bulunmuyor</p>;

    return (
      <div className="space-y-3 pt-2">
        {Object.entries(safeData).map(([key, value]) => {
          const percentage = total > 0 ? (value / total) * 100 : 0;
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-[11px] text-[#80deea] font-medium pr-1">
                <span>{key}</span>
                <span className="font-mono text-[#e0f7fa] font-semibold">{value} vaka ({percentage.toFixed(0)}%)</span>
              </div>
              <div className="w-full h-2 bg-[#030a10] border border-[#10293f] rounded-full overflow-hidden">
                <div
                  style={{ width: `${percentage}%`, background: color }}
                  className="h-full rounded-full transition-all duration-500"
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const kpis = [
    {
      label: "Toplam Kayıtlı Problem",
      value: stats.total_problems,
      sub: selectedDept !== "Tüm Şirket" ? `${selectedDept} Departmanı` : "Şirket Genel Toplamı",
      icon: Activity,
      colorClass: "text-[#00e5ff] bg-cyan-500/5 border-cyan-500/20"
    },
    {
      label: "Çözülme Başarı Oranı",
      value: `${completionRate.toFixed(0)}%`,
      sub: `${stats.closed_problems} / ${stats.total_problems} problem çözüldü`,
      icon: CheckCircle2,
      colorClass: "text-[#00e676] bg-green-500/5 border-green-500/20"
    },
    {
      label: "Atanmamış Görev Sayısı",
      value: unassignedTasks.length,
      sub: unassignedTasks.length > 0 ? "Atama Bekliyor" : "Tüm Görevler Atanmış",
      icon: UserX,
      colorClass: unassignedTasks.length > 0 ? "text-amber-400 bg-amber-500/5 border-amber-500/20" : "text-[#80deea] bg-cyan-500/5 border-cyan-500/20"
    },
    {
      label: "Geciken Aksiyon Oranı",
      value: `${(stats.delayed_rate * 100).toFixed(0)}%`,
      sub: `${overdueTasks.length} geciken görev`,
      icon: TrendingUp,
      colorClass: "text-[#ff1744] bg-red-500/5 border-red-500/20"
    }
  ];

  return (
    <div className="w-full space-y-8 animate-fade-in pb-8">
      {/* Task Assignment Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-start justify-center pt-6 md:pt-10 px-4 pb-12 overflow-y-auto z-50 animate-fade-in">
          <div className="w-full max-w-lg bg-[#061320] border border-[#10293f] rounded-2xl p-6 shadow-2xl space-y-5 mt-2 md:mt-4">
            <div className="flex justify-between items-center border-b border-[#10293f] pb-3">
              <div>
                <h3 className="text-base font-bold text-[#e0f7fa] flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-[#00e5ff]" />
                  Görev Ataması & Yönetimi
                </h3>
                <p className="text-xs text-[#80deea] mt-0.5 font-mono">
                  Görev ID: #{selectedTask.id.slice(0, 8)}
                </p>
              </div>
              <button 
                onClick={() => setSelectedTask(null)}
                className="p-1 text-[#4f7b92] hover:text-white rounded-lg transition"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveAssignment} className="space-y-4">
              {modalError && (
                <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-red-300 text-xs flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{modalError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-[#80deea] mb-1">Görev Başlığı</label>
                <input 
                  type="text" 
                  value={selectedTask.title} 
                  disabled
                  className="w-full bg-[#030a10] border border-[#10293f] rounded-xl p-2.5 text-xs text-[#4f7b92] cursor-not-allowed font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Departman */}
                <div>
                  <label className="block text-xs font-semibold text-[#80deea] mb-1">Departman *</label>
                  <select
                    value={editDept}
                    onChange={(e) => {
                      setEditDept(e.target.value);
                      setEditAssignee("");
                    }}
                    className="w-full bg-[#030a10] border border-[#10293f] rounded-xl p-2.5 text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition"
                    required
                  >
                    <option value="Üretim">Üretim</option>
                    <option value="Lojistik">Lojistik</option>
                    <option value="Kalite">Kalite</option>
                    <option value="Bilgi İşlem">Bilgi İşlem</option>
                    <option value="Finans">Finans</option>
                  </select>
                </div>

                {/* Sorumlu Kişi */}
                <div>
                  <label className="block text-xs font-semibold text-[#80deea] mb-1">Sorumlu İsim *</label>
                  <select
                    value={editAssignee}
                    onChange={(e) => setEditAssignee(e.target.value)}
                    className="w-full bg-[#030a10] border border-[#10293f] rounded-xl p-2.5 text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition"
                  >
                    <option value="">-- Kişi Seçin --</option>
                    {DEPARTMENT_PERSONNEL[editDept]?.map((person) => (
                      <option key={person} value={person}>
                        {person}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Serbest İsim Girişi Alternatifi */}
              <div>
                <label className="block text-[11px] text-[#4f7b92] mb-1">
                  Veya özel isim yazın (Örn: Ahmet Yılmaz)
                </label>
                <input
                  type="text"
                  placeholder="Atanacak kişi adı ve unvanı..."
                  value={editAssignee}
                  onChange={(e) => setEditAssignee(e.target.value)}
                  className="w-full bg-[#030a10] border border-[#10293f] rounded-xl p-2.5 text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Termin Tarihi */}
                <div>
                  <label className="block text-xs font-semibold text-[#80deea] mb-1">Termin Tarihi *</label>
                  <input
                    type="datetime-local"
                    value={editDeadline}
                    onChange={(e) => setEditDeadline(e.target.value)}
                    className="w-full bg-[#030a10] border border-[#10293f] rounded-xl p-2.5 text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition"
                  />
                </div>

                {/* Durum */}
                <div>
                  <label className="block text-xs font-semibold text-[#80deea] mb-1">Görev Durumu</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="w-full bg-[#030a10] border border-[#10293f] rounded-xl p-2.5 text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition"
                  >
                    <option value="todo">📋 Yapılacaklar (Todo)</option>
                    <option value="in_progress">⚡ Devam Edenler (In Progress)</option>
                    <option value="on_hold">⏸️ Beklemede (On Hold)</option>
                  </select>
                </div>
              </div>

              {/* On Hold Reason Field */}
              {editStatus === "on_hold" && (
                <div>
                  <label className="block text-xs font-semibold text-amber-300 mb-1">
                    Bekleme Nedeni (Konunun nerede/neden beklediği açıklaması) *
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Örn: İthalat parçası gümrük onayında bekleniyor / Tedarikçi teknik incelemesi devam ediyor..."
                    value={editReason}
                    onChange={(e) => setEditReason(e.target.value)}
                    className="w-full bg-[#030a10] border border-amber-500/40 rounded-xl p-2.5 text-xs text-[#e0f7fa] focus:border-amber-400 transition"
                    required
                  />
                </div>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-[#10293f]">
                <button
                  type="button"
                  onClick={() => setSelectedTask(null)}
                  className="px-4 py-2 bg-[#030a10] border border-[#10293f] text-[#80deea] hover:text-white text-xs rounded-xl transition font-semibold"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-5 py-2 bg-[#00e5ff] hover:bg-[#00b0ff] text-[#030a10] font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                >
                  {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check size={16} />}
                  Atamayı Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Header and Department Filter Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#10293f] pb-4">
        <div>
          <h2 className="text-2xl font-bold text-[#e0f7fa]">Yönetici Dashboardu (Executive BI)</h2>
          <p className="text-xs text-[#80deea] mt-1">
            Departman bazlı ve genel şirket seviyesinde problem çözme performansı, FMEA riskleri ve görev atamaları.
          </p>
        </div>

        {/* Department Filter Selector */}
        <div className="flex items-center gap-2 bg-[#061320] border border-[#10293f] p-2 rounded-xl">
          <Building2 className="w-4 h-4 text-[#00e5ff]" />
          <span className="text-xs font-semibold text-[#80deea]">Filtre:</span>
          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="bg-[#030a10] border border-[#10293f] rounded-lg text-xs text-[#e0f7fa] p-2 font-bold focus:border-[#00e5ff] transition"
          >
            <option value="Tüm Şirket">🌐 Tüm Şirket (Overall)</option>
            <option value="Üretim">🏭 Üretim</option>
            <option value="Lojistik">🚚 Lojistik</option>
            <option value="Kalite">🎯 Kalite</option>
            <option value="Bilgi İşlem">💻 Bilgi İşlem</option>
            <option value="Finans">📊 Finans</option>
          </select>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <div key={idx} className={`p-5 glass rounded-xl flex items-center justify-between shadow-md relative overflow-hidden ${kpi.colorClass}`}>
            <div className="space-y-1.5 overflow-hidden">
              <span className="text-[10px] uppercase font-semibold tracking-wider text-[#4f7b92] block">{kpi.label}</span>
              <span className="text-2xl font-bold font-mono tracking-tight text-[#e0f7fa]">{kpi.value}</span>
              {kpi.sub && <span className="text-[10px] text-[#4f7b92] block truncate">{kpi.sub}</span>}
            </div>
            <div className="p-3 rounded-lg bg-[#030a10] border border-[#10293f] text-inherit">
              <kpi.icon size={20} />
            </div>
          </div>
        ))}
      </div>

      {/* Management Tables: Unassigned Tasks & Overdue Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unassigned Tasks Section */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5 border border-amber-500/20">
          <div className="border-b border-[#10293f] pb-3 flex justify-between items-center">
            <div>
              <h3 className="text-xs font-bold text-amber-300 uppercase tracking-widest flex items-center gap-2">
                <UserX className="w-4 h-4 text-amber-400" />
                Atanmamış Görevler ({unassignedTasks.length})
              </h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">Sorumlu kişi, departman veya termin tarihi atanmayı bekleyen aksiyonlar</p>
            </div>
          </div>

          {unassignedTasks.length === 0 ? (
            <div className="p-6 text-center text-xs text-emerald-400/80 bg-emerald-950/20 border border-emerald-500/20 rounded-xl">
              ✅ Atanmamış görev bulunmuyor. Tüm aksiyonların sorumlusu ve terminii tanımlı.
            </div>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {unassignedTasks.map((t) => (
                <div key={t.id} className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl flex items-center justify-between gap-3 hover:border-amber-500/40 transition">
                  <div className="space-y-1 min-w-0 flex-1">
                    <p className="text-xs font-bold text-[#e0f7fa] truncate">{t.title}</p>
                    <div className="flex flex-wrap gap-2 text-[10px] text-[#4f7b92]">
                      <span>Departman: <strong className="text-[#80deea]">{t.department || "Atanmadı"}</strong></span>
                      <span>Sorumlu: <strong className="text-[#80deea]">{t.assignee_name || "Atanmadı"}</strong></span>
                      <span>Termin: <strong className="text-[#80deea]">{t.deadline ? new Date(t.deadline).toLocaleDateString("tr-TR") : "Atanmadı"}</strong></span>
                    </div>
                  </div>
                  <button
                    onClick={() => openAssignmentModal(t)}
                    className="px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-bold rounded-lg transition shrink-0 flex items-center gap-1"
                  >
                    <Edit3 size={14} />
                    Atama Yap
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Overdue Tasks Section */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5 border border-red-500/20">
          <div className="border-b border-[#10293f] pb-3 flex justify-between items-center">
            <div>
              <h3 className="text-xs font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
                <Clock className="w-4 h-4 text-red-400" />
                Termini Geçen Görevler ({overdueTasks.length})
              </h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">Planlanan termin tarihi dolmuş ve henüz tamamlanmamış aksiyonlar</p>
            </div>
          </div>

          {overdueTasks.length === 0 ? (
            <div className="p-6 text-center text-xs text-emerald-400/80 bg-emerald-950/20 border border-emerald-500/20 rounded-xl">
              🎉 Harika! Termini geçen hiçbir aksiyon bulunmuyor.
            </div>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {overdueTasks.map((t) => (
                <div key={t.id} className="p-3 bg-red-950/20 border border-red-500/30 rounded-xl flex items-center justify-between gap-3 hover:border-red-500/60 transition">
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 text-[9px] font-bold bg-red-500/20 text-red-300 border border-red-500/40 rounded uppercase">
                        Gecikti
                      </span>
                      <p className="text-xs font-bold text-[#e0f7fa] truncate">{t.title}</p>
                    </div>
                    <div className="flex flex-wrap gap-2 text-[10px] text-[#4f7b92]">
                      <span>Sorumlu: <strong className="text-[#80deea]">{t.assignee_name || "Belirtilmedi"}</strong> ({t.department || "N/A"})</span>
                      <span>Son Tarih: <strong className="text-red-400">{t.deadline ? new Date(t.deadline).toLocaleDateString("tr-TR") : "Belirtilmedi"}</strong></span>
                    </div>
                  </div>
                  <button
                    onClick={() => openAssignmentModal(t)}
                    className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/40 text-red-300 text-xs font-bold rounded-lg transition shrink-0 flex items-center gap-1"
                  >
                    <Edit3 size={14} />
                    Düzenle / Uzat
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Distributions Charts Panel (Departman & Metodoloji) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Department */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3 flex justify-between items-center">
            <div>
              <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Departman Dağılımı</h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">Departmanların vaka yükü</p>
            </div>
            <span className="text-[10px] font-mono text-[#00e5ff]">{selectedDept}</span>
          </div>
          {renderBarChart(stats.department_distribution, "linear-gradient(90deg, #00e5ff, #00b0ff)")}
        </div>

        {/* Methodologies */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3 flex justify-between items-center">
            <div>
              <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Metodoloji Kullanımı</h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">Problem çözmede tercih edilen araçlar</p>
            </div>
          </div>
          {renderBarChart(stats.methodology_distribution, "linear-gradient(90deg, #00e676, #ffea00)")}
        </div>
      </div>

      {/* FMEA Risk Heatmap Matrix & Department KPI Matrix + Collapsible Category Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* FMEA RPN Risk Heatmap (3x3 Matrix) */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3 flex justify-between items-center">
            <div>
              <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                FMEA Risk Isı Haritası (RPN Heatmap)
              </h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">Şiddet (Severity) vs Olasılık (Occurrence) Risk Dağılım Matrisi</p>
            </div>
            <span className="text-[10px] font-mono text-cyan-400 font-bold bg-cyan-500/10 border border-cyan-500/20 px-2 py-1 rounded">
              RPN = S × O × D
            </span>
          </div>

          {/* 3x3 Heatmap Grid */}
          <div className="space-y-2 pt-1">
            <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-mono text-[#80deea] font-semibold">
              <div></div>
              <div className="bg-[#061320] p-1 rounded border border-[#10293f]">Düşük Olasılık (1-3)</div>
              <div className="bg-[#061320] p-1 rounded border border-[#10293f]">Orta Olasılık (4-6)</div>
              <div className="bg-[#061320] p-1 rounded border border-[#10293f]">Yüksek Olasılık (7-10)</div>
            </div>

            {/* Row 1: High Severity (8-10) */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="flex items-center justify-center font-bold text-[10px] text-red-400 bg-[#061320] p-2 rounded border border-[#10293f]">
                Yüksek Şiddet (8-10)
              </div>
              <div className="bg-amber-950/40 border border-amber-500/30 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-amber-300 text-sm">Yüksek</span>
                <span className="text-[10px] text-amber-400/80 font-mono">1 vaka</span>
              </div>
              <div className="bg-red-950/60 border border-red-500/40 p-3 rounded-lg flex flex-col items-center justify-center animate-pulse">
                <span className="font-bold font-mono text-red-300 text-sm">Kritik</span>
                <span className="text-[10px] text-red-400/80 font-mono">2 vaka</span>
              </div>
              <div className="bg-red-950/80 border border-red-500/60 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-red-200 text-sm">Acil Risk</span>
                <span className="text-[10px] text-red-300 font-mono">1 vaka</span>
              </div>
            </div>

            {/* Row 2: Medium Severity (4-7) */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="flex items-center justify-center font-bold text-[10px] text-yellow-400 bg-[#061320] p-2 rounded border border-[#10293f]">
                Orta Şiddet (4-7)
              </div>
              <div className="bg-emerald-950/30 border border-emerald-500/20 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-emerald-300 text-sm">Düşük</span>
                <span className="text-[10px] text-emerald-400/80 font-mono">1 vaka</span>
              </div>
              <div className="bg-amber-950/40 border border-amber-500/30 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-amber-300 text-sm">Orta</span>
                <span className="text-[10px] text-amber-400/80 font-mono">2 vaka</span>
              </div>
              <div className="bg-red-950/40 border border-red-500/30 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-red-300 text-sm">Yüksek</span>
                <span className="text-[10px] text-red-400/80 font-mono">1 vaka</span>
              </div>
            </div>

            {/* Row 3: Low Severity (1-3) */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="flex items-center justify-center font-bold text-[10px] text-emerald-400 bg-[#061320] p-2 rounded border border-[#10293f]">
                Düşük Şiddet (1-3)
              </div>
              <div className="bg-emerald-950/50 border border-emerald-500/30 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-emerald-300 text-sm">Minimal</span>
                <span className="text-[10px] text-emerald-400/80 font-mono">1 vaka</span>
              </div>
              <div className="bg-emerald-950/30 border border-emerald-500/20 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-emerald-300 text-sm">Düşük</span>
                <span className="text-[10px] text-emerald-400/80 font-mono">0 vaka</span>
              </div>
              <div className="bg-amber-950/30 border border-amber-500/20 p-3 rounded-lg flex flex-col items-center justify-center">
                <span className="font-bold font-mono text-amber-300 text-sm">Orta</span>
                <span className="text-[10px] text-amber-400/80 font-mono">0 vaka</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Department KPI Matrix + Bottom-Right Collapsible Kategori Dağılımı */}
        <div className="space-y-6 flex flex-col justify-between">
          {/* Department KPI Matrix */}
          <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
            <div>
              <div className="border-b border-[#10293f] pb-3">
                <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Departman Risk & Performans Matrisi</h3>
                <p className="text-[10px] text-[#4f7b92] mt-0.5">Birimlerin aktif problem sayısı ve risk durumları</p>
              </div>
              <div className="overflow-x-auto pt-2">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#10293f] text-[#80deea] font-semibold text-[10px] uppercase font-mono">
                      <th className="py-2.5">Departman</th>
                      <th className="py-2.5 text-center">Vaka Yükü</th>
                      <th className="py-2.5 text-center">Risk Seviyesi</th>
                      <th className="py-2.5 text-right">Durum</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#10293f]/40 text-[#e0f7fa]">
                    {Object.entries(stats.department_distribution).map(([dept, count]) => {
                      const riskLevel = count > 3 ? "Yüksek Risk" : count > 1 ? "Orta Risk" : "Düşük Risk";
                      const statusColor = count > 3 ? "text-red-400 bg-red-500/10 border-red-500/20" : count > 1 ? "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" : "text-green-400 bg-green-500/10 border-green-500/20";
                      return (
                        <tr key={dept} className="hover:bg-[#061320]/40 transition-colors">
                          <td className="py-3 font-semibold text-sm">{dept}</td>
                          <td className="py-3 text-center font-mono font-bold text-[#00e5ff]">{count}</td>
                          <td className="py-3 text-center">
                            <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${statusColor}`}>
                              {riskLevel}
                            </span>
                          </td>
                          <td className="py-3 text-right">
                            <span className="text-[10px] text-[#4f7b92] font-mono">Takipte</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-3 bg-gradient-to-r from-cyan-950/30 to-purple-950/30 border border-cyan-500/30 rounded-xl text-[11px] text-[#80deea] leading-relaxed mt-4">
              <strong className="text-white block mb-1">💡 Yönetici Tavsiyesi:</strong>
              {selectedDept !== "Tüm Şirket" ? `${selectedDept} departmanındaki` : "Tüm şirketteki"} aksiyon planlarının zamanında kapatılmasını DevOps Aksiyon Paneli üzerinden denetleyebilir ve aksiyon sorumlularını takip edebilirsiniz.
            </div>
          </div>

          {/* En Sağ Alt: Açılır Kapanır Kategori Dağılımı */}
          <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-purple-500/10 border border-purple-500/30">
            <button
              type="button"
              onClick={() => setIsCategoryOpen(!isCategoryOpen)}
              className="w-full flex items-center justify-between border-b border-[#10293f] pb-3 text-left focus:outline-none group cursor-pointer"
            >
              <div>
                <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest flex items-center gap-2">
                  <Filter className="w-4 h-4 text-purple-400" />
                  Kategori Dağılımı
                </h3>
                <p className="text-[10px] text-[#4f7b92] mt-0.5">En sık karşılaşılan kök problem tipleri</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 rounded font-mono">
                  {isCategoryOpen ? "Daralt ▲" : "Aşağı Aç ▼"}
                </span>
                {isCategoryOpen ? (
                  <ChevronUp className="w-4 h-4 text-purple-400 group-hover:text-white transition" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-purple-400 group-hover:text-white transition" />
                )}
              </div>
            </button>

            {isCategoryOpen && (
              <div className="animate-fade-in pt-1">
                {renderBarChart(stats.category_distribution, "linear-gradient(90deg, #7c4dff, #ff1744)")}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
