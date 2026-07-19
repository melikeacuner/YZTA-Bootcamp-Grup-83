"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { listTasks, createTask, updateTask, deleteTask, listRecords } from "@/lib/api";
import { TaskResponse, RecordResponse } from "@/lib/types";

import { Plus, X, Calendar, User as UserIcon, Loader2, AlertTriangle, CheckSquare, ArrowUpRight } from "lucide-react";

interface DevOpsBoardProps {
  onViewReport?: (recordId: string) => void;
}

export default function DevOpsBoard({ onViewReport }: DevOpsBoardProps) {
  const { token } = useAuth();
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [records, setRecords] = useState<RecordResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [selectedDept, setSelectedDept] = useState<string>("All");
  const [selectedAssignee, setSelectedAssignee] = useState<string>("All");

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);

  // Form States (New Task)
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newAssignee, setNewAssignee] = useState("");
  const [newDeadline, setNewDeadline] = useState("");
  const [newRecordId, setNewRecordId] = useState<string>("");

  // Form States (Update Task)
  const [updateStatus, setUpdateStatus] = useState<string>("todo");
  const [updateAssignee, setUpdateAssignee] = useState("");
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
        deadline: newDeadline || undefined,
        problem_record_id: newRecordId || null
      });
      // Reset forms
      setNewTitle("");
      setNewDesc("");
      setNewAssignee("");
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

    try {
      await updateTask(token, selectedTask.id, {
        status: updateStatus,
        assignee_name: updateAssignee || undefined,
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
    setUpdateDeadline(task.deadline ? task.deadline.slice(0, 16) : "");
    setProofDesc(task.proof_description || "");
    setProofUrl(task.proof_url || "");
  }

  const recordMap = new Map(records.map((r) => [r.id, r]));

  const filteredTasks = tasks.filter((t) => {
    // Filter by assignee
    if (selectedAssignee !== "All" && t.assignee_name !== selectedAssignee) {
      return false;
    }
    // Filter by department
    if (selectedDept !== "All") {
      let dept: string | null | undefined = null;
      if (t.problem_record_id) {
        const rec = recordMap.get(t.problem_record_id);
        dept = rec?.department;
      }
      // If the task has no record yet, but is mapped to a session, we'll try to find the department through metadata or other properties
      if (!dept && t.session_id) {
        // Fallback to check if this task department matches selectedDept
        // We'll let it pass if we can't determine it to avoid hiding active tasks
        dept = "Kalite"; // Default pool task department is Kalite
      }
      if (dept && dept !== selectedDept) {
        return false;
      }
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
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-[#e0f7fa]">DevOps Aksiyon Paneli</h2>
          <p className="text-xs text-[#80deea]">Çözüme ulaştırılan problemlerin düzeltici eylem planlarını takip edin.</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn btn-primary text-xs py-2 px-4 flex items-center gap-1.5">
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
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-[#4f7b92] font-semibold">Departman:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="p-2 bg-[#030a10] border border-[#10293f] rounded-lg text-xs text-[#e0f7fa] focus:border-[#00e5ff]"
            >
              <option value="All">Tüm Departmanlar</option>
              {Array.from(new Set(records.map((r) => r.department).filter(Boolean))).map((dept) => (
                <option key={dept} value={dept!}>{dept}</option>
              ))}
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
        </div>
        <div className="text-[10px] text-[#4f7b92] font-mono">
          Toplam: {filteredTasks.length} / {tasks.length} Görev
        </div>
      </div>

      {/* Kanban Grid */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4 overflow-hidden h-full pb-4">
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
                        <h4 className="text-xs font-semibold text-[#e0f7fa] group-hover:text-[#00e5ff] transition-colors line-clamp-2">
                          {task.title}
                        </h4>
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
                          {task.deadline && (
                            <span className="flex items-center gap-1 font-mono">
                              <Calendar size={10} />
                              <span>{new Date(task.deadline).toLocaleDateString("tr-TR")}</span>
                            </span>
                          )}
                        </div>

                        {task.problem_record_id && onViewReport && (
                          <div className="mt-2.5 pt-2 border-t border-[#10293f]/30 flex justify-end">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                onViewReport(task.problem_record_id!);
                              }}
                              className="text-[9px] text-[#00e5ff] hover:text-[#7c4dff] hover:underline flex items-center gap-0.5"
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
                <input required type="text" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">Açıklama</label>
                <textarea rows={3} value={newDesc} onChange={(e) => setNewDesc(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Sorumlu Kişi</label>
                  <input type="text" value={newAssignee} onChange={(e) => setNewAssignee(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Son Gün</label>
                  <input type="datetime-local" value={newDeadline} onChange={(e) => setNewDeadline(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[10px]" />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">İlgili Problem Kaydı</label>
                <select value={newRecordId} onChange={(e) => setNewRecordId(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded">
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

      {/* Modal: Update / Detail Task */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="w-full max-w-md bg-[#061320] border border-[#10293f] rounded-xl overflow-hidden shadow-2xl relative">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />
            <div className="p-4 border-b border-[#10293f] flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-[#e0f7fa]">{selectedTask.title}</h3>
                <p className="text-[10px] text-[#4f7b92] mt-0.5">Aksiyon Düzenleme</p>
              </div>
              <button onClick={() => setSelectedTask(null)} className="text-[#4f7b92] hover:text-red-500">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleUpdateTask} className="p-4 space-y-4 text-xs">
              {selectedTask.description && (
                <div className="p-3 bg-[#030a10] border border-[#10293f] rounded text-[#80deea] leading-relaxed">
                  {selectedTask.description}
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Görev Durumu</label>
                  <select value={updateStatus} onChange={(e) => setUpdateStatus(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded">
                    <option value="todo">Yapılacak</option>
                    <option value="in_progress">Devam Ediyor</option>
                    <option value="completed">Tamamlandı</option>
                    <option value="delayed">Gecikti</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-[#80deea]">Sorumlu</label>
                  <input type="text" value={updateAssignee} onChange={(e) => setUpdateAssignee(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded" />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="font-semibold text-[#80deea]">Bitiş Tarihi</label>
                <input type="datetime-local" value={updateDeadline} onChange={(e) => setUpdateDeadline(e.target.value)} className="p-2 bg-[#030a10] border border-[#10293f] rounded text-[10px]" />
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
