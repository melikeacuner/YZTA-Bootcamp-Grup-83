"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { 
  getRecord, 
  updateRecord, 
  recordChat, 
  closeRecord, 
  uploadRecordDocument, 
  deleteRecordDocument, 
  getA3Preview,
  deleteSession
} from "@/lib/api";
import { RecordResponse, METHODOLOGY_LABELS, RecordDocument } from "@/lib/types";
import { 
  ArrowLeft, 
  User, 
  Building2, 
  Calendar, 
  Send, 
  Sparkles, 
  CheckCircle, 
  FileText,
  Loader2,
  Paperclip,
  Trash2,
  FileCheck,
  Eye,
  X,
  MessageSquare,
  BookmarkCheck
} from "lucide-react";

interface PoolSessionDetailProps {
  sessionId: string; // This receives recordId from dashboard.tsx
  onFinalized: (recordId: string) => void;
  onBack: () => void;
}

export default function PoolSessionDetail({ sessionId: recordId, onFinalized, onBack }: PoolSessionDetailProps) {
  const { token } = useAuth();
  const [record, setRecord] = useState<RecordResponse | null>(null);
  
  // Metadata States
  const [assigneeName, setAssigneeName] = useState("");
  const [trackerName, setTrackerName] = useState("");
  const [department, setDepartment] = useState("Kalite");

  // Chat States
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputMsg, setInputMsg] = useState("");

  // Document Upload States
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [documents, setDocuments] = useState<RecordDocument[]>([]);

  // A3 Report Preview Modal States
  const [showA3Preview, setShowA3Preview] = useState(false);
  const [a3PreviewData, setA3PreviewData] = useState<Record<string, any> | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const [isBusy, setIsBusy] = useState(false);
  const [isSavingMeta, setIsSavingMeta] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function load() {
      if (!token || !recordId) return;
      try {
        const data = await getRecord(token, recordId);
        setRecord(data);
        setAssigneeName(data.meta_data?.assignee_name || "");
        setTrackerName(data.meta_data?.tracker_name || "");
        setDepartment(data.department || "Kalite");
        setDocuments(data.meta_data?.documents || []);
        
        const existingHistory = data.meta_data?.resolution_chat_history || [];
        if (existingHistory.length === 0) {
          const initialGreeting = {
            role: "assistant",
            content: `👋 Merhaba! Bu problemin kök nedeni belirlendi: **"${data.root_cause || "Belirtildi"}"**.\n\nSimdi bu kök nedeni **kalıcı olarak gidermek** ve **bir daha yaşanmaması için süreç oluşturmak** üzere çalışacağız:\n1. 🛠️ **Kalıcı Düzeltici Aksiyon**: Kök nedeni tamamen ortadan kaldıracak teknik/operasyonel önlem.\n2. 📜 **Süreç & SOP Güncellemesi**: Operasyonel talimatların ve süreçlerin kalıcı hale getirilmesi.\n3. 🔒 **Poka-Yoke (Hata Önleme)**: İnsan hatasını imkansız kılacak fiziki/yazılımsal bariyerler.\n4. 🚀 **Yokoten (Yatay Yayılım)**: Benzer makine ve hatlara yaygınlaştırılması.\n\nHangi aksiyon adımları ile başlamak istersiniz? Bana belge yükleyebilir veya düşüncelerinizi iletebilirsiniz.`
          };
          setMessages([initialGreeting]);
        } else {
          setMessages(existingHistory);
        }
      } catch (err: any) {
        setError("Problem detayları yüklenemedi.");
      }
    }
    load();
  }, [token, recordId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!record) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-sm font-mono">Çözüm Kaydı Yükleniyor...</p>
      </div>
    );
  }

  const handleUpdateMetadata = async () => {
    if (!token) return;
    setIsSavingMeta(true);
    try {
      const updated = await updateRecord(token, recordId, {
        department: department,
        meta_data: {
          ...(record.meta_data || {}),
          assignee_name: assigneeName,
          tracker_name: trackerName
        }
      });
      setRecord(updated);
    } catch (err) {
      console.error("Failed to update metadata:", err);
    } finally {
      setIsSavingMeta(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !inputMsg.trim() || isBusy) return;

    const userMessage = inputMsg;
    setInputMsg("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsBusy(true);

    try {
      const updated = await recordChat(token, recordId, userMessage);
      setRecord(updated);
      setMessages(updated.meta_data?.resolution_chat_history || []);
    } catch (err: any) {
      setError(err.message || "Mesaj gönderilemedi.");
    } finally {
      setIsBusy(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploadingDoc(true);
    setError(null);
    try {
      const updated = await uploadRecordDocument(token, recordId, file);
      setRecord(updated);
      setDocuments(updated.meta_data?.documents || []);
    } catch (err: any) {
      setError(err.message || "Doküman yüklenirken hata oluştu.");
    } finally {
      setUploadingDoc(false);
      e.target.value = "";
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!token) return;
    try {
      const updated = await deleteRecordDocument(token, recordId, docId);
      setRecord(updated);
      setDocuments(updated.meta_data?.documents || []);
    } catch (err: any) {
      setError(err.message || "Doküman silinemedi.");
    }
  };

  const handleOpenA3Preview = async () => {
    if (!token) return;
    setLoadingPreview(true);
    setError(null);
    try {
      const preview = await getA3Preview(token, recordId);
      setA3PreviewData(preview);
      setShowA3Preview(true);
    } catch (err: any) {
      setError("A3 Rapor önizlemesi oluşturulamadı.");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleCloseSessionConfirmed = async () => {
    if (!token || isBusy) return;
    setIsBusy(true);
    setError(null);
    try {
      const response = await closeRecord(token, recordId);
      setShowA3Preview(false);
      onFinalized(response.id);
    } catch (err: any) {
      setError(err.message || "Problem kapatılamadı.");
    } finally {
      setIsBusy(false);
    }
  };

  const handleDeleteSessionConfirmed = async () => {
    if (!token || !recordId || isBusy) return;
    if (!confirm("Bu analiz seansını tamamen iptal etmek ve silmek istediğinize emin misiniz?")) return;
    setIsBusy(true);
    setError(null);
    try {
      await deleteSession(token, recordId);
      onBack();
    } catch (err: any) {
      setError(err.message || "Seans silinemedi.");
    } finally {
      setIsBusy(false);
    }
  };

  const conversationSummary = record.meta_data?.conversation_summary;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-fade-in text-[#e0f7fa]">
      {/* Header and Action Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-[#10293f] pb-4 gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-[#0a1f33] rounded-lg text-[#4f7b92] hover:text-[#00e5ff] transition-all"
            title="Geri Dön"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-lg md:text-xl font-bold tracking-wide">
              {record.title || "Problem Çözüm Paneli"}
            </h2>
            <p className="text-xs text-[#4f7b92] mt-0.5 font-mono">
              METODOLOJİ: {METHODOLOGY_LABELS[record.methodology as keyof typeof METHODOLOGY_LABELS] || record.methodology}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <button
            onClick={handleDeleteSessionConfirmed}
            disabled={isBusy}
            className="px-3 py-2.5 bg-red-950/30 border border-red-500/30 hover:bg-red-900/40 hover:border-red-400 text-red-400 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all"
            title="Bu aktif seansı iptal et ve sil"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:inline">İptal Et / Sil</span>
          </button>

          <button
            onClick={handleOpenA3Preview}
            disabled={loadingPreview || isBusy}
            className="flex-1 sm:flex-none px-3.5 py-2.5 bg-[#0a1f33] border border-[#00e5ff]/40 hover:bg-[#0e2a47] text-[#00e5ff] text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all"
          >
            {loadingPreview ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
            <span>A3 Rapor Önizleme</span>
          </button>

          <button
            onClick={handleOpenA3Preview}
            disabled={isBusy}
            className="flex-1 sm:flex-none px-4 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-all shadow-md shadow-emerald-500/10"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Çözümü Onayla & Kapat</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-xl text-xs text-red-400">
          {error}
        </div>
      )}

      {/* --- Metadata Inputs --- */}
      <div className="p-5 bg-[#061320] border border-[#10293f] rounded-2xl grid grid-cols-1 md:grid-cols-3 gap-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[1.5px] bg-[#10293f]" />

        {/* Department Selection */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" />
            Atanacak Birim / Departman
          </label>
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            onBlur={handleUpdateMetadata}
            className="w-full p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] transition-all"
          >
            <option value="Üretim">Üretim</option>
            <option value="Lojistik">Lojistik</option>
            <option value="Kalite">Kalite</option>
            <option value="Bilgi İşlem">Bilgi İşlem</option>
            <option value="Finans">Finans</option>
          </select>
        </div>

        {/* Assignee Name */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            Takip Edecek Sorumlu (Assignee)
          </label>
          <input
            type="text"
            value={assigneeName}
            onChange={(e) => setAssigneeName(e.target.value)}
            onBlur={handleUpdateMetadata}
            placeholder="İsim soyisim girin..."
            className="w-full p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] placeholder-[#4f7b92] transition-all"
          />
        </div>

        {/* Tracker / Supervisor Name */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#80deea] flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            Denetçi / Takipçi (Tracker)
          </label>
          <input
            type="text"
            value={trackerName}
            onChange={(e) => setTrackerName(e.target.value)}
            onBlur={handleUpdateMetadata}
            placeholder="İsim soyisim veya birim lideri..."
            className="w-full p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] placeholder-[#4f7b92] transition-all"
          />
        </div>
      </div>

      {/* --- Split Screen Content --- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        
        {/* Left Screen: Dynamic Problem Report & Uploaded Documents */}
        <div className="bg-[#061320] border border-[#10293f] rounded-2xl p-5 shadow-xl flex flex-col space-y-4 max-h-[680px] overflow-y-auto relative">
          <h3 className="text-sm font-bold text-[#80deea] border-b border-[#10293f] pb-2 flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#00e5ff]" />
            Dinamik Problem Analiz Raporu (A3)
          </h3>

          <div className="space-y-4 text-xs">
            {/* Description */}
            <div className="space-y-1.5">
              <span className="text-[#4f7b92] uppercase tracking-wider font-mono text-[9px]">Problem Tanımı</span>
              <p className="bg-[#030a10] p-3 rounded-xl border border-[#10293f]/50 leading-relaxed">
                {record.description}
              </p>
            </div>

            {/* RCA Step Answers */}
            <div className="space-y-2">
              <span className="text-[#4f7b92] uppercase tracking-wider font-mono text-[9px]">Kök Neden Analizi Adımları</span>
              <div className="space-y-2.5">
                {Object.entries(record.step_responses || {}).map(([stepKey, answerText]) => (
                  <div key={stepKey} className="p-3 bg-[#0a1f33]/40 border border-[#10293f]/50 rounded-xl space-y-1">
                    <div className="text-[10px] font-bold text-cyan-400 uppercase font-mono tracking-wide">
                      {stepKey.replace(/_/g, " ")}
                    </div>
                    <p className="leading-relaxed opacity-95 text-[#e0f7fa]">{answerText as string}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Uploaded Documents List & AI Summaries */}
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-[#10293f] pb-1">
                <span className="text-[#4f7b92] uppercase tracking-wider font-mono text-[9px] flex items-center gap-1">
                  <Paperclip className="w-3 h-3 text-[#00e5ff]" />
                  İlişkili Dökümanlar & AI Özetleri ({documents.length})
                </span>
                <label className="text-[10px] text-[#00e5ff] hover:underline cursor-pointer flex items-center gap-1 font-semibold">
                  {uploadingDoc ? (
                    <span className="flex items-center gap-1 text-cyan-400">
                      <Loader2 className="w-3 h-3 animate-spin" /> Yükleniyor...
                    </span>
                  ) : (
                    <>+ Belge Yükle</>
                  )}
                  <input
                    type="file"
                    className="hidden"
                    onChange={handleFileUpload}
                    disabled={uploadingDoc}
                  />
                </label>
              </div>

              {documents.length === 0 ? (
                <div className="p-3 bg-[#030a10]/50 border border-dashed border-[#10293f] rounded-xl text-center text-[#4f7b92] text-[11px]">
                  Henüz teknik doküman yüklenmedi. Belge yükleyerek AI analizine katkı sağlayabilirsiniz.
                </div>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div key={doc.id} className="p-3 bg-[#0a1f33]/60 border border-[#10293f] rounded-xl space-y-1.5 relative group">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-semibold text-[#e0f7fa]">
                          <FileCheck className="w-3.5 h-3.5 text-[#00e5ff]" />
                          <span>{doc.filename}</span>
                        </div>
                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="p-1 hover:bg-red-950/40 text-red-400 rounded transition-all"
                          title="Dokümanı Sil"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <div className="p-2 bg-[#030a10] border border-cyan-500/20 rounded-lg text-[11px] text-[#80deea] leading-relaxed">
                        <span className="font-bold text-cyan-400 font-mono text-[9px] uppercase block mb-0.5">🤖 AI Belge Özeti</span>
                        {doc.summary}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Synthesized Outputs (if closed or available) */}
            {record.root_cause && (
              <div className="p-3 bg-cyan-950/10 border border-cyan-500/20 rounded-xl space-y-1.5">
                <span className="text-[10px] font-bold text-cyan-400 uppercase font-mono tracking-wide">🔍 Tespit Edilen Kök Neden</span>
                <p className="leading-relaxed opacity-95 text-[#e0f7fa]">{record.root_cause}</p>
              </div>
            )}

            {record.corrective_actions && (
              <div className="p-3 bg-emerald-950/10 border border-emerald-500/20 rounded-xl space-y-1.5">
                <span className="text-[10px] font-bold text-emerald-400 uppercase font-mono tracking-wide">🛠️ Kalıcı Düzeltici Aksiyonlar</span>
                <p className="leading-relaxed opacity-95 text-[#e0f7fa]">{record.corrective_actions}</p>
              </div>
            )}

            {record.lessons_learned && (
              <div className="p-3 bg-purple-950/10 border border-purple-500/20 rounded-xl space-y-1.5">
                <span className="text-[10px] font-bold text-purple-400 uppercase font-mono tracking-wide">🎓 Öğrenilen Dersler (Lessons Learned)</span>
                <p className="leading-relaxed opacity-95 text-[#e0f7fa] whitespace-pre-line">{record.lessons_learned}</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Screen: AI Agent Resolution Chat & Conversation Summary */}
        <div className="bg-[#061320] border border-[#10293f] rounded-2xl flex flex-col h-[680px] shadow-xl overflow-hidden relative">
          {/* Chat Header */}
          <div className="p-4 bg-[#0a1f33]/60 border-b border-[#10293f] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 dot-pulse" />
              <span className="text-xs font-bold text-[#80deea]">AI Çözüm Ajanı</span>
            </div>
            <span className="text-[9px] px-2 py-0.5 rounded bg-[#10293f] text-[#4f7b92] font-mono uppercase">
              active-resolution
            </span>
          </div>

          {/* Live Conversation Summary Card */}
          {conversationSummary && (
            <div className="px-4 py-2.5 bg-[#030a10] border-b border-[#10293f] text-xs">
              <div className="flex items-center gap-1.5 font-bold text-cyan-400 text-[10px] uppercase font-mono mb-1">
                <MessageSquare className="w-3 h-3 text-[#00e5ff]" />
                <span>Canlı Sohbet & Karar Özeti</span>
              </div>
              <p className="text-[11px] text-[#e0f7fa] leading-relaxed whitespace-pre-line opacity-90">
                {conversationSummary}
              </p>
            </div>
          )}

          {/* Messages view */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 scrollbar-thin bg-[#030a10]/50">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-3 p-6">
                <Sparkles className="w-8 h-8 text-[#00e5ff] opacity-60 animate-bounce" />
                <div>
                  <h4 className="text-xs font-bold text-[#e0f7fa]">Problem Çözüm Ajanı Hazır</h4>
                  <p className="text-[11px] text-[#4f7b92] max-w-xs mt-1">
                    Kök neden analizine uygun kalıcı düzeltici eylemleri planlamak için ajana soru sorabilir veya planlarınızı iletebilirsiniz.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((m, idx) => {
                const isUser = m.role === "user";
                return (
                  <div
                    key={idx}
                    className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}
                  >
                    <div
                      className={`max-w-[85%] p-3 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? "bg-gradient-to-br from-[#7c4dff] to-[#5e35b1] text-white rounded-tr-none"
                          : "bg-[#0a1f33] border border-[#10293f] text-[#e0f7fa] rounded-tl-none"
                      }`}
                    >
                      <p className="whitespace-pre-line">{m.content}</p>
                    </div>
                  </div>
                );
              })
            )}
            {isBusy && (
              <div className="flex justify-start">
                <div className="p-3 bg-[#0a1f33] border border-[#10293f] rounded-2xl rounded-tl-none flex items-center gap-2 text-[#80deea] text-xs">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00e5ff]" />
                  <span>Ajan analiz edip yazıyor...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Message form with file upload attachment */}
          <form onSubmit={handleSendMessage} className="p-3 bg-[#061320] border-t border-[#10293f] flex items-center gap-2">
            <label className="p-2.5 bg-[#030a10] border border-[#10293f] text-[#80deea] hover:border-[#00e5ff] rounded-xl cursor-pointer transition-all shrink-0" title="Belge Yükle ve Analiz Et (PDF, TXT, Log)">
              <Paperclip className="w-4 h-4 text-[#00e5ff]" />
              <input
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploadingDoc || isBusy}
              />
            </label>

            <input
              type="text"
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              disabled={isBusy}
              placeholder="Çözüm planınızı yazın, ajana danışın veya belge yükleyin..."
              className="flex-1 p-2.5 bg-[#030a10] border border-[#10293f] rounded-xl text-xs text-[#e0f7fa] focus:border-[#00e5ff] placeholder-[#4f7b92] focus:outline-none"
            />
            <button
              type="submit"
              disabled={isBusy || !inputMsg.trim()}
              className="p-2.5 bg-[#00e5ff] text-[#030a10] hover:bg-[#00b2cc] disabled:bg-[#10293f] disabled:text-[#4f7b92] rounded-xl transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

      </div>

      {/* --- A3 Report Preview Modal --- */}
      {showA3Preview && a3PreviewData && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#061320] border border-[#00e5ff]/30 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fade-in">
            {/* Modal Header */}
            <div className="p-4 bg-[#0a1f33] border-b border-[#10293f] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookmarkCheck className="w-5 h-5 text-[#00e5ff]" />
                <h3 className="text-sm font-bold text-[#e0f7fa]">
                  AI Destekli A3 Kök Neden Çözüm Raporu Önizlemesi
                </h3>
              </div>
              <button
                onClick={() => setShowA3Preview(false)}
                className="p-1 hover:bg-[#10293f] text-[#4f7b92] hover:text-[#e0f7fa] rounded-lg transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4 sm:p-6 overflow-y-auto max-h-[75vh] space-y-4 text-xs print-container break-words">
              <div className="space-y-1 border-b border-[#10293f] pb-3">
                <span className="text-[10px] text-[#4f7b92] uppercase font-mono">Rapor Başlığı</span>
                <h4 className="text-sm sm:text-base font-bold text-[#00e5ff] break-words">{a3PreviewData.title}</h4>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl space-y-1">
                  <span className="text-[9px] text-[#4f7b92] uppercase font-mono block">Departman</span>
                  <span className="font-semibold text-[#80deea]">{a3PreviewData.department || "Kalite"}</span>
                </div>
                <div className="p-3 bg-[#030a10] border border-[#10293f] rounded-xl space-y-1">
                  <span className="text-[9px] text-[#4f7b92] uppercase font-mono block">Etiketler (Tags)</span>
                  <div className="flex flex-wrap gap-1">
                    {(a3PreviewData.tags || ["A3"]).map((t: string, i: number) => (
                      <span key={i} className="px-1.5 py-0.5 bg-[#10293f] text-[#00e5ff] rounded text-[10px]">#{t}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="p-3.5 bg-cyan-950/20 border border-cyan-500/30 rounded-xl space-y-1">
                <span className="text-[10px] font-bold text-cyan-400 uppercase font-mono">🔍 Kök Neden Analizi Özeti</span>
                <p className="leading-relaxed text-[#e0f7fa] whitespace-pre-line break-words">{a3PreviewData.root_cause}</p>
              </div>

              <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-xl space-y-1">
                <span className="text-[10px] font-bold text-emerald-400 uppercase font-mono">🛠️ Kararlaştırılan Düzeltici Aksiyonlar</span>
                <p className="leading-relaxed text-[#e0f7fa] whitespace-pre-line break-words">{a3PreviewData.corrective_actions}</p>
              </div>

              <div className="p-3.5 bg-purple-950/20 border border-purple-500/30 rounded-xl space-y-1">
                <span className="text-[10px] font-bold text-purple-400 uppercase font-mono">🎓 Kurumsal Öğrenilen Dersler</span>
                <p className="leading-relaxed text-[#e0f7fa] whitespace-pre-line break-words">{a3PreviewData.lessons_learned}</p>
              </div>

              {a3PreviewData.yokoten_notes && (
                <div className="p-3.5 bg-amber-950/20 border border-amber-500/30 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold text-amber-400 uppercase font-mono">🚀 Yokoten (Yatay Yayılım) Önerileri</span>
                  <p className="leading-relaxed text-[#e0f7fa] whitespace-pre-line break-words">{a3PreviewData.yokoten_notes}</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-[#0a1f33] border-t border-[#10293f] flex items-center justify-end gap-3">
              <button
                onClick={() => setShowA3Preview(false)}
                className="px-4 py-2 bg-[#10293f] hover:bg-[#183957] text-[#e0f7fa] text-xs rounded-xl font-semibold transition-all"
              >
                İncelemeye Devam Et
              </button>
              <button
                onClick={handleCloseSessionConfirmed}
                disabled={isBusy}
                className="px-5 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white text-xs font-bold rounded-xl flex items-center gap-1.5 transition-all shadow-lg shadow-emerald-500/20"
              >
                {isBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                <span>Raporu Onayla ve Problemi Kapat</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
