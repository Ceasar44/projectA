import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelativeTime(date: Date | string): string {
  const now = new Date();
  const d = new Date(date);
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "刚刚";
  if (diffMins < 60) return `${diffMins} 分钟前`;
  if (diffHours < 24) return `${diffHours} 小时前`;
  if (diffDays < 7) return `${diffDays} 天前`;
  return formatDate(date);
}

export function getChannelLabel(channel: string): string {
  const labels: Record<string, string> = {
    whatsapp: "WhatsApp",
    email: "邮箱",
    phone: "电话",
  };
  return labels[channel] || channel;
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: "活跃",
    resolved: "已解决",
    escalated: "已升级",
    closed: "已关闭",
    open: "未处理",
    in_progress: "处理中",
    connected: "已连接",
    disconnected: "未连接",
    error: "错误",
    pending: "待处理",
  };
  return labels[status] || status;
}

export function getPriorityLabel(priority: string): string {
  const labels: Record<string, string> = {
    low: "低",
    medium: "中",
    high: "高",
    urgent: "紧急",
  };
  return labels[priority] || priority;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    resolved: "bg-blue-100 text-blue-700",
    escalated: "bg-orange-100 text-orange-700",
    closed: "bg-gray-100 text-gray-700",
    open: "bg-yellow-100 text-yellow-700",
    in_progress: "bg-blue-100 text-blue-700",
    connected: "bg-green-100 text-green-700",
    disconnected: "bg-red-100 text-red-700",
    error: "bg-red-100 text-red-700",
  };
  return colors[status] || "bg-gray-100 text-gray-700";
}

export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    low: "bg-gray-100 text-gray-700",
    medium: "bg-yellow-100 text-yellow-700",
    high: "bg-orange-100 text-orange-700",
    urgent: "bg-red-100 text-red-700",
  };
  return colors[priority] || "bg-gray-100 text-gray-700";
}
