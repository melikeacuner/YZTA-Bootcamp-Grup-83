"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardStats } from "@/lib/api";
import { DashboardStats } from "@/lib/types";
import { Loader2, Activity, ShieldAlert, CheckCircle2, TrendingUp, Building2, Filter } from "lucide-react";

export default function ManagerDashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDept, setSelectedDept] = useState<string>("Tüm Şirket");
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await getDashboardStats(token, selectedDept);
      setStats(data);
    } catch (err) {
      console.error("Failed to load dashboard statistics:", err);
      setError("İstatistikler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [token, selectedDept]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

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
      label: "Ortalama FMEA Riski (RPN)",
      value: stats.average_rpn.toFixed(1),
      sub: "Hedef: RPN < 50",
      icon: ShieldAlert,
      colorClass: "text-[#ffea00] bg-yellow-500/5 border-yellow-500/20"
    },
    {
      label: "Geciken Aksiyon Oranı",
      value: `${(stats.delayed_rate * 100).toFixed(0)}%`,
      sub: `${stats.delayed_tasks} geciken görev`,
      icon: TrendingUp,
      colorClass: "text-[#ff1744] bg-red-500/5 border-red-500/20"
    }
  ];

  return (
    <div className="w-full space-y-8 animate-fade-in pb-8">
      {/* Header and Department Filter Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#10293f] pb-4">
        <div>
          <h2 className="text-2xl font-bold text-[#e0f7fa]">Yönetici Dashboardu (Executive BI)</h2>
          <p className="text-xs text-[#80deea] mt-1">
            Departman bazlı ve genel şirket seviyesinde problem çözme performansı, FMEA riskleri ve aksiyon uyumu.
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

      {/* Distributions Charts Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

        {/* Categories */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3 flex justify-between items-center">
            <div>
              <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Kategori Dağılımı</h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">En sık karşılaşılan kök problem tipleri</p>
            </div>
          </div>
          {renderBarChart(stats.category_distribution, "linear-gradient(90deg, #7c4dff, #ff1744)")}
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

      {/* FMEA Risk Heatmap Matrix & Department KPI Matrix */}
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

        {/* Department KPI Matrix */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5 flex flex-col justify-between">
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
      </div>
    </div>
  );
}

