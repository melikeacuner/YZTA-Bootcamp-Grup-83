"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardStats } from "@/lib/api";
import { DashboardStats } from "@/lib/types";
import { Loader2, Activity, ShieldAlert, CheckCircle2, TrendingUp } from "lucide-react";

export default function ManagerDashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    if (!token) return;
    try {
      const data = await getDashboardStats(token);
      setStats(data);
    } catch (err) {
      console.error("Failed to load dashboard statistics:", err);
      setError("İstatistikler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [token]);

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
  const renderBarChart = (data: Record<string, number>, color: string) => {
    const total = Object.values(data).reduce((a, b) => a + b, 0);
    if (total === 0) return <p className="text-[10px] text-[#4f7b92] italic mt-2">Veri yok</p>;

    return (
      <div className="space-y-3 pt-2">
        {Object.entries(data).map(([key, value]) => {
          const percentage = total > 0 ? (value / total) * 100 : 0;
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-[11px] text-[#80deea] font-medium pr-1">
                <span>{key}</span>
                <span className="font-mono">{value} ({percentage.toFixed(0)}%)</span>
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
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-[#e0f7fa]">Yönetici Dashboardu</h2>
        <p className="text-xs text-[#80deea]">Kurumsal problem çözme performans göstergelerini ve FMEA risk dağılımlarını analiz edin.</p>
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
          <div className="border-b border-[#10293f] pb-3">
            <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Departman Dağılımı</h3>
            <p className="text-[10px] text-[#4f7b92] mt-0.5">Departmanların problem çözme yoğunluğu</p>
          </div>
          {renderBarChart(stats.department_distribution, "linear-gradient(90deg, #00e5ff, #00b0ff)")}
        </div>

        {/* Categories */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3">
            <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Kategori Dağılımı</h3>
            <p className="text-[10px] text-[#4f7b92] mt-0.5">En sık hata veren problem kategorileri</p>
          </div>
          {renderBarChart(stats.category_distribution, "linear-gradient(90deg, #7c4dff, #ff1744)")}
        </div>

        {/* Methodologies */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3">
            <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Metodoloji Dağılımı</h3>
            <p className="text-[10px] text-[#4f7b92] mt-0.5">Analizlerde kullanılan problem çözme araçları</p>
          </div>
          {renderBarChart(stats.methodology_distribution, "linear-gradient(90deg, #00e676, #ffea00)")}
        </div>
      </div>

      {/* Technical Analyses and Department KPI Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
        {/* Department KPI Matrix */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5">
          <div className="border-b border-[#10293f] pb-3">
            <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">Departman KPI Performans Matrisi</h3>
            <p className="text-[10px] text-[#4f7b92] mt-0.5">Birimlerin reaktif ve proaktif aksiyon verimliliği</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#10293f] text-[#80deea] font-semibold text-[10px] uppercase font-mono">
                  <th className="py-2.5">Departman</th>
                  <th className="py-2.5 text-center">Vaka Sayısı</th>
                  <th className="py-2.5 text-center">Risk Seviyesi</th>
                  <th className="py-2.5 text-right">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#10293f]/40 text-[#e0f7fa]">
                {Object.entries(stats.department_distribution).map(([dept, count]) => {
                  const riskLevel = count > 5 ? "Yüksek" : count > 2 ? "Orta" : "Düşük";
                  const statusColor = count > 5 ? "text-red-400 bg-red-500/10 border-red-500/20" : count > 2 ? "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" : "text-green-400 bg-green-500/10 border-green-500/20";
                  return (
                    <tr key={dept} className="hover:bg-[#061320]/40 transition-colors">
                      <td className="py-3 font-semibold">{dept}</td>
                      <td className="py-3 text-center font-mono">{count}</td>
                      <td className="py-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] border ${statusColor}`}>
                          {riskLevel}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <span className="text-[10px] text-[#4f7b92] font-mono">Aktif Takip</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* FMEA Risk and Yokoten Analysis */}
        <div className="p-5 glass rounded-xl space-y-4 shadow-md shadow-cyan-500/5 flex flex-col justify-between">
          <div>
            <div className="border-b border-[#10293f] pb-3">
              <h3 className="text-xs font-bold text-[#e0f7fa] uppercase tracking-widest">FMEA Risk & Sürdürülebilirlik Analizi</h3>
              <p className="text-[10px] text-[#4f7b92] mt-0.5">RPN kontrol limitleri ve Yokoten yaygınlaştırma oranı</p>
            </div>
            
            <div className="space-y-4 pt-4 text-xs">
              <div className="flex justify-between items-center bg-[#030a10]/40 p-3 rounded-lg border border-[#10293f]/50">
                <div>
                  <span className="text-[#80deea] font-medium block">Ortalama RPN Değeri</span>
                  <span className="text-[10px] text-[#4f7b92]">Kontrol Limiti: RPN &lt; 50</span>
                </div>
                <span className={`text-lg font-bold font-mono ${stats.average_rpn > 50 ? "text-amber-400" : "text-green-400"}`}>
                  {stats.average_rpn.toFixed(1)}
                </span>
              </div>

              <div className="flex justify-between items-center bg-[#030a10]/40 p-3 rounded-lg border border-[#10293f]/50">
                <div>
                  <span className="text-[#80deea] font-medium block">Aksiyon Kapatma Süresi</span>
                  <span className="text-[10px] text-[#4f7b92]">Planlanan aksiyon tamamlama performansı</span>
                </div>
                <span className="text-xs font-semibold text-cyan-400 font-mono">
                  {(stats.total_tasks > 0 ? (stats.completed_tasks / stats.total_tasks) * 100 : 100).toFixed(0)}% Zamanında
                </span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-gradient-to-r from-cyan-950/20 to-purple-950/20 border border-cyan-500/20 rounded-xl text-[11px] text-[#80deea] leading-relaxed">
            <strong className="text-white block mb-1">💡 Sistem Önerisi:</strong>
            FMEA RPN risk limitlerinin aşılmaması için aksiyon planı atamalarını DevOps board üzerinden takip ederek geciken aksiyonları denetleyin.
          </div>
        </div>
      </div>
    </div>
  );
}
