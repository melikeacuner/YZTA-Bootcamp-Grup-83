"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { listTasks, createTask, updateTask, deleteTask, listRecords } from "@/lib/api";
import { TaskResponse, RecordResponse } from "@/lib/types";

import { Plus, X, Calendar, User as UserIcon, Loader2, AlertTriangle, CheckSquare, ArrowUpRight } from "lucide-react";

interface DevOpsBoardProps {
  onViewReport?: (recordId: string) => void;
}

export const DEPARTMENT_PERSONNEL: Record<string, string[]> = {
  "Üretim": ["Mehmet Can (Bakım Mühendisi)", "Ali Öztürk (Üretim Sorumlusu)", "Kadir Şen (Montaj Şefi)", "Hasan Kaya (Bakım Şefi)"],
  "Lojistik": ["Fatma Şahin (Tesis Sorumlusu)", "Caner Kaya (Operasyon Direktörü)", "Volkan Aydoğan (Depo Şefi)"],
  "Kalite": ["Ahmet Yılmaz (Kalite Uzmanı)", "Merve Şahin (Kalite Mühendisi)", "Mehmet Demir (Üretim Müdürü)"],
  "Bilgi İşlem": ["Burak Öz (Kıdemli Backend Geliştirici)", "Selin Arslan (Software Lead)", "Ahmet Yılmaz (Kıdemli Bulut Mimar)", "Deniz Er (IT Ops Manager)"],
  "Finans": ["Zeynep Avcı (Mali İşler Uzmanı)", "Emre Yıldız (Finansal Analist)"]
};

export default function DevOpsBoard({ onViewReport }: DevOpsBoardProps) {
  const { token } = useAuth();
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [records, setRecords] = useState<RecordResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [selectedDept, setSelectedDept] = useState<string>("All");
  const [selectedAssignee, setSelectedAssignee] = useState<string>("All");
  const [selectedPriority, setSelectedPriority] = useState<string>("All");
  const [overdueStart, setOverdueStart] = useState<string>("");
  const [overdueEnd, setOverdueEnd] = useState<string>("");

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);

  // Form States (New Task)
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newAssignee, setNewAssignee] = useState("");
  const [newDept, setNewDept] = useState("Kalite");
  const [newPriority, setNewPriority] = useState("medium");
  const [newDeadline, setNewDeadline] = useState("");
  const [newRecordId, setNewRecordId] = useState<string>("");

  // Form States (Update Task)
  const [updateStatus, setUpdateStatus] = useState<string>("todo");
  const [updateAssignee, setUpdateAssignee] = useState("");
  const [updateDept, setUpdateDept] = useState("");
  const [updatePriority, setUpdatePriority] = useState("medium");
  const [updateDeadline, setUpdateDeadline] = useState("");
  const [proofDesc, setProofDesc] = useState("");
  const [proofUrl, setProofUrl] = useState("");

  const loadData = useCallback(async () => {
    if (!token) return;
    try {
      const taskList = await listTasks(token);
      setTasks(taskList);
      const recordList = await listRecords(token, 1, 100);
      setRecords(recordList.items || []);
    } catch (err) {
      console.error("Failed to load tasks:", err);
      setError("Görevler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !newTitle.trim()) return;

    try {
      await createTask(token, {
        title: newTitle,
        description: newDesc || undefined,
        assignee_name: newAssignee || undefined,
        department: newDept || undefined,
        priority: newPriority,
        deadline: newDeadline || undefined,
        problem_record_id: newRecordId || null
      });
      // Reset forms
      setNewTitle("");
      setNewDesc("");
      setNewAssignee("");
      setNewDept("Kalite");
      setNewPriority("medium");
      setNewDeadline("");
      setNewRecordId("");
      setShowAddModal(false);
      loadData();
    } catch (err: any) {
      setError(err.message || "Görev oluşturulamadı.");
    }
  }

  async function handleUpdateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !selectedTask) return;

    if (updateStatus === "in_progress" || updateStatus === "completed") {
      if (!updateAssignee.trim() || !updateDept.trim() || !updateDeadline) {
        setError("Görevi 'Devam Edenler' veya 'Tamamlananlar' durumuna almak için İsim (Sorumlu), Departman ve Termin Tarihi atanmalıdır.");
        return;
      }
    }

    if (updateStatus === "on_hold" && !proofDesc.trim()) {
      setError("Görevi 'Beklemede (On Hold)' durumuna almak için konunun nerede beklediğine dair bir açıklama girilmelidir.");
      return;
    }

    try {
      await updateTask(token, selectedTask.id, {
        status: updateStatus,
        assignee_name: updateAssignee || undefined,
        department: updateDept || undefined,
        priority: updatePriority,
        deadline: updateDeadline || undefined,
        proof_description: proofDesc || undefined,
        proof_url: proofUrl || undefined
      });
      setSelectedTask(null);
      loadData();
    } catch (err: any) {
      setError(err.message || "Görev güncellenemedi.");
    }
  }

  async function handleDeleteTask(taskId: string) {
    if (!token || !confirm("Bu görevi silmek istediğinize emin misiniz?")) return;
    try {
      await deleteTask(token, taskId);
      setSelectedTask(null);
      loadData();
    } catch (err: any) {
      setError(err.message || "Görev silinemedi.");
    }
  }

  function openUpdateModal(task: TaskResponse) {
    setSelectedTask(task);
    setUpdateStatus(task.status);
    setUpdateAssignee(task.assignee_name || "");
    setUpdateDept(task.department || "Kalite");
    setUpdatePriority(task.priority || "medium");
    setUpdateDeadline(task.deadline ? task.deadline.slice(0, 16) : "");
    setProofDesc(task.proof_description || "");
    setProofUrl(task.proof_url || "");
  }

  const recordMap = new Map(records.map((r) => [r.id, r]));

  const nowIso = new Date().toISOString();

  // Process and filter tasks, auto-routing overdue tasks to delayed status if not completed
  const processedTasks: TaskResponse[] = tasks.map((t) => {
    if (t.deadline && t.deadline < nowIso && t.status !== "completed") {
      return { ...t, status: "delayed" as const };
    }
    return t;
  });

  const filteredTasks = processedTasks.filter((t) => {
    // Filter by assignee
    if (selectedAssignee !== "All" && t.assignee_name !== selectedAssignee) {
      return false;
    }
    // Filter by priority
    if (selectedPriority !== "All" && t.priority !== selectedPriority) {
      return false;
    }
    // Filter by department
    if (selectedDept !== "All") {
      const taskDept = t.department || (t.problem_record_id ? recordMap.get(t.problem_record_id)?.department : "Kalite");
      if (taskDept !== selectedDept) {
        return false;
      }
    }
    // Filter by overdue / deadline range
    if (overdueStart && t.deadline) {
      if (t.deadline < overdueStart) return false;
    }
    if (overdueEnd && t.deadline) {
      if (t.deadline > overdueEnd) return false;
    }
    return true;
  });

  const columns = [
    { id: "todo", title: "Yapılacaklar", colorClass: "border-cyan-500/20 text-cyan-400" },
    { id: "in_progress", title: "Devam Edenler", colorClass: "border-purple-500/20 text-purple-400" },
    { id: "completed", title: "Tamamlananlar", colorClass: "border-green-500/20 text-green-400" },
    { id: "delayed", title: "Gecikenler (Overdue)", colorClass: "border-red-500/20 text-red-400" },
  ];

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">Aksiyon Planı Yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="w-full flex-1 flex flex-col space-y-6 overflow-hidden animate-fade-in">
      {/* Board Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between shrink-0 gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-[#e0f7fa]">DevOps Aksiyon Paneli</h2>
          <p className="text-xs text-[#80deea]">Çözüme ulaştırılan problemlerin düzeltici eylem planlarını takip edin.</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn btn-primary text-xs py-2 px-4 flex items-center gap-1.5 w-full sm:w-auto justify-center">
          <Plus size={14} />
          <span>Yeni Aksiyon Ekle</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg text-xs text-red-400 shrink-0">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="p-4 bg-[#061320] border border-[#10293f] rounded-xl flex flex-wrap gap-4 items-center justify-between shrink-0">
        <div className="flex flex-wrap gap-4 items-center w-full lg:w-auto">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-[#4f7b92] font-semibold">Departman:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="p-2 bg-[#030a10] border border-[#10293f] rounded-lg text-xs text-[#e0f7fa] focus:border-[#00e5ff]"
            >
              <option value="All">Tüm Departmanlar</option>
              <option value="Üretim">Üretim</option>
              <option value="Lojistik">Lojistik</option>
              <option value="Kalite">Kalite</option>
              <option value="Bilgi İşlem">Bilgi İşlem</option>
              <option value="Finans">Finans</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-[#4f7b92] font-semibold">Sorumlu:</span>
            <select
              value={selectedAssignee}
              onChange={(e) => setSelectedAssignee(e.target.value)}
              className="p-2 bg-[#030a10] border border-[#10293f] rounded-lg text-xs text-[#e0f7fa] focus:border-[#00e5ff]"
            >
              <option value="All">Tüm Kişiler</option>
              {Array.from(new Set(tasks.map((t) => t.assignee_name).filter(Boolean))).map((name) => (
                <option key={name} value={name!}>{name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-[#4f7b92] font-semibold">Öncelik:</span>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="p-2 bg-[#030a10] border border-[#10293f] rounded-lg text-xs text-[#e0f7fa] focus:border-[#00e5ff]"
            >
              <option value="All">Tümü</option>
              <option value="critical">Critical (Kritik)</option>
              <option value="high">High (Yüksek)</option>
              <option value="medium">Medium (Orta)</option>
              <option value="low">Low (Düşük)</option>
            </select>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-[#4f7b92]">
            <span className="font-semibold uppercase tracking-wider">Gecikme:</span>
            <input
              type="date"
              value={overdueStart}
              onChange={(e) => setOverdueStart(e.target.value)}
              className="p-1.5 bg-[#030a10] border border-[#10293f] rounded text-[10px] text-[#e0f7fa]"
            />
            <span>-</span>
            <input
              type="date"
              value={overdueEnd}
              onChange={(e) => setOverdueEnd(e.target.value)}
              className="p-1.5 bg-[#030a10] border border-[#10293f] rounded text-[10px] text-[#e0f7fa]"
            />
          </div>
        </div>
        <div className="text-[10px] text-[#4f7b92] font-mono">
          Toplam: {filteredTasks.length} / {tasks.length} Görev
        </div>
      </div>

      {/* Kanban Grid */}
      <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 overflow-y-auto h-full pb-4">
        {columns.map((col) => {
          const colTasks = filteredTasks.filter((t) => t.status === col.id);
          return (
            <div key={col.id} className="flex flex-col h-full glass rounded-xl overflow-hidden shadow-lg shadow-cyan-500/5">
              {/* Header */}
              <div className={`p-4 border-b border-[#10293f] flex items-center justify-between font-bold text-xs ${col.colorClass}`}>
                <span>{col.title}</span>
                <span className="px-2 py-0.5 rounded bg-[#10293f] text-[#4f7b92] text-[10px] font-mono">
                  {colTasks.length}
                </span>
              </div>
              
              {/* Task Cards Stack */}
              <div className="flex-1 p-3 space-y-3 overflow-y-auto">
                {colTasks.length === 0 ? (
                  <p className="text-[10px] text-[#4f7b92] text-center mt-6">Görev bulunmuyor.</p>
                ) : (
                  colTasks.map((task) => {
                    const isDelayed = task.status === "delayed";
                    const linkedRecord = task.problem_record_id ? recordMap.get(task.problem_record_id) : null;
                    // Rule: A3 Report link ONLY visible for completed/closed problems
                    const isRecordClosed = linkedRecord && (linkedRecord.resolution_status === "completed" || linkedRecord.resolution_status === "closed");

                    return (
                      <div
                        key={task.id}
                        onClick={() => openUpdateModal(task)}
                        className={`p-3 bg-[#030a10] border rounded-lg cursor-pointer hover:bg-[#0a1f33] transition-all relative overflow-hidden group ${
                          isDelayed
                            ? "border-red-500/40 shadow-sm shadow-red-500/10"
                            : "border-[#10293f] hover:border-cyan-500/35"
                        }`}
                      >
                        {isDelayed && (
                          <div className="absolute top-0 right-0 p-1 text-red-500 dot-pulse">
                            <AlertTriangle size={11} />
                          </div>
                        )}
                        <div className="flex items-center justify-between gap-2">
                          <h4 className="text-xs font-semibold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors line-clamp-2">
                            {task.title}
                          </h4>
                          <span className={`text-[8px] px-1.5 py-0.5 rounded font-mono uppercase font-bold shrink-0 ${
                            task.priority === "critical"
                              ? "bg-red-500/20 text-red-400 border border-red-500/30"
                              : task.priority === "high"
                              ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                              : task.priority === "low"
                              ? "bg-green-500/20 text-green-400 border border-green-500/30"
                              : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                          }`}>
                            {task.priority || "medium"}
                          </span>
                        </div>
                        {task.description && (
                          <p className="text-[10px] text-[#4f7b92] mt-1.5 line-clamp-2">
                            {task.description}
                          </p>
                        )}
                        
                        {/* Meta info footer */}
                        <div className="mt-3 flex items-center justify-between text-[9px] text-[#4f7b92] pt-2 border-t border-[#10293f]/50">
                          <span className="flex items-center gap-1">
                            <UserIcon size={10} className="text-[#00e5ff]" />
                            <span className="truncate max-w-[70px]">{task.assignee_name || "Atanmamış"}</span>
                          </span>
                          <span className="text-[9px] text-[#80deea]">
                            {task.department || "Kalite"}
                          </span>
                          {task.deadline && (
                            <span className="flex items-center gap-1 font-mono">
                              <Calendar size={10} />
                              <span>{new Date(task.deadline).toLocaleDateString("tr-TR")}</span>
                            </span>
                          )}
                        </div>

                        {/* A3 Report Link: ONLY rendered if problem is completed/closed */}
                        {task.problem_record_id && isRecordClosed && onViewReport && (
                          <div className="mt-2.5 pt-2 border-t border-[#10293f]/30 flex justify-end">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                onViewReport(task.problem_record_id!);
                              }}
                              className="text-[9px] text-[#00e5ff] hover:text-[#7c4dff] hover:underline flex items-center gap-0.5 font-semibold"
                            >
                              <span>A3 Raporuna Git</span>
                              <ArrowUpRight size={10} />
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Add Task */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="w-full max-w-md bg-[#061320] border border-[#10293f] rounded-xl overflow-hidden shadow-2xl relative">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />
            <div className="p-4 border-b border-[#10293f] flex items-center justify-between">
              <h3 className="font-bold text-sm text-[#e0f7fa]">Yeni Aksiyon Görevi Ekle</h3>
              <button onClick={() => setShowAddModal(false)} className="text-[#4f7b92] hover:text-red-500">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleCreateTask} className="p-4 space-y-4 text-xs">
              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">Görev Başlığı *</label>
                <input required type="text" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">Açıklama</label>
                <textarea rows={3} value={newDesc} onChange={(e) => setNewDesc(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Departman</label>
                  <select 
                    value={newDept} 
                    onChange={(e) => {
                      const dept = e.target.value;
                      setNewDept(dept);
                      const defaultAssignee = DEPARTMENT_PERSONNEL[dept]?.[0] || "";
                      setNewAssignee(defaultAssignee);
                    }} 
                    className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                  >
                    <option value="Üretim">Üretim</option>
                    <option value="Lojistik">Lojistik</option>
                    <option value="Kalite">Kalite</option>
                    <option value="Bilgi İşlem">Bilgi İşlem</option>
                    <option value="Finans">Finans</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Sorumlu Kişi</label>
                  <select 
                    value={newAssignee} 
                    onChange={(e) => setNewAssignee(e.target.value)} 
                    className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                  >
                    <option value="">Sorumlu Seçiniz</option>
                    {(DEPARTMENT_PERSONNEL[newDept] || []).map((person, idx) => (
                      <option key={idx} value={person}>{person}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Öncelik (Priority)</label>
                  <select value={newPriority} onChange={(e) => setNewPriority(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]">
                    <option value="low">Low (Düşük)</option>
                    <option value="medium">Medium (Orta)</option>
                    <option value="high">High (Yüksek)</option>
                    <option value="critical">Critical (Kritik)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Bitiş Tarihi (Due Date)</label>
                  <input type="datetime-local" value={newDeadline} onChange={(e) => setNewDeadline(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa] text-[10px]" />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">İlgili Problem Kaydı</label>
                <select value={newRecordId} onChange={(e) => setNewRecordId(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]">
                  <option value="">Seçilmedi</option>
                  {records.map((r) => (
                    <option key={r.id} value={r.id}>{r.title}</option>
                  ))}
                </select>
              </div>

              <button type="submit" className="btn btn-primary w-full py-2.5 mt-2">
                Görevi Oluştur
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Update / Task Management Detail */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="w-full max-w-lg bg-[#061320] border border-[#10293f] rounded-xl overflow-hidden shadow-2xl relative">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />
            <div className="p-4 border-b border-[#10293f] flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-[#e0f7fa]">{selectedTask.title}</h3>
                <p className="text-[10px] text-[#4f7b92] mt-0.5 font-mono">TASK YÖNETİMİ & SORUMLU ATAMA</p>
              </div>
              <button onClick={() => setSelectedTask(null)} className="text-[#4f7b92] hover:text-red-500">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleUpdateTask} className="p-4 space-y-4 text-xs">
              {/* Linked Record Details view */}
              {selectedTask.problem_record_id && recordMap.get(selectedTask.problem_record_id) && (
                <div className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg space-y-1 text-[#80deea]">
                  <div className="text-[10px] font-bold text-cyan-400 font-mono uppercase">İlişkili Problem Bilgisi:</div>
                  <div className="text-xs font-semibold text-[#e0f7fa]">{recordMap.get(selectedTask.problem_record_id)?.title}</div>
                  <div className="text-[10px] text-[#4f7b92]">Kök Neden: {recordMap.get(selectedTask.problem_record_id)?.root_cause || "Belirlenmedi"}</div>
                </div>
              )}

              {selectedTask.description && (
                <div className="p-3 bg-[#030a10] border border-[#10293f] rounded text-[#80deea] leading-relaxed">
                  {selectedTask.description}
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Görev Durumu</label>
                  <select value={updateStatus} onChange={(e) => setUpdateStatus(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]">
                    <option value="todo">Yapılacaklar</option>
                    <option value="in_progress">Devam Edenler</option>
                    <option value="completed">Tamamlananlar</option>
                    <option value="delayed">Gecikenler (Overdue)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Departman</label>
                  <select 
                    value={updateDept} 
                    onChange={(e) => {
                      const dept = e.target.value;
                      setUpdateDept(dept);
                      const defaultAssignee = DEPARTMENT_PERSONNEL[dept]?.[0] || "";
                      setUpdateAssignee(defaultAssignee);
                    }} 
                    className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                  >
                    <option value="Üretim">Üretim</option>
                    <option value="Lojistik">Lojistik</option>
                    <option value="Kalite">Kalite</option>
                    <option value="Bilgi İşlem">Bilgi İşlem</option>
                    <option value="Finans">Finans</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Sorumlu Kişi (Assignee)</label>
                  <select 
                    value={updateAssignee} 
                    onChange={(e) => setUpdateAssignee(e.target.value)} 
                    className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]"
                  >
                    <option value="">Sorumlu Seçiniz</option>
                    {(DEPARTMENT_PERSONNEL[updateDept] || []).map((person, idx) => (
                      <option key={idx} value={person}>{person}</option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Öncelik (Priority)</label>
                  <select value={updatePriority} onChange={(e) => setUpdatePriority(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa]">
                    <option value="low">Low (Düşük)</option>
                    <option value="medium">Medium (Orta)</option>
                    <option value="high">High (Yüksek)</option>
                    <option value="critical">Critical (Kritik)</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">Termin / Bitiş Tarihi (Due Date)</label>
                <input type="datetime-local" value={updateDeadline} onChange={(e) => setUpdateDeadline(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[#e0f7fa] text-[10px]" />
              </div>

              {/* Completion Verification Proof */}
              {updateStatus === "completed" && (
                <div className="p-3 bg-[#030a10] border border-green-500/20 rounded-lg space-y-3">
                  <p className="text-[10px] font-semibold text-green-400 flex items-center gap-1.5">
                    <CheckSquare size={13} />
                    Tamamlanma Kanıtı Ekle
                  </p>
                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] text-[#4f7b92]">Nasıl çözüldü? (Açıklama) *</label>
                    <textarea required rows={2} value={proofDesc} onChange={(e) => setProofDesc(e.target.value)} className="p-2 bg-[#061320] border border-[#10293f] rounded text-xs" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] text-[#4f7b92]">Kanıt Bağlantısı / URL (Dosya, Fotoğraf vb.)</label>
                    <input type="url" placeholder="https://example.com/proof" value={proofUrl} onChange={(e) => setProofUrl(e.target.value)} className="p-2 bg-[#061320] border border-[#10293f] rounded text-xs" />
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button type="submit" className="btn btn-primary flex-1 py-2">
                  Değişiklikleri Kaydet
                </button>
                <button type="button" onClick={() => handleDeleteTask(selectedTask.id)} className="btn btn-secondary text-red-400 border-red-500/20 hover:bg-red-500/10 hover:border-red-500/40 py-2">
                  Sil
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
