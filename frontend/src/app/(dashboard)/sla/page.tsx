"use client";

import { Header } from "@/components/layout/header";
import {
  Timer,
  Plus,
  X,
  Pencil,
  Trash2,
  Info,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";

interface SLARuleData {
  id: string;
  name: string;
  description: string;
  channel: string;
  priority: string;
  firstResponseMins: number;
  resolutionMins: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface SLAListResponse {
  data: SLARuleData[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

const channelOptions = [
  { value: "all", label: "全部渠道" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "email", label: "邮箱" },
  { value: "phone", label: "电话" },
];

const priorityOptions = [
  { value: "all", label: "全部优先级" },
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
  { value: "urgent", label: "紧急" },
];

const defaultForm = {
  name: "",
  description: "",
  channel: "all",
  priority: "all",
  firstResponseMins: 30,
  resolutionMins: 480,
  isActive: true,
};

function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  const remaining = mins % 60;
  return remaining > 0 ? `${hours}h ${remaining}m` : `${hours}h`;
}

export default function SLAPage() {
  const [rules, setRules] = useState<SLARuleData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState<SLARuleData | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(defaultForm);

  const fetchRules = useCallback(async () => {
    try {
      const res = await fetch("/api/sla");
      if (res.ok) {
        const data: SLAListResponse = await res.json();
        setRules(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch SLA rules:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  const openCreateModal = () => {
    setEditingRule(null);
    setForm(defaultForm);
    setShowModal(true);
  };

  const openEditModal = (rule: SLARuleData) => {
    setEditingRule(rule);
    setForm({
      name: rule.name,
      description: rule.description,
      channel: rule.channel,
      priority: rule.priority,
      firstResponseMins: rule.firstResponseMins,
      resolutionMins: rule.resolutionMins,
      isActive: rule.isActive,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const url = editingRule ? `/api/sla/${editingRule.id}` : "/api/sla";
      const method = editingRule ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setShowModal(false);
        setEditingRule(null);
        setForm(defaultForm);
        fetchRules();
      }
    } catch (error) {
      console.error("Failed to save SLA rule:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/sla/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDeleteConfirm(null);
        fetchRules();
      }
    } catch (error) {
      console.error("Failed to delete SLA rule:", error);
    }
  };

  const handleToggleActive = async (rule: SLARuleData) => {
    try {
      const res = await fetch(`/api/sla/${rule.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isActive: !rule.isActive }),
      });
      if (res.ok) {
        fetchRules();
      }
    } catch (error) {
      console.error("Failed to toggle SLA rule:", error);
    }
  };

  return (
    <>
      <Header
        title="SLA 规则"
        description="为团队设置响应时间目标"
        actions={
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2 bg-owly-primary text-white rounded-lg hover:bg-owly-primary-dark transition-colors text-sm font-medium"
          >
            <Plus className="h-4 w-4" />
            添加规则
          </button>
        }
      />

      <div className="flex-1 overflow-auto p-6 space-y-4">
        {/* Info Section */}
        <div className="bg-owly-primary-50 rounded-xl border border-owly-primary/20 p-4 flex items-start gap-3">
          <Info className="h-5 w-5 text-owly-primary flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-owly-text">
              What are SLA Rules?
            </p>
            <p className="text-sm text-owly-text-light mt-1">
              Service Level Agreement rules define response time targets for your
              support team. Configure first response and resolution time goals
              based on channel and priority to ensure consistent service quality.
            </p>
          </div>
        </div>

        {/* Rules Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="text-sm text-owly-text-light">正在加载...</div>
          </div>
        ) : rules.length === 0 ? (
          <div className="bg-owly-surface rounded-xl border border-owly-border">
            <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
              <div className="p-4 rounded-full bg-owly-primary-50 mb-4">
                <Timer className="h-8 w-8 text-owly-primary" />
              </div>
              <p className="font-medium text-owly-text">暂无 SLA 规则</p>
              <p className="text-sm text-owly-text-light mt-1">
                创建第一条 SLA 规则来设置响应时间目标
              </p>
              <button
                onClick={openCreateModal}
                className="mt-4 flex items-center gap-2 px-4 py-2 bg-owly-primary text-white rounded-lg hover:bg-owly-primary-dark transition-colors text-sm font-medium"
              >
                <Plus className="h-4 w-4" />
                添加规则
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className={cn(
                  "bg-owly-surface rounded-xl border border-owly-border p-5 transition-colors",
                  !rule.isActive && "opacity-60"
                )}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-owly-text truncate">
                      {rule.name}
                    </h3>
                    {rule.description && (
                      <p className="text-xs text-owly-text-light mt-0.5 line-clamp-2">
                        {rule.description}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => openEditModal(rule)}
                      className="p-1.5 hover:bg-owly-primary-50 rounded-lg transition-colors"
                    >
                      <Pencil className="h-3.5 w-3.5 text-owly-text-light" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(rule.id)}
                      className="p-1.5 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-owly-text-light" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-owly-primary-50 text-owly-primary">
                    {channelOptions.find((c) => c.value === rule.channel)?.label || rule.channel}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                    {priorityOptions.find((p) => p.value === rule.priority)?.label || rule.priority}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-owly-text-light" />
                    <div>
                      <p className="text-xs text-owly-text-light">
                        First Response
                      </p>
                      <p className="text-sm font-medium text-owly-text">
                        {formatMinutes(rule.firstResponseMins)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-3.5 w-3.5 text-owly-text-light" />
                    <div>
                      <p className="text-xs text-owly-text-light">
                        Resolution
                      </p>
                      <p className="text-sm font-medium text-owly-text">
                        {formatMinutes(rule.resolutionMins)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-owly-border">
                  <span
                    className={cn(
                      "text-xs font-medium",
                      rule.isActive ? "text-owly-success" : "text-owly-text-light"
                    )}
                  >
                    {rule.isActive ? "Active" : "Inactive"}
                  </span>
                  <button
                    onClick={() => handleToggleActive(rule)}
                    className={cn(
                      "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
                      rule.isActive ? "bg-owly-success" : "bg-gray-300"
                    )}
                  >
                    <span
                      className={cn(
                        "inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform",
                        rule.isActive ? "translate-x-4.5" : "translate-x-1"
                      )}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setShowModal(false)}
          />
          <div className="relative w-full max-w-md mx-4 bg-owly-surface rounded-xl shadow-xl">
            <div className="flex items-center justify-between px-5 py-4 border-b border-owly-border">
              <h3 className="font-semibold text-owly-text text-lg">
                {editingRule ? "编辑 SLA 规则" : "创建 SLA 规则"}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1.5 hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-owly-text-light" />
              </button>
            </div>

            <div className="px-5 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-owly-text mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="例如：紧急 WhatsApp SLA"
                  className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-owly-text mb-1">
                  描述
                </label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  placeholder="选填描述..."
                  className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1">
                    Channel
                  </label>
                  <select
                    value={form.channel}
                    onChange={(e) =>
                      setForm({ ...form, channel: e.target.value })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                  >
                    {channelOptions.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1">
                    优先级
                  </label>
                  <select
                    value={form.priority}
                    onChange={(e) =>
                      setForm({ ...form, priority: e.target.value })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 text-owly-text"
                  >
                    {priorityOptions.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1">
                    First Response (minutes)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={form.firstResponseMins}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        firstResponseMins: parseInt(e.target.value) || 1,
                      })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1">
                    Resolution (minutes)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={form.resolutionMins}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        resolutionMins: parseInt(e.target.value) || 1,
                      })
                    }
                    className="w-full text-sm px-3 py-2 border border-owly-border rounded-lg bg-owly-bg focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-owly-border">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm font-medium text-owly-text hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={!form.name.trim() || saving}
                className={cn(
                  "px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                  form.name.trim() && !saving
                    ? "bg-owly-primary text-white hover:bg-owly-primary-dark"
                    : "bg-owly-border text-owly-text-light cursor-not-allowed"
                )}
              >
                {saving
                  ? "正在保存..."
                  : editingRule
                  ? "Update Rule"
                  : "创建规则"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setDeleteConfirm(null)}
          />
          <div className="relative w-full max-w-sm mx-4 bg-owly-surface rounded-xl shadow-xl p-5">
            <h3 className="font-semibold text-owly-text text-lg mb-2">
              删除 SLA 规则
            </h3>
            <p className="text-sm text-owly-text-light mb-4">
              Are you sure you want to delete this SLA rule? This action cannot
              be undone.
            </p>
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-sm font-medium text-owly-text hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="px-4 py-2 text-sm font-medium bg-owly-danger text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
