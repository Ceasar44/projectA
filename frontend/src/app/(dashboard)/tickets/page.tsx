"use client";

import { Header } from "@/components/layout/header";
import {
  Ticket,
  Search,
  Plus,
  X,
  User,
  MessageSquare,
  CheckCircle2,
  Clock,
  CircleDot,
  ExternalLink,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import {
  cn,
  formatRelativeTime,
  formatDate,
  getStatusColor,
  getPriorityColor,
  getStatusLabel,
  getPriorityLabel,
} from "@/lib/utils";

interface TicketData {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  resolution: string;
  conversationId: string | null;
  departmentId: string | null;
  assignedToId: string | null;
  conversation: {
    id: string;
    customerName: string;
    channel: string;
    status: string;
  } | null;
  department: {
    id: string;
    name: string;
  } | null;
  assignedTo: {
    id: string;
    name: string;
    email: string;
  } | null;
  createdAt: string;
  updatedAt: string;
}

interface DepartmentData {
  id: string;
  name: string;
}

interface TicketListResponse {
  data: TicketData[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

const ticketStatuses = [
  { value: "all", label: "全部状态" },
  { value: "open", label: "未处理" },
  { value: "in_progress", label: "处理中" },
  { value: "resolved", label: "已解决" },
  { value: "closed", label: "已关闭" },
];

const ticketPriorities = [
  { value: "all", label: "全部优先级" },
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
  { value: "urgent", label: "紧急" },
];

const statusIcons: Record<string, React.ElementType> = {
  open: CircleDot,
  in_progress: Clock,
  resolved: CheckCircle2,
  closed: CheckCircle2,
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [departments, setDepartments] = useState<DepartmentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTicket, setSelectedTicket] = useState<TicketData | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [saving, setSaving] = useState(false);

  // Create form state
  const [createForm, setCreateForm] = useState({
    title: "",
    description: "",
    priority: "medium",
    status: "open",
    departmentId: "",
  });

  const fetchTickets = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (priorityFilter !== "all") params.set("priority", priorityFilter);
      if (departmentFilter !== "all")
        params.set("departmentId", departmentFilter);
      if (searchQuery.trim()) params.set("search", searchQuery.trim());

      const res = await fetch(`/api/tickets?${params.toString()}`);
      if (res.ok) {
        const data: TicketListResponse = await res.json();
        setTickets(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, departmentFilter, searchQuery]);

  const fetchDepartments = useCallback(async () => {
    try {
      const res = await fetch("/api/team/departments");
      if (res.ok) {
        const data = await res.json();
        setDepartments(data);
      }
    } catch (error) {
      console.error("Failed to fetch departments:", error);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  const handleCreateTicket = async () => {
    if (!createForm.title.trim()) return;
    setSaving(true);
    try {
      const res = await fetch("/api/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...createForm,
          departmentId: createForm.departmentId || undefined,
        }),
      });
      if (res.ok) {
        setShowCreateModal(false);
        setCreateForm({
          title: "",
          description: "",
          priority: "medium",
          status: "open",
          departmentId: "",
        });
        fetchTickets();
      }
    } catch (error) {
      console.error("Failed to create ticket:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateTicket = async (
    id: string,
    updates: Record<string, unknown>
  ) => {
    try {
      const res = await fetch(`/api/tickets/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedTicket(updated);
        fetchTickets();
      }
    } catch (error) {
      console.error("Failed to update ticket:", error);
    }
  };

  const handleDeleteTicket = async (id: string) => {
    try {
      const res = await fetch(`/api/tickets/${id}`, { method: "DELETE" });
      if (res.ok) {
        setSelectedTicket(null);
        fetchTickets();
      }
    } catch (error) {
      console.error("Failed to delete ticket:", error);
    }
  };

  const openCount = tickets.filter((t) => t.status === "open").length;
  const inProgressCount = tickets.filter(
    (t) => t.status === "in_progress"
  ).length;
  const resolvedCount = tickets.filter((t) => t.status === "resolved").length;

  return (
    <>
      <Header
        title="工单"
        description="跟踪并管理客户问题"
        actions={
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-owly-primary text-white rounded-lg hover:bg-owly-primary-dark transition-colors text-sm font-medium"
          >
            <Plus className="h-4 w-4" />
            新建工单
          </button>
        }
      />

      <div className="flex-1 overflow-auto p-6 space-y-4">
        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="bg-owly-surface rounded-xl border border-owly-border px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-50">
              <CircleDot className="h-4 w-4 text-yellow-600" />
            </div>
            <div>
              <p className="text-xs text-owly-text-light">未处理</p>
              <p className="text-lg font-semibold text-owly-text">
                {openCount}
              </p>
            </div>
          </div>
          <div className="bg-owly-surface rounded-xl border border-owly-border px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50">
              <Clock className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-owly-text-light">处理中</p>
              <p className="text-lg font-semibold text-owly-text">
                {inProgressCount}
              </p>
            </div>
          </div>
          <div className="bg-owly-surface rounded-xl border border-owly-border px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-owly-text-light">已解决</p>
              <p className="text-lg font-semibold text-owly-text">
                {resolvedCount}
              </p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-owly-surface rounded-xl border border-owly-border p-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-owly-text-light" />
              <input
                type="text"
                placeholder="搜索工单..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
            >
              {ticketStatuses.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
            >
              {ticketPriorities.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
            >
              <option value="all">全部部门</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tickets Table */}
        <div className="bg-owly-surface rounded-xl border border-owly-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="text-sm text-owly-text-light">正在加载...</div>
            </div>
          ) : tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
              <div className="p-4 rounded-full bg-owly-primary-50 mb-4">
                <Ticket className="h-8 w-8 text-owly-primary" />
              </div>
              <p className="font-medium text-owly-text">未找到工单</p>
              <p className="text-sm text-owly-text-light mt-1">
                创建工单来开始跟踪客户问题
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 flex items-center gap-2 px-4 py-2 bg-owly-primary text-white rounded-lg hover:bg-owly-primary-dark transition-colors text-sm font-medium"
              >
                <Plus className="h-4 w-4" />
                创建工单
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-owly-border bg-owly-bg/50">
                    <th className="text-left px-4 py-3 text-xs font-medium text-owly-text-light uppercase tracking-wider">
                      工单
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-owly-text-light uppercase tracking-wider">
                      状态
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-owly-text-light uppercase tracking-wider">
                      优先级
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-owly-text-light uppercase tracking-wider hidden md:table-cell">
                      部门
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-owly-text-light uppercase tracking-wider hidden lg:table-cell">
                      负责人
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-owly-text-light uppercase tracking-wider hidden lg:table-cell">
                      创建时间
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-owly-border">
                  {tickets.map((ticket) => {
                    const StatusIcon =
                      statusIcons[ticket.status] || CircleDot;

                    return (
                      <tr
                        key={ticket.id}
                        onClick={() => setSelectedTicket(ticket)}
                        className="hover:bg-owly-primary-50/50 cursor-pointer transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-start gap-3">
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-owly-text truncate max-w-[280px]">
                                {ticket.title}
                              </p>
                              {ticket.conversation && (
                                <p className="text-xs text-owly-text-light mt-0.5">
                                  {ticket.conversation.customerName}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-full text-xs font-medium inline-flex items-center gap-1",
                              getStatusColor(ticket.status)
                            )}
                          >
                            <StatusIcon className="h-3 w-3" />
                            {getStatusLabel(ticket.status)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-full text-xs font-medium",
                              getPriorityColor(ticket.priority)
                            )}
                          >
                            {getPriorityLabel(ticket.priority)}
                          </span>
                        </td>
                        <td className="px-4 py-3 hidden md:table-cell">
                          <span className="text-sm text-owly-text-light">
                            {ticket.department?.name || "--"}
                          </span>
                        </td>
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <span className="text-sm text-owly-text-light">
                            {ticket.assignedTo?.name || "未分配"}
                          </span>
                        </td>
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <span className="text-xs text-owly-text-light">
                            {formatRelativeTime(ticket.createdAt)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Ticket Detail Panel */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setSelectedTicket(null)}
          />
          <div className="relative w-full max-w-lg bg-owly-surface shadow-xl flex flex-col animate-in slide-in-from-right">
            {/* Detail Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-owly-border">
              <h3 className="font-semibold text-owly-text text-lg">
                工单详情
              </h3>
              <button
                onClick={() => setSelectedTicket(null)}
                className="p-1.5 hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-owly-text-light" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
              {/* Title */}
              <div>
                <h4 className="text-lg font-semibold text-owly-text">
                  {selectedTicket.title}
                </h4>
                <p className="text-xs text-owly-text-light mt-1">
                  创建于 {formatDate(selectedTicket.createdAt)}
                </p>
              </div>

              {/* Status and Priority Controls */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-owly-text-light mb-1">
                    状态
                  </label>
                  <select
                    value={selectedTicket.status}
                    onChange={(e) =>
                      handleUpdateTicket(selectedTicket.id, {
                        status: e.target.value,
                      })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                  >
                    {ticketStatuses
                      .filter((s) => s.value !== "all")
                      .map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-owly-text-light mb-1">
                    优先级
                  </label>
                  <select
                    value={selectedTicket.priority}
                    onChange={(e) =>
                      handleUpdateTicket(selectedTicket.id, {
                        priority: e.target.value,
                      })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                  >
                    {ticketPriorities
                      .filter((p) => p.value !== "all")
                      .map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              {/* Department */}
              <div>
                <label className="block text-xs font-medium text-owly-text-light mb-1">
                  部门
                </label>
                <select
                  value={selectedTicket.departmentId || ""}
                  onChange={(e) =>
                    handleUpdateTicket(selectedTicket.id, {
                      departmentId: e.target.value || null,
                    })
                  }
                  className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                >
                  <option value="">未分配</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Assigned To */}
              <div>
                <label className="block text-xs font-medium text-owly-text-light mb-1">
                  负责人
                </label>
                <div className="flex items-center gap-2 px-3 py-2 border border-owly-border rounded-lg bg-owly-bg">
                  <User className="h-4 w-4 text-owly-text-light" />
                  <span className="text-sm text-owly-text">
                    {selectedTicket.assignedTo?.name || "未分配"}
                  </span>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-medium text-owly-text-light mb-1">
                  描述
                </label>
                <div className="px-3 py-2.5 border border-owly-border rounded-lg bg-owly-bg min-h-[80px]">
                  <p className="text-sm text-owly-text whitespace-pre-wrap">
                    {selectedTicket.description || "未提供描述。"}
                  </p>
                </div>
              </div>

              {/* Linked Conversation */}
              {selectedTicket.conversation && (
                <div>
                  <label className="block text-xs font-medium text-owly-text-light mb-1">
                    关联会话
                  </label>
                  <div className="flex items-center gap-3 px-3 py-2.5 border border-owly-border rounded-lg bg-owly-bg">
                    <MessageSquare className="h-4 w-4 text-owly-primary flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-owly-text truncate">
                        {selectedTicket.conversation.customerName}
                      </p>
                      <p className="text-xs text-owly-text-light">
                        {selectedTicket.conversation.channel} --{" "}
                        {getStatusLabel(selectedTicket.conversation.status)}
                      </p>
                    </div>
                    <a
                      href={`/conversations`}
                      className="p-1 hover:bg-owly-primary-50 rounded transition-colors"
                    >
                      <ExternalLink className="h-3.5 w-3.5 text-owly-primary" />
                    </a>
                  </div>
                </div>
              )}

              {/* Resolution */}
              <div>
                <label className="block text-xs font-medium text-owly-text-light mb-1">
                  处理结果
                </label>
                <textarea
                  value={selectedTicket.resolution}
                  onChange={(e) => {
                    setSelectedTicket({
                      ...selectedTicket,
                      resolution: e.target.value,
                    });
                  }}
                  onBlur={() =>
                    handleUpdateTicket(selectedTicket.id, {
                      resolution: selectedTicket.resolution,
                    })
                  }
                  placeholder="添加处理结果备注..."
                  rows={3}
                  className="w-full text-sm px-3 py-2.5 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary resize-none"
                />
              </div>
            </div>

            {/* Detail Footer */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-owly-border">
              <button
                onClick={() => handleDeleteTicket(selectedTicket.id)}
                className="text-sm text-owly-danger hover:text-red-700 font-medium transition-colors"
              >
                删除工单
              </button>
              <button
                onClick={() => setSelectedTicket(null)}
                className="px-4 py-2 text-sm font-medium bg-owly-primary text-white rounded-lg hover:bg-owly-primary-dark transition-colors"
              >
                完成
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="relative w-full max-w-md mx-4 bg-owly-surface rounded-xl shadow-xl">
            <div className="flex items-center justify-between px-5 py-4 border-b border-owly-border">
              <h3 className="font-semibold text-owly-text text-lg">
                新建工单
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1.5 hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-owly-text-light" />
              </button>
            </div>

            <div className="px-5 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-owly-text mb-1">
                  标题
                </label>
                <input
                  type="text"
                  value={createForm.title}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, title: e.target.value })
                  }
                  placeholder="请输入工单标题..."
                  className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-owly-text mb-1">
                  描述
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      description: e.target.value,
                    })
                  }
                  placeholder="描述问题..."
                  rows={3}
                  className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1">
                    优先级
                  </label>
                  <select
                    value={createForm.priority}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        priority: e.target.value,
                      })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                  >
                    {ticketPriorities
                      .filter((p) => p.value !== "all")
                      .map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1">
                    部门
                  </label>
                  <select
                    value={createForm.departmentId}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        departmentId: e.target.value,
                      })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                  >
                    <option value="">无</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-owly-border">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-owly-text hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateTicket}
                disabled={!createForm.title.trim() || saving}
                className={cn(
                  "px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                  createForm.title.trim() && !saving
                    ? "bg-owly-primary text-white hover:bg-owly-primary-dark"
                    : "bg-owly-border text-owly-text-light cursor-not-allowed"
                )}
              >
                {saving ? "正在创建..." : "创建工单"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
