"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { StatCard } from "@/components/ui/stat-card";
import { OnboardingChecklist } from "@/components/ui/onboarding-checklist";
import {
  MessageSquare,
  Ticket,
  Phone,
  Mail,
  MessageCircle,
  CheckCircle,
  Clock,
} from "lucide-react";
import { formatRelativeTime, getChannelLabel, getStatusColor, getStatusLabel } from "@/lib/utils";

interface StatsResponse {
  totalConversations: number;
  activeConversations: number;
  totalTickets: number;
  openTickets: number;
  totalMessages: number;
  resolutionRate: number;
}

interface ConversationItem {
  id: string;
  channel: string;
  customerName: string;
  status: string;
  updatedAt: string;
  messages: { id: string; content: string }[];
  _count: { messages: number };
}

const emptyStats: StatsResponse = {
  totalConversations: 0,
  activeConversations: 0,
  totalTickets: 0,
  openTickets: 0,
  totalMessages: 0,
  resolutionRate: 0,
};

const channelIcons: Record<string, React.ElementType> = {
  whatsapp: MessageCircle,
  email: Mail,
  phone: Phone,
};

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse>(emptyStats);
  const [recentConversations, setRecentConversations] = useState<ConversationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const [statsRes, conversationsRes] = await Promise.all([
          fetch("/api/stats"),
          fetch("/api/conversations?limit=10"),
        ]);

        const statsData = statsRes.ok ? await statsRes.json() : emptyStats;
        const conversationsData = conversationsRes.ok ? await conversationsRes.json() : { data: [] };

        if (!active) {
          return;
        }

        setStats({
          totalConversations: statsData.totalConversations ?? 0,
          activeConversations: statsData.activeConversations ?? 0,
          totalTickets: statsData.totalTickets ?? 0,
          openTickets: statsData.openTickets ?? 0,
          totalMessages: statsData.totalMessages ?? 0,
          resolutionRate: statsData.resolutionRate ?? 0,
        });
        setRecentConversations(Array.isArray(conversationsData.data) ? conversationsData.data : []);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      <Header
        title="仪表盘"
        description="查看客户支持工作的整体情况"
      />
      <div className="flex-1 overflow-auto p-6 space-y-6">
        <OnboardingChecklist />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="会话总数"
            value={loading ? "..." : stats.totalConversations}
            icon={MessageSquare}
          />
          <StatCard
            title="当前活跃"
            value={loading ? "..." : stats.activeConversations}
            icon={Clock}
            iconColor="bg-green-50 text-green-600"
          />
          <StatCard
            title="未处理工单"
            value={loading ? "..." : stats.openTickets}
            icon={Ticket}
            iconColor="bg-orange-50 text-orange-600"
          />
          <StatCard
            title="解决率"
            value={loading ? "..." : `${stats.resolutionRate}%`}
            icon={CheckCircle}
            iconColor="bg-blue-50 text-blue-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-owly-surface rounded-xl border border-owly-border">
            <div className="px-5 py-4 border-b border-owly-border">
              <h3 className="font-semibold text-owly-text">
                最近会话
              </h3>
            </div>
            <div className="divide-y divide-owly-border">
              {!loading && recentConversations.length === 0 ? (
                <div className="px-5 py-12 text-center text-owly-text-light">
                  <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">暂无会话</p>
                  <p className="text-sm mt-1">
                    客户开始联系后，会话会显示在这里
                  </p>
                </div>
              ) : (
                recentConversations.map((conv) => {
                  const ChannelIcon =
                    channelIcons[conv.channel] || MessageSquare;
                  const lastMessage = conv.messages?.[0];
                  return (
                    <div
                      key={conv.id}
                      className="px-5 py-3.5 hover:bg-owly-primary-50/50 transition-colors cursor-pointer"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-owly-primary-50 text-owly-primary mt-0.5">
                          <ChannelIcon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="font-medium text-sm text-owly-text truncate">
                              {conv.customerName}
                            </p>
                            <span className="text-xs text-owly-text-light flex-shrink-0 ml-2">
                              {formatRelativeTime(conv.updatedAt)}
                            </span>
                          </div>
                          <p className="text-xs text-owly-text-light mt-0.5">
                            {getChannelLabel(conv.channel)} -{" "}
                            {conv._count?.messages ?? 0} 条消息
                          </p>
                          {lastMessage && (
                            <p className="text-sm text-owly-text-light mt-1 truncate">
                              {lastMessage.content}
                            </p>
                          )}
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(conv.status)}`}
                        >
                          {getStatusLabel(conv.status)}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
              {loading && (
                <div className="px-5 py-6 text-sm text-owly-text-light">
                  正在加载最近活动...
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-owly-surface rounded-xl border border-owly-border">
              <div className="px-5 py-4 border-b border-owly-border">
                <h3 className="font-semibold text-owly-text">
                  渠道概览
                </h3>
              </div>
              <div className="p-5 space-y-4">
                {[
                  {
                    name: "WhatsApp",
                    icon: MessageCircle,
                    color: "text-green-600",
                  },
                  { name: "邮箱", icon: Mail, color: "text-blue-600" },
                  { name: "电话", icon: Phone, color: "text-purple-600" },
                ].map((channel) => (
                  <div
                    key={channel.name}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2.5">
                      <channel.icon
                        className={`h-4 w-4 ${channel.color}`}
                      />
                      <span className="text-sm font-medium">
                        {channel.name}
                      </span>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-600 font-medium">
                      未连接
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-owly-surface rounded-xl border border-owly-border">
              <div className="px-5 py-4 border-b border-owly-border">
                <h3 className="font-semibold text-owly-text">快速概览</h3>
              </div>
              <div className="p-5 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-owly-text-light">消息总数</span>
                  <span className="font-medium">{stats.totalMessages}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-owly-text-light">工单总数</span>
                  <span className="font-medium">{stats.totalTickets}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-owly-text-light">
                    平均解决率
                  </span>
                  <span className="font-medium">{stats.resolutionRate}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
