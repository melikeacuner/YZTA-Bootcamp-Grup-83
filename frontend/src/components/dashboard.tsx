"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  MessageSquarePlus,
  Database,
  Search,
  Activity,
  LogOut,
  CheckCircle,
  X,
  FolderOpen,
  ListTodo,
  User,
  ChevronRight,
  Inbox,
  Menu,
  Trash2
} from "lucide-react";
import { listSessions, deleteSession } from "@/lib/api";
import { SessionResponse } from "@/lib/types";

import NewSession from "./new-session";
import AgentChat from "./agent-chat";
import MethodologyChat from "./methodology-chat";
import KnowledgeSearch from "./knowledge-search";
import ManagerDashboard from "./manager-dashboard";
import A3Explorer from "./a3-explorer";
import DevOpsBoard from "./devops-board";
import UnifiedRecordDetail from "./unified-record-detail";
import ProblemPool from "./problem-pool";
import PoolSessionDetail from "./pool-session-detail";

type View =
  | "new"
  | "agent_chat"
  | "methodology_chat"
  | "records"
  | "search"
  | "report"
  | "manager_dashboard"
  | "a3_explorer"
  | "devops_board"
  | "pool"
  | "pool_detail";

export default function Dashboard() {
  const { token, user, logout } = useAuth();
  const [currentView, setCurrentView] = useState<View>("new");
  const [activeSessions, setActiveSessions] = useState<SessionResponse[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [finalizedRecordId, setFinalizedRecordId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false); // Mobile defaults to closed

  // Auto-open sidebar on desktop screens on mount
  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth >= 768) {
      setSidebarOpen(true);
    }
  }, []);

  const fetchActiveSessions = useCallback(async () => {
    if (!token) return;
    try {
      const allSessions = await listSessions(token);
      setActiveSessions(allSessions.filter((s) => s.status === "active"));
    } catch (err) {
      console.error("Failed to load active sessions:", err);
    }
  }, [token]);

  useEffect(() => {
    fetchActiveSessions();
  }, [fetchActiveSessions, currentView]);

  function handleSessionCreated(session: SessionResponse) {
    setActiveSessionId(session.id);
    setCurrentView("methodology_chat");
    fetchActiveSessions();
  }

  function handleSessionSelected(session: SessionResponse) {
    setActiveSessionId(session.id);
    setCurrentView("methodology_chat");
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }

  function handleFinalized(recordId: string) {
    setFinalizedRecordId(recordId);
    setActiveSessionId(null);
    setCurrentView("report");
    fetchActiveSessions();
  }

  function handleViewA3Detail(recordId: string) {
    setFinalizedRecordId(recordId);
    setCurrentView("report");
  }

  const navItems = [
    { id: "new" as View, icon: MessageSquarePlus, label: "Yeni Problem Çözümü" },
    { id: "pool" as View, icon: Inbox, label: "Problem Havuzu (Pool)" },
    { id: "a3_explorer" as View, icon: FolderOpen, label: "A3 Rapor Havuzu" },
    { id: "devops_board" as View, icon: ListTodo, label: "Aksiyon Planı (DevOps)" },
    { id: "search" as View, icon: Search, label: "Bilgi Bankası Arama" },
    { id: "manager_dashboard" as View, icon: Activity, label: "Yönetici Dashboard" },
  ];

  const currentNavItem = navItems.find((i) => i.id === currentView);
  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : "US";

  return (
    <div className="flex flex-col md:flex-row h-screen w-screen overflow-hidden text-[#e0f7fa]">
      {/* Mobile Backdrop Overlay */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/70 backdrop-blur-xs z-40 md:hidden no-print animate-fade-in"
        />
      )}

      {/* --- Responsive Sidebar Menu --- */}
      <aside 
        className={`fixed md:relative inset-y-0 left-0 z-50 md:z-10 w-[280px] bg-[#061320] border-r border-[#10293f] flex flex-col h-full transition-transform duration-300 ease-in-out no-print ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0 md:hidden"
        }`}
      >
        {/* Header/Logo */}
        <div className="p-5 border-b border-[#10293f] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-[36px] h-[36px] rounded-lg bg-gradient-to-br from-[#00e5ff] to-[#7c4dff] flex items-center justify-center font-bold text-[#030a10] text-lg shadow-md shadow-cyan-500/10">
              P
            </div>
            <div>
              <h1 className="font-bold text-md text-[#e0f7fa] tracking-wide font-sans">Proby AI</h1>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="text-[#4f7b92] hover:text-[#00e5ff] transition-colors p-1"
          >
            <ChevronRight className="rotate-180" size={18} />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <p className="text-[10px] font-semibold text-[#4f7b92] uppercase tracking-widest pl-2 mb-2">NAVİGASYON</p>
          {navItems.map((item) => {
            const active = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setCurrentView(item.id);
                  setActiveSessionId(null);
                  if (typeof window !== "undefined" && window.innerWidth < 768) {
                    setSidebarOpen(false);
                  }
                }}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm transition-all duration-200 text-left ${
                  active
                    ? "bg-gradient-to-r from-[rgba(0,229,255,0.1)] to-transparent border-l-2 border-[#00e5ff] text-[#00e5ff]"
                    : "text-[#80deea] hover:bg-[#0a1f33] hover:text-[#e0f7fa]"
                }`}
              >
                <item.icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* Active Sessions List */}
          {activeSessions.length > 0 && (
            <div className="pt-6 space-y-2">
              <p className="text-[10px] font-semibold text-[#4f7b92] uppercase tracking-widest pl-2">AKTİF OTURUMLAR</p>
              <div className="space-y-1">
                {activeSessions.map((s) => {
                  const active = activeSessionId === s.id;
                  return (
                    <div
                      key={s.id}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all group ${
                        active
                          ? "bg-[#0a1f33] text-[#00e5ff] border border-cyan-500/25"
                          : "text-[#80deea] hover:bg-[#0a1f33] hover:text-[#e0f7fa]"
                      }`}
                    >
                      <button
                        onClick={() => handleSessionSelected(s)}
                        className="flex-1 flex items-center gap-2 overflow-hidden text-left min-w-0"
                      >
                        <span className="w-1.5 h-1.5 rounded-full dot-pulse bg-[#00e676] shrink-0" />
                        <span className="truncate pr-1 font-mono text-[11px]">
                          {s.problem_description.slice(0, 18)}...
                        </span>
                      </button>

                      <div className="flex items-center gap-1 shrink-0">
                        <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-[#10293f] text-[#4f7b92]">
                          {s.methodology}
                        </span>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            if (!confirm("Bu aktif oturumu iptal edip silmek istediğinize emin misiniz?")) return;
                            try {
                              await deleteSession(token!, s.id);
                              if (activeSessionId === s.id) {
                                setActiveSessionId(null);
                                setCurrentView("new");
                              }
                              fetchActiveSessions();
                            } catch (err: any) {
                              alert("Oturum silinirken hata oluştu: " + (err.message || ""));
                            }
                          }}
                          className="p-1 text-[#4f7b92] hover:text-red-400 hover:bg-red-950/40 rounded transition-all"
                          title="Bu oturumu iptal et ve sil"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-[#10293f] flex items-center justify-between bg-[#030a10]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-[#10293f] border border-[#194063] flex items-center justify-center font-bold text-xs text-[#00e5ff] shrink-0">
              {initials}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-[#e0f7fa] truncate">{(user as any)?.full_name || user?.email || "Admin Yöneticisi"}</p>
              <p className="text-[10px] text-[#4f7b92] truncate">{user?.email || "admin@proby.ai"}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="text-[#4f7b92] hover:text-[#ff1744] transition-colors p-1.5 rounded-lg hover:bg-red-950/20"
            title="Çıkış Yap"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* --- Main Content Area --- */}
      <main className="flex-1 bg-[#030a10] flex flex-col h-full overflow-hidden relative w-full">
        {/* Mobile Header Bar */}
        <div className="md:hidden flex items-center justify-between p-3.5 bg-[#061320] border-b border-[#10293f] z-20 no-print shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 text-[#80deea] hover:text-[#00e5ff] hover:bg-[#0a1f33] rounded-lg border border-[#10293f] transition-all"
              aria-label="Menüyü Aç"
            >
              <Menu size={18} />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-gradient-to-br from-[#00e5ff] to-[#7c4dff] flex items-center justify-center font-bold text-[#030a10] text-sm">
                P
              </div>
              <span className="font-bold text-sm text-[#e0f7fa]">{currentNavItem?.label || "Proby AI"}</span>
            </div>
          </div>
        </div>

        {/* Mini Toggle for Desktop Sidebar when collapsed */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="hidden md:flex fixed left-4 top-4 w-9 h-9 rounded-lg bg-[#061320] border border-[#10293f] items-center justify-center text-[#e0f7fa] hover:text-[#00e5ff] hover:border-[#00e5ff] transition-all z-20 no-print"
          >
            <ChevronRight size={18} />
          </button>
        )}

        {/* Glow decorative graphics */}
        <div className="absolute top-0 right-0 w-[300px] md:w-[400px] h-[300px] md:h-[400px] rounded-full bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.02),transparent_70%)] pointer-events-none" />

        <div className="flex-1 overflow-y-auto p-3 sm:p-5 md:p-8 flex flex-col">
          {currentView === "new" && (
            <NewSession 
              onSessionCreated={handleSessionCreated} 
              onViewReport={handleViewA3Detail}
            />
          )}
          {currentView === "methodology_chat" && activeSessionId && (
            <MethodologyChat sessionId={activeSessionId} onFinalized={handleFinalized} />
          )}
          {currentView === "pool" && (
            <ProblemPool
              onViewDetail={(sessionId) => {
                setActiveSessionId(sessionId);
                setCurrentView("pool_detail");
              }}
            />
          )}
          {currentView === "pool_detail" && activeSessionId && (
            <PoolSessionDetail
              sessionId={activeSessionId}
              onFinalized={handleFinalized}
              onBack={() => setCurrentView("pool")}
            />
          )}
          {currentView === "a3_explorer" && <A3Explorer onViewDetail={handleViewA3Detail} />}
          {currentView === "devops_board" && (
            <DevOpsBoard
              onViewReport={(recordId) => {
                setFinalizedRecordId(recordId);
                setCurrentView("report");
              }}
            />
          )}
          {currentView === "search" && <KnowledgeSearch />}
          {currentView === "manager_dashboard" && <ManagerDashboard />}
          {currentView === "report" && finalizedRecordId && (
            <UnifiedRecordDetail recordId={finalizedRecordId} onClose={() => setCurrentView("a3_explorer")} />
          )}
        </div>
      </main>
    </div>
  );
}
