"use client";

import Link from "next/link";
import { Header } from "@/components/layout/header";
import { StatCard } from "@/components/ui/stat-card";
import { cn, formatDate } from "@/lib/utils";
import { Coins, CreditCard, ReceiptText, TrendingDown } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

type RangeValue = "7d" | "30d" | "90d";

interface TokenOverviewResponse {
  wallet: {
    remainingTokens: number;
    totalConsumedTokens: number;
    totalRechargedTokens: number;
  };
  usageTrend: {
    date: string;
    consumed: number;
    recharged: number;
    net: number;
  }[];
  recentRecharges: {
    id: string;
    amountCents: number;
    tokens: number;
    completedAt: string | null;
    createdAt: string | null;
  }[];
}

const rangeOptions: { label: string; value: RangeValue }[] = [
  { label: "7 天", value: "7d" },
  { label: "30 天", value: "30d" },
  { label: "90 天", value: "90d" },
];

function TokenTrendChart({
  range,
  onRangeChange,
  data,
}: {
  range: RangeValue;
  onRangeChange: (value: RangeValue) => void;
  data: {
    label: string;
    value: number;
  }[];
}) {
  const chart = useMemo(() => {
    const chartHeight = 320;
    const chartWidth = Math.max(920, data.length * 34);
    const padding = { top: 20, right: 24, bottom: 52, left: 52 };
    const innerWidth = chartWidth - padding.left - padding.right;
    const innerHeight = chartHeight - padding.top - padding.bottom;
    const maxValue = Math.max(...data.map((item) => item.value), 0);
    const yMax = maxValue > 0 ? maxValue : 1;
    const step = data.length > 1 ? innerWidth / (data.length - 1) : innerWidth;
    const barWidth = Math.max(10, Math.min(22, step * 0.58));

    const points = data.map((item, index) => {
      const x = padding.left + (data.length === 1 ? innerWidth / 2 : step * index);
      const height = (item.value / yMax) * innerHeight;
      const y = padding.top + innerHeight - height;

      return {
        ...item,
        barWidth,
        x,
        y,
        height,
      };
    });

    const path = points
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
      .join(" ");

    const ticks = Array.from({ length: 5 }, (_, index) => {
      const value = (yMax / 4) * (4 - index);
      const y = padding.top + (innerHeight / 4) * index;
      return {
        value: Math.round(value),
        y,
      };
    });

    return {
      chartHeight,
      chartWidth,
      innerHeight,
      padding,
      path,
      points,
      ticks,
    };
  }, [data]);

  return (
    <section className="rounded-xl border border-owly-border bg-owly-surface">
      <div className="flex flex-col gap-4 border-b border-owly-border px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-sm font-semibold text-owly-text">Token 消耗趋势</h3>
          <p className="mt-1 text-xs text-owly-text-light">
            选择统计区间后，可通过柱状图和折线同时观察每日 token 消耗变化。
          </p>
        </div>
        <div className="flex gap-2 rounded-lg bg-owly-bg p-1">
          {rangeOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => onRangeChange(option.value)}
              className={cn(
                "rounded-md px-4 py-2 text-sm font-medium transition-colors",
                range === option.value
                  ? "bg-owly-primary text-white"
                  : "text-owly-text-light hover:text-owly-text"
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto px-4 py-4">
        <div className="min-w-[960px]">
          <svg
            viewBox={`0 0 ${chart.chartWidth} ${chart.chartHeight}`}
            className="h-[320px] w-full"
            role="img"
            aria-label="Token 消耗趋势图"
          >
            {chart.ticks.map((tick) => (
              <g key={tick.y}>
                <line
                  x1={chart.padding.left}
                  x2={chart.chartWidth - chart.padding.right}
                  y1={tick.y}
                  y2={tick.y}
                  stroke="rgba(148, 163, 184, 0.2)"
                  strokeDasharray="4 4"
                />
                <text
                  x={chart.padding.left - 10}
                  y={tick.y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="#94a3b8"
                >
                  {tick.value}
                </text>
              </g>
            ))}

            <line
              x1={chart.padding.left}
              x2={chart.chartWidth - chart.padding.right}
              y1={chart.padding.top + chart.innerHeight}
              y2={chart.padding.top + chart.innerHeight}
              stroke="rgba(15, 23, 42, 0.18)"
            />

            {chart.points.map((point) => (
              <g key={point.label}>
                <rect
                  x={point.x - point.barWidth / 2}
                  y={point.y}
                  width={point.barWidth}
                  height={point.height}
                  rx={6}
                  fill="rgba(59, 130, 246, 0.22)"
                  stroke="rgba(59, 130, 246, 0.45)"
                />
                <text
                  x={point.x}
                  y={chart.chartHeight - 18}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#94a3b8"
                >
                  {point.label}
                </text>
              </g>
            ))}

            <path
              d={chart.path}
              fill="none"
              stroke="#2563eb"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {chart.points.map((point) => (
              <g key={`${point.label}-dot`}>
                <circle cx={point.x} cy={point.y} r="4.5" fill="#2563eb" />
                <circle cx={point.x} cy={point.y} r="2" fill="#ffffff" />
              </g>
            ))}
          </svg>
        </div>
      </div>
    </section>
  );
}

export default function TokenUsagePage() {
  const [range, setRange] = useState<RangeValue>("30d");
  const [data, setData] = useState<TokenOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const isInitialLoading = loading && !data;

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/tokens/overview?range=${range}`);
      if (res.ok) {
        setData(await res.json());
      }
    } finally {
      setLoading(false);
    }
  }, [range]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  return (
    <>
      <Header
        title="Token 用量"
        description="查看 token 剩余总量、区间消耗趋势与充值记录。"
        actions={
          <Link
            href="/token-usage/recharge"
            className="inline-flex items-center gap-2 rounded-lg bg-owly-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-owly-primary-dark"
          >
            <CreditCard className="h-4 w-4" />
            充值
          </Link>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-[1400px] space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard
              title="剩余 Token"
              value={isInitialLoading ? "--" : (data?.wallet.remainingTokens || 0).toLocaleString()}
              icon={Coins}
              iconColor="bg-owly-primary-50 text-owly-primary"
            />
            <StatCard
              title="累计消耗"
              value={isInitialLoading ? "--" : (data?.wallet.totalConsumedTokens || 0).toLocaleString()}
              icon={TrendingDown}
              iconColor="bg-red-50 text-red-600"
            />
            <StatCard
              title="累计充值"
              value={isInitialLoading ? "--" : (data?.wallet.totalRechargedTokens || 0).toLocaleString()}
              icon={CreditCard}
              iconColor="bg-green-50 text-green-600"
            />
            <StatCard
              title="充值记录"
              value={isInitialLoading ? "--" : `${data?.recentRecharges.length || 0}`}
              icon={ReceiptText}
              iconColor="bg-amber-50 text-amber-600"
            />
          </div>

          <TokenTrendChart
            range={range}
            onRangeChange={setRange}
            data={(data?.usageTrend || []).map((item) => ({
              label: item.date.slice(5),
              value: item.consumed,
            }))}
          />

          <section className="rounded-xl border border-owly-border bg-owly-surface">
            <div className="border-b border-owly-border px-5 py-4">
              <h3 className="text-sm font-semibold text-owly-text">最近充值记录</h3>
              <p className="mt-1 text-xs text-owly-text-light">
                记录仅展示金额、Token 和时间。
              </p>
            </div>

            <div className="overflow-hidden">
              <div className="grid grid-cols-[140px_140px_180px] gap-4 bg-owly-bg px-5 py-3 text-xs font-semibold uppercase tracking-wide text-owly-text-light">
                <span>金额</span>
                <span>Token</span>
                <span>时间</span>
              </div>

              <div className="divide-y divide-owly-border">
                {(data?.recentRecharges || []).length > 0 ? (
                  data?.recentRecharges.map((record) => (
                    <div
                      key={record.id}
                      className="grid grid-cols-[140px_140px_180px] gap-4 px-5 py-4 text-sm"
                    >
                      <p className="text-owly-text">￥{(record.amountCents / 100).toFixed(2)}</p>
                      <p className="text-owly-text">{record.tokens.toLocaleString()}</p>
                      <p className="text-xs text-owly-text-light">
                        {formatDate(record.completedAt || record.createdAt || "")}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="px-5 py-10 text-center text-sm text-owly-text-light">
                    暂无充值记录
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
