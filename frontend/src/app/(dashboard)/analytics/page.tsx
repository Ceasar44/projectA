"use client";

import { useEffect, useState, useCallback } from "react";
import { StatCard } from "@/components/ui/stat-card";
import { BarChart, LineChart, DonutChart } from "@/components/ui/chart";
import {
  MessageSquare,
  Clock,
  CheckCircle2,
  Star,
  Users,
} from "lucide-react";
import { cn, getChannelLabel, getPriorityLabel, getStatusLabel } from "@/lib/utils";

// ==================== TYPES ====================

interface AnalyticsData {
  conversationsPerDay: { date: string; count: number }[];
  channelBreakdown: { channel: string; count: number }[];
  avgResponseTime: number;
  resolutionRate: number;
  satisfactionAvg: number;
  ticketsByPriority: { priority: string; count: number }[];
  ticketsByStatus: { status: string; count: number }[];
  topCategories: { category: string; hitCount: number }[];
  teamPerformance: { member: string; ticketsResolved: number; avgTime: number }[];
  totalConversations: number;
}

type Period = "7d" | "30d" | "90d";

const PERIOD_OPTIONS: { label: string; value: Period }[] = [
  { label: "7 天", value: "7d" },
  { label: "30 天", value: "30d" },
  { label: "90 天", value: "90d" },
];

const PRIORITY_COLORS: Record<string, string> = {
  low: "#64748B",
  medium: "#F59E0B",
  high: "#C4956A",
  urgent: "#EF4444",
};

const STATUS_COLORS: Record<string, string> = {
  open: "#F59E0B",
  in_progress: "#4A7C9B",
  resolved: "#22C55E",
  closed: "#64748B",
  escalated: "#EF4444",
};

const CHANNEL_COLORS: Record<string, string> = {
  whatsapp: "#22C55E",
  email: "#4A7C9B",
  phone: "#C4956A",
  web: "#8B5CF6",
  chat: "#A8D0E6",
};

// ==================== SKELETON ====================

function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-owly-border/50",
        className
      )}
    />
  );
}

function StatCardSkeleton() {
  return (
    <div className="bg-owly-surface rounded-xl border border-owly-border p-5">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-7 w-16" />
        </div>
        <Skeleton className="h-10 w-10 rounded-lg" />
      </div>
    </div>
  );
}

function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div className="bg-owly-surface rounded-xl border border-owly-border p-5">
      <Skeleton className="h-4 w-40 mb-4" />
      <div className="w-full animate-pulse rounded bg-owly-border/60" style={{ height }} />
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="bg-owly-surface rounded-xl border border-owly-border p-5">
      <Skeleton className="h-4 w-40 mb-4" />
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

// ==================== HELPER ====================

function formatMinutes(mins: number): string {
  if (mins < 1) return "<1 分钟";
  if (mins < 60) return `${Math.round(mins)} 分钟`;
  const h = Math.floor(mins / 60);
  const m = Math.round(mins % 60);
  return m > 0 ? `${h} 小时 ${m} 分钟` : `${h} 小时`;
}

// ==================== PAGE ====================

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [period, setPeriod] = useState<Period>("30d");
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/analytics?period=${period}`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch {
      // silently handle
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-owly-text">分析</h1>
          <p className="text-sm text-owly-text-light mt-1">
            监控客服支持表现
          </p>
        </div>

        {/* Period selector */}
        <div className="flex bg-owly-surface border border-owly-border rounded-lg p-1">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={cn(
                "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                period === opt.value
                  ? "bg-owly-primary text-white"
                  : "text-owly-text-light hover:text-owly-text"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Row 1: Stat cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="会话总数"
            value={data.totalConversations.toLocaleString()}
            icon={MessageSquare}
            iconColor="bg-owly-primary-50 text-owly-primary"
          />
          <StatCard
            title="平均响应时间"
            value={formatMinutes(data.avgResponseTime)}
            icon={Clock}
            iconColor="bg-amber-50 text-amber-600"
          />
          <StatCard
            title="解决率"
            value={`${data.resolutionRate}%`}
            icon={CheckCircle2}
            iconColor="bg-green-50 text-green-600"
          />
          <StatCard
            title="满意度评分"
            value={
              data.satisfactionAvg > 0
                ? `${data.satisfactionAvg} / 5`
                : "--"
            }
            icon={Star}
            iconColor="bg-purple-50 text-purple-600"
          />
        </div>
      ) : null}

      {/* Row 2: Line chart + Donut chart */}
      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <ChartSkeleton height={300} />
          <ChartSkeleton height={300} />
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <LineChart
            title="会话趋势"
            data={data.conversationsPerDay.map((d) => ({
              label: d.date.slice(5), // MM-DD
              value: d.count,
            }))}
            height={300}
            className="lg:col-span-2"
          />
          <DonutChart
            title="渠道分布"
            data={data.channelBreakdown.map((d) => ({
              label: getChannelLabel(d.channel),
              value: d.count,
              color: CHANNEL_COLORS[d.channel] || undefined,
            }))}
            height={300}
          />
        </div>
      ) : null}

      {/* Row 3: Bar charts */}
      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartSkeleton height={260} />
          <ChartSkeleton height={260} />
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BarChart
            title="按优先级统计工单"
            data={data.ticketsByPriority.map((d) => ({
              label: getPriorityLabel(d.priority),
              value: d.count,
              color: PRIORITY_COLORS[d.priority] || undefined,
            }))}
            height={260}
          />
          <BarChart
            title="按状态统计工单"
            data={data.ticketsByStatus.map((d) => ({
              label: getStatusLabel(d.status),
              value: d.count,
              color: STATUS_COLORS[d.status] || undefined,
            }))}
            height={260}
          />
        </div>
      ) : null}

      {/* Row 4: Team performance table */}
      {loading ? (
        <TableSkeleton />
      ) : data && data.teamPerformance.length > 0 ? (
        <div className="bg-owly-surface rounded-xl border border-owly-border p-5">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-4 w-4 text-owly-text-light" />
            <h3 className="text-sm font-semibold text-owly-text">
              团队表现
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-owly-border text-left">
                  <th className="pb-3 font-medium text-owly-text-light">
                    团队成员
                  </th>
                  <th className="pb-3 font-medium text-owly-text-light text-right">
                    已解决工单
                  </th>
                  <th className="pb-3 font-medium text-owly-text-light text-right">
                    平均解决时间
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.teamPerformance.map((tp) => (
                  <tr
                    key={tp.member}
                    className="border-b border-owly-border/50 last:border-0"
                  >
                    <td className="py-3 font-medium text-owly-text">
                      {tp.member}
                    </td>
                    <td className="py-3 text-right text-owly-text">
                      <span className="inline-flex items-center justify-center min-w-[28px] px-2 py-0.5 rounded-full bg-owly-primary-50 text-owly-primary text-xs font-semibold">
                        {tp.ticketsResolved}
                      </span>
                    </td>
                    <td className="py-3 text-right text-owly-text-light">
                      {formatMinutes(tp.avgTime)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
