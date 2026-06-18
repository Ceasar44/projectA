"use client";

import { Header } from "@/components/layout/header";
import {
  Workflow,
  Plus,
  X,
  Pencil,
  Trash2,
  Route,
  Tag,
  MessageSquareReply,
  Bell,
  Activity,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";

interface ConditionData {
  field: string;
  operator: string;
  value: string;
}

interface ActionData {
  type: string;
  value: string;
}

interface AutomationRuleData {
  id: string;
  name: string;
  description: string;
  type: string;
  isActive: boolean;
  conditions: ConditionData[];
  actions: ActionData[];
  priority: number;
  triggerCount: number;
  createdAt: string;
  updatedAt: string;
}

const ruleTypes = [
  { value: "auto_route", label: "自动分配", icon: Route, color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
  { value: "auto_tag", label: "自动打标签", icon: Tag, color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
  { value: "auto_reply", label: "自动回复", icon: MessageSquareReply, color: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" },
  { value: "keyword_alert", label: "关键词提醒", icon: Bell, color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" },
];

const conditionFields = [
  { value: "message_content", label: "消息内容" },
  { value: "channel", label: "渠道" },
  { value: "customer_name", label: "客户姓名" },
];

const conditionOperators = [
  { value: "contains", label: "包含" },
  { value: "equals", label: "等于" },
  { value: "starts_with", label: "开头是" },
];

const filterTabs = [
  { value: "all", label: "全部" },
  { value: "auto_route", label: "自动分配" },
  { value: "auto_tag", label: "自动打标签" },
  { value: "auto_reply", label: "自动回复" },
  { value: "keyword_alert", label: "关键词提醒" },
];

const defaultCondition: ConditionData = {
  field: "message_content",
  operator: "contains",
  value: "",
};

const defaultForm = {
  name: "",
  description: "",
  type: "auto_route",
  isActive: true,
  conditions: [{ ...defaultCondition }] as ConditionData[],
  actions: [{ type: "", value: "" }] as ActionData[],
  priority: 0,
};

export default function AutomationPage() {
  const [rules, setRules] = useState<AutomationRuleData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState<AutomationRuleData | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [typeFilter, setTypeFilter] = useState("all");

  const fetchRules = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (typeFilter !== "all") params.set("type", typeFilter);
      const res = await fetch(`/api/automation?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setRules(data);
      }
    } catch (error) {
      console.error("Failed to fetch automation rules:", error);
    } finally {
      setLoading(false);
    }
  }, [typeFilter]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  const getRuleType = (type: string) =>
    ruleTypes.find((t) => t.value === type) || ruleTypes[0];

  const getActionLabel = (type: string) => {
    switch (type) {
      case "auto_route": return "Route to Department";
      case "auto_tag": return "Apply Tag";
      case "auto_reply": return "Reply Message";
      case "keyword_alert": return "Notify Email";
      default: return "Action";
    }
  };

  const openCreateModal = () => {
    setEditingRule(null);
    setForm({ ...defaultForm, conditions: [{ ...defaultCondition }], actions: [{ type: "auto_route", value: "" }] });
    setShowModal(true);
  };

  const openEditModal = (rule: AutomationRuleData) => {
    setEditingRule(rule);
    setForm({
      name: rule.name,
      description: rule.description,
      type: rule.type,
      isActive: rule.isActive,
      conditions: rule.conditions.length > 0 ? [...rule.conditions] : [{ ...defaultCondition }],
      actions: rule.actions.length > 0 ? [...rule.actions] : [{ type: rule.type, value: "" }],
      priority: rule.priority,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    if (form.conditions.some((c) => !c.value.trim())) return;
    if (form.actions.some((a) => !a.value.trim())) return;

    setSaving(true);
    try {
      const payload = {
        ...form,
        actions: form.actions.map((a) => ({ type: form.type, value: a.value })),
      };

      const url = editingRule
        ? `/api/automation/${editingRule.id}`
        : "/api/automation";
      const method = editingRule ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setShowModal(false);
        fetchRules();
      }
    } catch (error) {
      console.error("Failed to save rule:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/automation/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDeleteConfirm(null);
        fetchRules();
      }
    } catch (error) {
      console.error("Failed to delete rule:", error);
    }
  };

  const handleToggleActive = async (rule: AutomationRuleData) => {
    try {
      const res = await fetch(`/api/automation/${rule.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isActive: !rule.isActive }),
      });
      if (res.ok) fetchRules();
    } catch (error) {
      console.error("Failed to toggle rule:", error);
    }
  };

  const addCondition = () => {
    setForm((f) => ({
      ...f,
      conditions: [...f.conditions, { ...defaultCondition }],
    }));
  };

  const removeCondition = (index: number) => {
    setForm((f) => ({
      ...f,
      conditions: f.conditions.filter((_, i) => i !== index),
    }));
  };

  const updateCondition = (index: number, field: keyof ConditionData, value: string) => {
    setForm((f) => ({
      ...f,
      conditions: f.conditions.map((c, i) =>
        i === index ? { ...c, [field]: value } : c
      ),
    }));
  };

  const addAction = () => {
    setForm((f) => ({
      ...f,
      actions: [...f.actions, { type: f.type, value: "" }],
    }));
  };

  const removeAction = (index: number) => {
    setForm((f) => ({
      ...f,
      actions: f.actions.filter((_, i) => i !== index),
    }));
  };

  const updateAction = (index: number, value: string) => {
    setForm((f) => ({
      ...f,
      actions: f.actions.map((a, i) =>
        i === index ? { ...a, value } : a
      ),
    }));
  };

  const renderActionInput = (action: ActionData, index: number) => {
    const commonProps = {
      className:
        "flex-1 px-3 py-2 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary transition-theme",
      value: action.value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        updateAction(index, e.target.value),
    };

    switch (form.type) {
      case "auto_route":
        return (
          <input
            {...commonProps}
            type="text"
            placeholder="部门名称，例如：销售、客服、账单"
          />
        );
      case "auto_tag":
        return (
          <input
            {...commonProps}
            type="text"
            placeholder="标签名称，例如：紧急、VIP、退款"
          />
        );
      case "auto_reply":
        return (
          <textarea
            {...commonProps}
            rows={3}
            placeholder="自动回复内容..."
          />
        );
      case "keyword_alert":
        return (
          <input
            {...commonProps}
            type="email"
            placeholder="通知邮箱地址"
          />
        );
      default:
        return <input {...commonProps} type="text" placeholder="值" />;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header
        title="自动化"
        description="设置规则来自动化客服流程"
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

      <div className="flex-1 overflow-y-auto p-6">
        {/* Filter Tabs */}
        <div className="flex gap-1 mb-6 bg-owly-surface border border-owly-border rounded-lg p-1 w-fit">
          {filterTabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setTypeFilter(tab.value)}
              className={cn(
                "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                typeFilter === tab.value
                  ? "bg-owly-primary text-white"
                  : "text-owly-text-light hover:text-owly-text hover:bg-owly-primary-50"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-owly-surface border border-owly-border rounded-xl p-5 animate-pulse"
              >
                <div className="h-5 bg-owly-border rounded w-2/3 mb-3" />
                <div className="h-4 bg-owly-border rounded w-1/3 mb-4" />
                <div className="h-4 bg-owly-border rounded w-full mb-2" />
                <div className="h-4 bg-owly-border rounded w-3/4" />
              </div>
            ))}
          </div>
        ) : rules.length === 0 ? (
          <div className="bg-owly-surface border border-owly-border rounded-xl p-12 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-owly-primary-50 mb-4">
              <Workflow className="h-8 w-8 text-owly-primary" />
            </div>
            <h3 className="text-lg font-semibold text-owly-text mb-2">
              暂无自动化规则
            </h3>
            <p className="text-owly-text-light max-w-lg mx-auto mb-6">
              自动化规则可以帮助你自动处理重复任务。
              创建规则来简化客服工作流。
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
              <div className="flex gap-3 p-4 rounded-lg bg-owly-bg border border-owly-border">
                <Route className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-owly-text">自动分配</p>
                  <p className="text-xs text-owly-text-light mt-0.5">
                    根据消息内容自动将会话分配到合适部门。
                  </p>
                </div>
              </div>
              <div className="flex gap-3 p-4 rounded-lg bg-owly-bg border border-owly-border">
                <Tag className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-owly-text">自动打标签</p>
                  <p className="text-xs text-owly-text-light mt-0.5">
                    根据关键词或条件自动为会话添加标签。
                  </p>
                </div>
              </div>
              <div className="flex gap-3 p-4 rounded-lg bg-owly-bg border border-owly-border">
                <MessageSquareReply className="h-5 w-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-owly-text">自动回复</p>
                  <p className="text-xs text-owly-text-light mt-0.5">
                    当收到的消息满足指定条件时自动发送回复。
                  </p>
                </div>
              </div>
              <div className="flex gap-3 p-4 rounded-lg bg-owly-bg border border-owly-border">
                <Bell className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-owly-text">关键词提醒</p>
                  <p className="text-xs text-owly-text-light mt-0.5">
                    当会话中出现指定关键词时，通过邮件通知你。
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={openCreateModal}
              className="mt-6 inline-flex items-center gap-2 px-4 py-2 bg-owly-primary text-white rounded-lg hover:bg-owly-primary-dark transition-colors text-sm font-medium"
            >
              <Plus className="h-4 w-4" />
              创建第一条规则
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {rules.map((rule) => {
              const ruleType = getRuleType(rule.type);
              const Icon = ruleType.icon;

              return (
                <div
                  key={rule.id}
                  className={cn(
                    "bg-owly-surface border border-owly-border rounded-xl p-5 transition-all hover:shadow-md",
                    !rule.isActive && "opacity-60"
                  )}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={cn(
                          "flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0",
                          ruleType.color
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-sm font-semibold text-owly-text truncate">
                          {rule.name}
                        </h3>
                        <span
                          className={cn(
                            "inline-block text-xs font-medium px-2 py-0.5 rounded-full mt-0.5",
                            ruleType.color
                          )}
                        >
                          {ruleType.label}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleToggleActive(rule)}
                      className={cn(
                        "relative inline-flex h-5 w-9 items-center rounded-full transition-colors flex-shrink-0",
                        rule.isActive ? "bg-owly-primary" : "bg-owly-border"
                      )}
                    >
                      <span
                        className={cn(
                          "inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform",
                          rule.isActive ? "translate-x-4.5" : "translate-x-0.5"
                        )}
                      />
                    </button>
                  </div>

                  {rule.description && (
                    <p className="text-xs text-owly-text-light mb-3 line-clamp-2">
                      {rule.description}
                    </p>
                  )}

                  <div className="flex items-center gap-3 text-xs text-owly-text-light mb-4">
                    <span className="flex items-center gap-1">
                      <Activity className="h-3.5 w-3.5" />
                      {rule.triggerCount} 次触发
                    </span>
                    <span>优先级：{rule.priority}</span>
                  </div>

                  <div className="flex items-center gap-2 pt-3 border-t border-owly-border">
                    <button
                      onClick={() => openEditModal(rule)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-owly-text-light hover:text-owly-primary hover:bg-owly-primary-50 rounded-lg transition-colors"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      编辑
                    </button>
                    {deleteConfirm === rule.id ? (
                      <div className="flex items-center gap-1.5 ml-auto">
                        <button
                          onClick={() => handleDelete(rule.id)}
                          className="px-3 py-1.5 text-xs font-medium text-white bg-owly-danger rounded-lg hover:bg-red-600 transition-colors"
                        >
                          确认
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="px-3 py-1.5 text-xs font-medium text-owly-text-light hover:text-owly-text rounded-lg transition-colors"
                        >
                          取消
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirm(rule.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-owly-text-light hover:text-owly-danger hover:bg-red-50 rounded-lg transition-colors ml-auto"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        删除
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-owly-surface border border-owly-border rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-scale-in">
            <div className="flex items-center justify-between p-5 border-b border-owly-border sticky top-0 bg-owly-surface z-10">
              <h3 className="text-lg font-semibold text-owly-text">
                {editingRule ? "编辑规则" : "创建自动化规则"}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1.5 text-owly-text-light hover:text-owly-text hover:bg-owly-primary-50 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-5 space-y-5">
              {/* Name & Description */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1.5">
                    规则名称
                  </label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, name: e.target.value }))
                    }
                    placeholder="例如：分配账单问题"
                    className="w-full px-3 py-2 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary transition-theme"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-owly-text mb-1.5">
                    优先级
                  </label>
                  <input
                    type="number"
                    value={form.priority}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        priority: parseInt(e.target.value) || 0,
                      }))
                    }
                    min={0}
                    className="w-full px-3 py-2 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary transition-theme"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-owly-text mb-1.5">
                  描述
                </label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, description: e.target.value }))
                  }
                  placeholder="简要说明这条规则的作用"
                  className="w-full px-3 py-2 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary transition-theme"
                />
              </div>

              {/* Type Selector */}
              <div>
                <label className="block text-sm font-medium text-owly-text mb-1.5">
                  规则类型
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {ruleTypes.map((rt) => (
                    <button
                      key={rt.value}
                      onClick={() =>
                        setForm((f) => ({
                          ...f,
                          type: rt.value,
                          actions: f.actions.map((a) => ({
                            ...a,
                            type: rt.value,
                          })),
                        }))
                      }
                      className={cn(
                        "flex flex-col items-center gap-1.5 p-3 rounded-lg border text-xs font-medium transition-all",
                        form.type === rt.value
                          ? "border-owly-primary bg-owly-primary-50 text-owly-primary"
                          : "border-owly-border text-owly-text-light hover:border-owly-primary/30"
                      )}
                    >
                      <rt.icon className="h-5 w-5" />
                      {rt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Conditions */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-owly-text">
                    条件
                  </label>
                  <button
                    onClick={addCondition}
                    className="text-xs text-owly-primary hover:text-owly-primary-dark font-medium transition-colors"
                  >
                    + 添加条件
                  </button>
                </div>
                <div className="space-y-2">
                  {form.conditions.map((condition, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 p-3 bg-owly-bg border border-owly-border rounded-lg"
                    >
                      <select
                        value={condition.field}
                        onChange={(e) =>
                          updateCondition(index, "field", e.target.value)
                        }
                        className="px-2.5 py-1.5 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 transition-theme"
                      >
                        {conditionFields.map((f) => (
                          <option key={f.value} value={f.value}>
                            {f.label}
                          </option>
                        ))}
                      </select>
                      <select
                        value={condition.operator}
                        onChange={(e) =>
                          updateCondition(index, "operator", e.target.value)
                        }
                        className="px-2.5 py-1.5 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 transition-theme"
                      >
                        {conditionOperators.map((o) => (
                          <option key={o.value} value={o.value}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                      <input
                        type="text"
                        value={condition.value}
                        onChange={(e) =>
                          updateCondition(index, "value", e.target.value)
                        }
                        placeholder="值..."
                        className="flex-1 px-2.5 py-1.5 text-sm border border-owly-border rounded-lg bg-owly-surface text-owly-text focus:outline-none focus:ring-2 focus:ring-owly-primary/30 transition-theme"
                      />
                      {form.conditions.length > 1 && (
                        <button
                          onClick={() => removeCondition(index)}
                          className="p-1 text-owly-text-light hover:text-owly-danger rounded transition-colors"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-owly-text">
                    {getActionLabel(form.type)}
                  </label>
                  <button
                    onClick={addAction}
                    className="text-xs text-owly-primary hover:text-owly-primary-dark font-medium transition-colors"
                  >
                    + 添加动作
                  </button>
                </div>
                <div className="space-y-2">
                  {form.actions.map((action, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-2 p-3 bg-owly-bg border border-owly-border rounded-lg"
                    >
                      {renderActionInput(action, index)}
                      {form.actions.length > 1 && (
                        <button
                          onClick={() => removeAction(index)}
                          className="p-1 mt-1 text-owly-text-light hover:text-owly-danger rounded transition-colors flex-shrink-0"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-5 border-t border-owly-border sticky bottom-0 bg-owly-surface">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm font-medium text-owly-text-light hover:text-owly-text border border-owly-border rounded-lg hover:bg-owly-bg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.name.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-owly-primary rounded-lg hover:bg-owly-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving
                  ? "正在保存..."
                  : editingRule
                    ? "更新规则"
                    : "创建规则"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
