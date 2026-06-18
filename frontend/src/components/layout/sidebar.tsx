"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  BookOpen,
  Bot,
  Users,
  Contact,
  MessageSquare,
  Settings,
  Radio,
  Ticket,
  BarChart3,
  ScrollText,
  Timer,
  Zap,
  Workflow,
  Clock,
  Shield,
  FileCode,
  Webhook,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

interface NavSection {
  title?: string;
  items: { name: string; href: string; icon: React.ElementType }[];
}

const sections: NavSection[] = [
  {
    items: [
      { name: "仪表盘", href: "/", icon: LayoutDashboard },
      { name: "会话", href: "/conversations", icon: MessageSquare },
      { name: "客户", href: "/customers", icon: Contact },
      { name: "工单", href: "/tickets", icon: Ticket },
    ],
  },
  {
    title: "知识",
    items: [
      { name: "知识库", href: "/knowledge", icon: BookOpen },
      { name: "AI 工作台", href: "/knowledge/ai-workspace", icon: Bot },
      { name: "快捷回复", href: "/canned-responses", icon: Zap },
      { name: "自动化", href: "/automation", icon: Workflow },
      { name: "营业时间", href: "/business-hours", icon: Clock },
    ],
  },
  {
    title: "团队",
    items: [
      { name: "团队", href: "/team", icon: Users },
      { name: "SLA 规则", href: "/sla", icon: Timer },
    ],
  },
  {
    title: "渠道",
    items: [
      { name: "渠道", href: "/channels", icon: Radio },
      { name: "Webhooks", href: "/webhooks", icon: Webhook },
    ],
  },
  {
    title: "洞察",
    items: [
      { name: "分析", href: "/analytics", icon: BarChart3 },
      { name: "Token 用量", href: "/token-usage", icon: BarChart3 },
      { name: "活动日志", href: "/activity", icon: ScrollText },
    ],
  },
  {
    title: "系统",
    items: [
      { name: "管理", href: "/admin", icon: Shield },
      { name: "API 文档", href: "/api-docs", icon: FileCode },
      { name: "设置", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col bg-owly-sidebar text-white transition-all duration-300",
        collapsed ? "w-16" : "w-60"
      )}
    >
      <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
        <Image
          src="/owly.png"
          alt="Owly"
          width={32}
          height={32}
          className="rounded-lg flex-shrink-0"
        />
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-base font-bold tracking-tight">Owly</h1>
            <p className="text-[10px] text-white/50">AI 客户支持</p>
          </div>
        )}
      </div>

      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-3">
        {sections.map((section, si) => (
          <div key={si}>
            {section.title && !collapsed && (
              <p className="px-3 mb-1 text-[10px] uppercase tracking-wider text-white/40 font-medium">
                {section.title}
              </p>
            )}
            {collapsed && si > 0 && (
              <div className="mx-3 mb-2 border-t border-white/10" />
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isKnowledgeRoot = item.href === "/knowledge";
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" &&
                    !isKnowledgeRoot &&
                    pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors",
                      isActive
                        ? "bg-owly-sidebar-active text-white"
                        : "text-white/65 hover:bg-owly-sidebar-hover hover:text-white"
                    )}
                    title={collapsed ? item.name : undefined}
                  >
                    <item.icon className="h-4 w-4 flex-shrink-0" />
                    {!collapsed && <span>{item.name}</span>}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-2 py-2 border-t border-white/10">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full py-1.5 rounded-md text-white/40 hover:text-white hover:bg-owly-sidebar-hover transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
