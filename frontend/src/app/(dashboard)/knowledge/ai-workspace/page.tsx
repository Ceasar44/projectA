"use client";

import { Header } from "@/components/layout/header";
import { cn, formatDate } from "@/lib/utils";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  LogOut,
  Loader2,
  Mail,
  Plus,
  Send,
  Sparkles,
  Target,
  TrendingUp,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

type TabKey = "outreach" | "intent" | "service";

interface CustomerSummary {
  id: string;
  name: string;
  email: string;
  phone: string;
  whatsapp: string;
  tags: string;
  isBlocked: boolean;
}

interface KnowledgeEntry {
  id: string;
  title: string;
  content: string;
  isActive: boolean;
  category: {
    id: string;
    name: string;
    color: string;
  } | null;
}

interface OutreachResult {
  draftId: string;
  subject: string;
  content: string;
  channel: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

interface IntentResult {
  analysisId: string;
  result: {
    intent: string;
    customerQuality: string;
    successProbability: number;
    reasoning: string;
    replySuggestion: string;
    nextActions: string[];
    riskFlags: string[];
  };
}

interface AutoServiceConfig {
  id?: string;
  scope: "global" | "customer";
  customerId?: string | null;
  enabled: boolean;
  tone: string;
  salesFocus: boolean;
  knowledgeEntryIds: string[];
  escalationKeywords: string[];
  replyStyle: string;
}

interface ConfiguredCustomerItem {
  configId: string;
  customerId: string;
  enabled: boolean;
  tone: string;
  replyStyle: string;
  salesFocus: boolean;
  knowledgeEntryIds: string[];
  updatedAt: string | null;
  customer: {
    id: string;
    name: string;
    email: string;
    phone: string;
    whatsapp: string;
    tags: string;
  } | null;
}

const tabs: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: "outreach", label: "开发信生成", icon: Mail },
  { key: "intent", label: "客户意图识别", icon: Target },
  { key: "service", label: "AI 自动客服", icon: Bot },
];

const channelOptions = [
  { value: "email", label: "邮件" },
  { value: "whatsapp", label: "WhatsApp" },
] as const;

const outreachLanguageOptions = [
  { value: "简体中文", label: "简体中文" },
  { value: "English", label: "English" },
  { value: "Español", label: "Español" },
  { value: "Français", label: "Français" },
  { value: "Deutsch", label: "Deutsch" },
  { value: "日本語", label: "日本語" },
  { value: "العربية", label: "العربية" },
] as const;

function createDefaultCustomerConfig(customerId: string): AutoServiceConfig {
  return {
    scope: "customer",
    customerId,
    enabled: false,
    tone: "friendly",
    salesFocus: true,
    knowledgeEntryIds: [],
    escalationKeywords: ["refund", "complaint", "lawsuit", "price", "discount"],
    replyStyle: "helpful and concise",
  };
}

function SectionCard({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-xl border border-owly-border bg-owly-surface", className)}>
      <div className="border-b border-owly-border px-5 py-4">
        <h3 className="text-sm font-semibold text-owly-text">{title}</h3>
        {description ? <p className="mt-1 text-xs text-owly-text-light">{description}</p> : null}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function ToggleButton({
  checked,
  onClick,
  disabled,
  loading,
}: {
  checked: boolean;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        "inline-flex min-w-24 items-center justify-center rounded-full px-4 py-2 text-sm font-medium transition-colors",
        checked ? "bg-green-100 text-green-700" : "bg-gray-100 text-owly-text-light",
        (disabled || loading) && "cursor-not-allowed opacity-60"
      )}
    >
      {loading ? "处理中..." : checked ? "已开启" : "未开启"}
    </button>
  );
}

function KnowledgeDropdownPicker({
  entries,
  selectedIds,
  onChange,
  disabled,
  emptyText,
}: {
  entries: KnowledgeEntry[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
  emptyText?: string;
}) {
  const [pendingId, setPendingId] = useState("");

  const availableEntries = entries.filter((entry) => !selectedIds.includes(entry.id));
  const selectedEntries = selectedIds
    .map((id) => entries.find((entry) => entry.id === id))
    .filter((entry): entry is KnowledgeEntry => Boolean(entry));

  const handleAdd = () => {
    if (!pendingId) {
      return;
    }
    onChange([...selectedIds, pendingId]);
    setPendingId("");
  };

  const handleRemove = (id: string) => {
    onChange(selectedIds.filter((item) => item !== id));
  };

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-owly-border bg-owly-bg px-4 py-6 text-sm text-owly-text-light">
        {emptyText || "暂无可选的 knowledge entry。"}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <select
          value={pendingId}
          onChange={(event) => setPendingId(event.target.value)}
          disabled={disabled}
          className="w-full max-w-[280px] rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <option value="">请选择知识条目</option>
          {availableEntries.map((entry) => (
            <option key={entry.id} value={entry.id}>
              {entry.title}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAdd}
          disabled={disabled || !pendingId}
          className="inline-flex items-center gap-2 rounded-lg border border-owly-primary px-3 py-2 text-sm font-medium text-owly-primary hover:bg-owly-primary-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Plus className="h-4 w-4" />
          添加
        </button>
      </div>

      <div className="rounded-xl border border-owly-border bg-owly-bg p-3">
        {selectedEntries.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {selectedEntries.map((entry) => (
              <div
                key={entry.id}
                className="inline-flex max-w-full items-center gap-2 rounded-full bg-owly-primary-50 px-3 py-1.5 text-xs text-owly-primary"
              >
                <span className="truncate">{entry.title}</span>
                <button
                  type="button"
                  onClick={() => handleRemove(entry.id)}
                  disabled={disabled}
                  className="rounded-full p-0.5 text-owly-primary hover:bg-owly-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-owly-text-light">当前还没有选择知识条目。</p>
        )}
      </div>
    </div>
  );
}

export default function AIWorkspacePage() {
  const [activeTab, setActiveTab] = useState<TabKey>("outreach");
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [knowledgeEntries, setKnowledgeEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const [outreachCustomerId, setOutreachCustomerId] = useState("");
  const [outreachChannel, setOutreachChannel] = useState<(typeof channelOptions)[number]["value"]>("email");
  const [outreachLanguage, setOutreachLanguage] =
    useState<(typeof outreachLanguageOptions)[number]["value"]>("简体中文");
  const [outreachPurpose, setOutreachPurpose] = useState("");
  const [outreachKnowledgeIds, setOutreachKnowledgeIds] = useState<string[]>([]);
  const [outreachResult, setOutreachResult] = useState<OutreachResult | null>(null);
  const [generatingOutreach, setGeneratingOutreach] = useState(false);
  const [sendingOutreach, setSendingOutreach] = useState(false);

  const [intentCustomerId, setIntentCustomerId] = useState("");
  const [intentGoal, setIntentGoal] = useState("");
  const [intentKnowledgeIds, setIntentKnowledgeIds] = useState<string[]>([]);
  const [intentResult, setIntentResult] = useState<IntentResult | null>(null);
  const [analyzingIntent, setAnalyzingIntent] = useState(false);

  const [globalConfig, setGlobalConfig] = useState<AutoServiceConfig | null>(null);
  const [serviceCustomerId, setServiceCustomerId] = useState("");
  const [customerConfig, setCustomerConfig] = useState<AutoServiceConfig | null>(null);
  const [configuredCustomers, setConfiguredCustomers] = useState<ConfiguredCustomerItem[]>([]);
  const [savingGlobalConfig, setSavingGlobalConfig] = useState(false);
  const [savingCustomerConfig, setSavingCustomerConfig] = useState(false);

  const selectedServiceCustomer = useMemo(
    () => customers.find((customer) => customer.id === serviceCustomerId) || null,
    [customers, serviceCustomerId]
  );

  const activeCustomerCount = configuredCustomers.filter((item) => item.enabled).length;
  const isGlobalEnabled = Boolean(globalConfig?.enabled);

  const fetchBaseData = useCallback(async () => {
    setLoading(true);
    try {
      const [customersRes, entriesRes, settingsRes, configuredRes] = await Promise.all([
        fetch("/api/customers?limit=100", { cache: "no-store" }),
        fetch("/api/knowledge/entries?limit=100", { cache: "no-store" }),
        fetch("/api/knowledge/ai/customer-service/settings", { cache: "no-store" }),
        fetch("/api/knowledge/ai/customer-service/customers", { cache: "no-store" }),
      ]);

      if (customersRes.ok) {
        const customersJson = await customersRes.json();
        setCustomers(customersJson.data || []);
      }

      if (entriesRes.ok) {
        const entriesJson = await entriesRes.json();
        setKnowledgeEntries((entriesJson.data || []).filter((entry: KnowledgeEntry) => entry.isActive));
      }

      if (settingsRes.ok) {
        const settingsJson = await settingsRes.json();
        setGlobalConfig(
          settingsJson.global || {
            scope: "global",
            enabled: false,
            tone: "friendly",
            salesFocus: true,
            knowledgeEntryIds: [],
            escalationKeywords: ["refund", "complaint", "lawsuit", "price", "discount"],
            replyStyle: "helpful and concise",
          }
        );
      }

      if (configuredRes.ok) {
        const configuredJson = await configuredRes.json();
        setConfiguredCustomers(configuredJson.data || []);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchCustomerConfig = useCallback(async (customerId: string) => {
    if (!customerId) {
      setCustomerConfig(null);
      return;
    }

    const res = await fetch(`/api/knowledge/ai/customer-service/settings?customerId=${customerId}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      setCustomerConfig(createDefaultCustomerConfig(customerId));
      return;
    }

    const json = await res.json();
    setCustomerConfig(
      json.customer && Object.keys(json.customer).length > 0
        ? json.customer
        : createDefaultCustomerConfig(customerId)
    );
  }, []);

  useEffect(() => {
    fetchBaseData();
  }, [fetchBaseData]);

  useEffect(() => {
    fetchCustomerConfig(serviceCustomerId);
  }, [fetchCustomerConfig, serviceCustomerId]);

  const saveConfig = async (
    config: AutoServiceConfig,
    target: "global" | "customer",
    successMessage: string,
    refreshAfterSave = true
  ): Promise<AutoServiceConfig | null> => {
    if (target === "global") {
      setSavingGlobalConfig(true);
    } else {
      setSavingCustomerConfig(true);
    }

    setFeedback(null);

    try {
      const res = await fetch("/api/knowledge/ai/customer-service/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      const json = await res.json();

      if (!res.ok || json.error) {
        setFeedback({ type: "error", message: json.error || "保存配置失败。" });
        return null;
      }

      const nextConfig = json as AutoServiceConfig;
      if (target === "global") {
        setGlobalConfig(nextConfig);
      } else {
        setCustomerConfig(nextConfig);
      }

      setFeedback({ type: "success", message: successMessage });
      if (refreshAfterSave) {
        await fetchBaseData();
        if (config.customerId) {
          await fetchCustomerConfig(String(config.customerId));
        }
      }
      return nextConfig;
    } finally {
      if (target === "global") {
        setSavingGlobalConfig(false);
      } else {
        setSavingCustomerConfig(false);
      }
    }
  };

  const handleGenerateOutreach = async () => {
    if (!outreachCustomerId) {
      return;
    }

    setGeneratingOutreach(true);
    setFeedback(null);

    try {
      const res = await fetch("/api/knowledge/ai/outreach/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customerId: outreachCustomerId,
          knowledgeEntryIds: outreachKnowledgeIds,
          channel: outreachChannel,
          language: outreachLanguage,
          purpose: outreachPurpose,
          autoDeliveryEnabled: false,
        }),
      });
      const json = await res.json();

      if (!res.ok) {
        setFeedback({ type: "error", message: json.error || "开发信生成失败。" });
        return;
      }

      setOutreachResult({
        draftId: json.draftId,
        subject: json.subject || "",
        content: json.content || "",
        channel: json.channel || outreachChannel,
        usage: json.usage,
      });
      setFeedback({ type: "success", message: "开发信已生成，可在右侧编辑后再手动投递。" });
    } finally {
      setGeneratingOutreach(false);
    }
  };

  const handleSendOutreach = async () => {
    if (!outreachResult) {
      return;
    }

    setSendingOutreach(true);
    setFeedback(null);

    try {
      const res = await fetch("/api/knowledge/ai/outreach/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          draftId: outreachResult.draftId,
          subject: outreachResult.subject,
          content: outreachResult.content,
          channel: outreachChannel,
          autoDeliveryEnabled: false,
        }),
      });
      const json = await res.json();

      if (!res.ok) {
        setFeedback({ type: "error", message: json.error || "投递失败。" });
        return;
      }

      setFeedback({
        type: "success",
        message: `已手动投递，状态：${json.status}${json.errorMessage ? `，原因：${json.errorMessage}` : ""}`,
      });
    } finally {
      setSendingOutreach(false);
    }
  };

  const handleAnalyzeIntent = async () => {
    if (!intentCustomerId || !intentGoal.trim()) {
      return;
    }

    setAnalyzingIntent(true);
    setFeedback(null);

    try {
      const res = await fetch("/api/knowledge/ai/intent/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customerId: intentCustomerId,
          communicationGoal: intentGoal,
          knowledgeEntryIds: intentKnowledgeIds,
        }),
      });
      const json = await res.json();

      if (!res.ok) {
        setFeedback({ type: "error", message: json.error || "意图分析失败。" });
        return;
      }

      setIntentResult(json);
    } finally {
      setAnalyzingIntent(false);
    }
  };

  const handleToggleGlobal = async () => {
    if (!globalConfig) {
      return;
    }

    if (globalConfig.enabled) {
      setGlobalConfig((prev) => (prev ? { ...prev, enabled: false } : prev));
      await saveConfig(
        { ...globalConfig, scope: "global", enabled: false },
        "global",
        "全局 AI 自动客服已关闭。"
      );
      return;
    }

    if (activeCustomerCount > 0) {
      setFeedback({
        type: "error",
        message: "当前已有单客户 AI 自动客服处于开启状态，请先关闭单客户开关后再开启全局开关。",
      });
      return;
    }

    setGlobalConfig((prev) => (prev ? { ...prev, enabled: true } : prev));
    await saveConfig(
      { ...globalConfig, scope: "global", enabled: true },
      "global",
      "全局 AI 自动客服已开启。"
    );
  };

  const handleAddCustomerConfig = async () => {
    if (!serviceCustomerId || !customerConfig) {
      return;
    }

    const matchedCustomer = customers.find((item) => item.id === serviceCustomerId) || null;
    const previousCustomers = configuredCustomers;
    const optimisticItem: ConfiguredCustomerItem = {
      configId: `temp-${serviceCustomerId}`,
      customerId: serviceCustomerId,
      enabled: true,
      tone: customerConfig.tone,
      replyStyle: customerConfig.replyStyle,
      salesFocus: customerConfig.salesFocus,
      knowledgeEntryIds: customerConfig.knowledgeEntryIds,
      updatedAt: new Date().toISOString(),
      customer: matchedCustomer
        ? {
            id: matchedCustomer.id,
            name: matchedCustomer.name,
            email: matchedCustomer.email,
            phone: matchedCustomer.phone,
            whatsapp: matchedCustomer.whatsapp,
            tags: matchedCustomer.tags,
          }
        : null,
    };

    setConfiguredCustomers((prev) => {
      const exists = prev.some((item) => item.customerId === serviceCustomerId);
      if (exists) {
        return prev.map((item) => (item.customerId === serviceCustomerId ? optimisticItem : item));
      }
      return [optimisticItem, ...prev];
    });

    const saved = await saveConfig(
      {
        ...customerConfig,
        scope: "customer",
        customerId: serviceCustomerId,
        enabled: true,
      },
      "customer",
      "单客户 AI 自动客服配置已加入列表。",
      false
    );

    if (!saved) {
      setConfiguredCustomers(previousCustomers);
      return;
    }

    setConfiguredCustomers((prev) =>
      prev.map((item) =>
        item.customerId === serviceCustomerId
          ? {
              ...item,
              configId: saved.id || item.configId,
              enabled: true,
              tone: saved.tone,
              replyStyle: saved.replyStyle,
              salesFocus: saved.salesFocus,
              knowledgeEntryIds: saved.knowledgeEntryIds,
              updatedAt: new Date().toISOString(),
            }
          : item
      )
    );
  };

  const handleRemoveConfiguredCustomer = async (item: ConfiguredCustomerItem) => {
    if (isGlobalEnabled) {
      setFeedback({ type: "error", message: "全局 AI 自动客服已开启时，单客户配置不可编辑。" });
      return;
    }

    const previousCustomers = configuredCustomers;
    setConfiguredCustomers((prev) => prev.filter((config) => config.customerId !== item.customerId));

    const saved = await saveConfig(
      {
        scope: "customer",
        customerId: item.customerId,
        enabled: false,
        tone: item.tone,
        salesFocus: item.salesFocus,
        knowledgeEntryIds: item.knowledgeEntryIds,
        escalationKeywords: ["refund", "complaint", "lawsuit", "price", "discount"],
        replyStyle: item.replyStyle,
      },
      "customer",
      "单客户 AI 自动客服已移除。",
      false
    );

    if (!saved) {
      setConfiguredCustomers(previousCustomers);
      return;
    }
  };

  if (loading) {
    return (
      <>
        <Header title="AI 工作台" description="AI 工作页加载中..." />
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-owly-primary" />
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="AI 工作台"
        description="统一管理开发信生成、客户意图识别与 AI 自动客服。"
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-[1440px] space-y-6">
          {feedback ? (
            <div
              className={cn(
                "flex items-start gap-3 rounded-xl border px-4 py-3 text-sm",
                feedback.type === "success"
                  ? "border-green-200 bg-green-50 text-green-700"
                  : "border-red-200 bg-red-50 text-red-700"
              )}
            >
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{feedback.message}</span>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2 rounded-xl border border-owly-border bg-owly-surface p-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key)}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                    activeTab === tab.key
                      ? "bg-owly-primary text-white"
                      : "text-owly-text-light hover:bg-owly-primary-50 hover:text-owly-text"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {activeTab === "outreach" ? (
            <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
              <SectionCard
                title="开发信配置"
                description="引用知识条目已改为下拉选择，可逐个添加。"
              >
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-owly-text-light">客户</label>
                    <select
                      value={outreachCustomerId}
                      onChange={(event) => setOutreachCustomerId(event.target.value)}
                      className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                    >
                      <option value="">请选择客户</option>
                      {customers.map((customer) => (
                        <option key={customer.id} value={customer.id}>
                          {customer.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-xs font-medium text-owly-text-light">发送渠道</label>
                    <div className="grid grid-cols-2 gap-2">
                      {channelOptions.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => setOutreachChannel(option.value)}
                          className={cn(
                            "rounded-lg border px-3 py-2 text-sm transition-colors",
                            outreachChannel === option.value
                              ? "border-owly-primary bg-owly-primary-50 text-owly-primary"
                              : "border-owly-border text-owly-text-light hover:border-owly-primary/30"
                          )}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-owly-text-light">使用语言</label>
                    <select
                      value={outreachLanguage}
                      onChange={(event) =>
                        setOutreachLanguage(
                          event.target.value as (typeof outreachLanguageOptions)[number]["value"]
                        )
                      }
                      className="w-full max-w-[280px] rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                    >
                      {outreachLanguageOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-owly-text-light">
                      开发信目的（可选）
                    </label>
                    <textarea
                      value={outreachPurpose}
                      onChange={(event) => setOutreachPurpose(event.target.value)}
                      rows={4}
                      placeholder="例如：介绍新品、争取报价机会、推进样品寄送或安排下一步沟通。"
                      className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-xs font-medium text-owly-text-light">
                      引用 Knowledge Entry
                    </label>
                    <KnowledgeDropdownPicker
                      entries={knowledgeEntries}
                      selectedIds={outreachKnowledgeIds}
                      onChange={setOutreachKnowledgeIds}
                      emptyText="请先在 Knowledge Base 中创建并启用 knowledge entry。"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleGenerateOutreach}
                    disabled={!outreachCustomerId || generatingOutreach}
                    className="inline-flex items-center gap-2 rounded-lg bg-owly-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-owly-primary-dark disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {generatingOutreach ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                    生成开发信
                  </button>
                </div>
              </SectionCard>

              <SectionCard title="开发信结果" description="生成结果在右侧，可编辑后再手动投递。">
                {!outreachResult ? (
                  <div className="flex min-h-96 flex-col items-center justify-center rounded-xl border border-dashed border-owly-border bg-owly-bg text-center">
                    <Mail className="mb-3 h-10 w-10 text-owly-text-light/40" />
                    <p className="text-sm font-medium text-owly-text">还没有生成开发信</p>
                    <p className="mt-1 text-xs text-owly-text-light">左侧配置完成后点击生成。</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="rounded-xl bg-owly-bg p-4">
                      <p className="text-xs text-owly-text-light">预计消耗 Token</p>
                      <p className="mt-1 text-lg font-semibold text-owly-text">
                        {(outreachResult.usage?.totalTokens || 0).toLocaleString()}
                      </p>
                    </div>

                    <div>
                      <label className="mb-1 block text-xs font-medium text-owly-text-light">邮件主题</label>
                      <input
                        value={outreachResult.subject}
                        onChange={(event) =>
                          setOutreachResult((prev) =>
                            prev ? { ...prev, subject: event.target.value } : prev
                          )
                        }
                        className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-xs font-medium text-owly-text-light">开发信内容</label>
                      <textarea
                        value={outreachResult.content}
                        onChange={(event) =>
                          setOutreachResult((prev) =>
                            prev ? { ...prev, content: event.target.value } : prev
                          )
                        }
                        rows={16}
                        className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                      />
                    </div>

                    <button
                      type="button"
                      onClick={handleSendOutreach}
                      disabled={sendingOutreach || !outreachResult.content.trim()}
                      className="inline-flex items-center gap-2 rounded-lg bg-owly-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-owly-primary-dark disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {sendingOutreach ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                      手动投递
                    </button>
                  </div>
                )}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "intent" ? (
            <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
              <SectionCard
                title="分析输入"
                description="附加知识条目已改为下拉选择，可逐个添加。"
              >
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-owly-text-light">客户</label>
                    <select
                      value={intentCustomerId}
                      onChange={(event) => setIntentCustomerId(event.target.value)}
                      className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                    >
                      <option value="">请选择客户</option>
                      {customers.map((customer) => (
                        <option key={customer.id} value={customer.id}>
                          {customer.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-owly-text-light">本次沟通目的</label>
                    <textarea
                      value={intentGoal}
                      onChange={(event) => setIntentGoal(event.target.value)}
                      rows={5}
                      placeholder="例如：希望推动客户进一步了解产品，并争取报价或演示机会。"
                      className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-xs font-medium text-owly-text-light">
                      附加 Knowledge Entry
                    </label>
                    <KnowledgeDropdownPicker
                      entries={knowledgeEntries}
                      selectedIds={intentKnowledgeIds}
                      onChange={setIntentKnowledgeIds}
                      emptyText="请先在 Knowledge Base 中创建并启用 knowledge entry。"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleAnalyzeIntent}
                    disabled={!intentCustomerId || !intentGoal.trim() || analyzingIntent}
                    className="inline-flex items-center gap-2 rounded-lg bg-owly-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-owly-primary-dark disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {analyzingIntent ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                    AI 分析
                  </button>
                </div>
              </SectionCard>

              <SectionCard title="分析结果" description="输出客户意图、客户质量、成功概率和执行建议。">
                {!intentResult ? (
                  <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-owly-border bg-owly-bg text-center">
                    <Target className="mb-3 h-10 w-10 text-owly-text-light/40" />
                    <p className="text-sm font-medium text-owly-text">还没有分析结果</p>
                    <p className="mt-1 text-xs text-owly-text-light">填写目标后点击 “AI 分析”。</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="rounded-xl bg-owly-bg p-4">
                        <p className="text-xs text-owly-text-light">客户意图</p>
                        <p className="mt-1 text-base font-semibold text-owly-text">{intentResult.result.intent}</p>
                      </div>
                      <div className="rounded-xl bg-owly-bg p-4">
                        <p className="text-xs text-owly-text-light">客户质量</p>
                        <p className="mt-1 text-base font-semibold text-owly-text">
                          {intentResult.result.customerQuality}
                        </p>
                      </div>
                      <div className="rounded-xl bg-owly-bg p-4">
                        <p className="text-xs text-owly-text-light">成功概率</p>
                        <p className="mt-1 flex items-center gap-2 text-base font-semibold text-owly-text">
                          <TrendingUp className="h-4 w-4 text-owly-primary" />
                          {Math.round((intentResult.result.successProbability || 0) * 100)}%
                        </p>
                      </div>
                    </div>

                    <div className="rounded-xl border border-owly-border bg-owly-bg p-4">
                      <p className="text-xs font-medium text-owly-text-light">分析依据</p>
                      <p className="mt-2 whitespace-pre-wrap text-sm text-owly-text">
                        {intentResult.result.reasoning}
                      </p>
                    </div>

                    <div className="rounded-xl border border-owly-border bg-owly-bg p-4">
                      <p className="text-xs font-medium text-owly-text-light">建议回复</p>
                      <p className="mt-2 whitespace-pre-wrap text-sm text-owly-text">
                        {intentResult.result.replySuggestion}
                      </p>
                    </div>

                    <div className="grid gap-4 lg:grid-cols-2">
                      <div className="rounded-xl border border-owly-border bg-owly-bg p-4">
                        <p className="text-xs font-medium text-owly-text-light">后续动作</p>
                        <div className="mt-3 space-y-2">
                          {(intentResult.result.nextActions || []).map((action, index) => (
                            <div key={`${action}-${index}`} className="flex items-start gap-2">
                              <CheckCircle2 className="mt-0.5 h-4 w-4 text-owly-primary" />
                              <p className="text-sm text-owly-text">{action}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-xl border border-owly-border bg-owly-bg p-4">
                        <p className="text-xs font-medium text-owly-text-light">风险提示</p>
                        <div className="mt-3 space-y-2">
                          {(intentResult.result.riskFlags || []).length > 0 ? (
                            intentResult.result.riskFlags.map((flag, index) => (
                              <div
                                key={`${flag}-${index}`}
                                className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
                              >
                                {flag}
                              </div>
                            ))
                          ) : (
                            <div className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">
                              当前未识别到高风险阻塞项。
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "service" && globalConfig ? (
            <div className="space-y-6">
              <div className="grid gap-6 xl:grid-cols-2">
                <SectionCard
                  title="全局 AI 自动客服"
                  description="开启后，单客户配置区无法编辑。"
                >
                  <div className="space-y-4">
                    <div className="flex items-center justify-between rounded-xl bg-owly-bg p-4">
                      <div>
                        <p className="text-sm font-medium text-owly-text">全局开关</p>
                        <p className="mt-1 text-xs text-owly-text-light">
                          当前已启用单客户策略 {activeCustomerCount} 个；如需开启全局，请先移除所有单客户ai自动客服策略。
                        </p>
                      </div>
                      <ToggleButton
                        checked={globalConfig.enabled}
                        onClick={handleToggleGlobal}
                        loading={savingGlobalConfig}
                      />
                    </div>

                    <fieldset
                      disabled={!isGlobalEnabled}
                      className={cn(
                        "space-y-4",
                        !isGlobalEnabled && "cursor-not-allowed opacity-50"
                      )}
                    >
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <label className="mb-1 block text-xs font-medium text-owly-text-light">回复语气</label>
                          <input
                            value={globalConfig.tone}
                            onChange={(event) => setGlobalConfig({ ...globalConfig, tone: event.target.value })}
                            className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                          />
                        </div>

                        <div>
                          <label className="mb-1 block text-xs font-medium text-owly-text-light">回复风格</label>
                          <input
                            value={globalConfig.replyStyle}
                            onChange={(event) =>
                              setGlobalConfig({ ...globalConfig, replyStyle: event.target.value })
                            }
                            className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="mb-2 block text-xs font-medium text-owly-text-light">
                          全局 Knowledge Entry
                        </label>
                        <KnowledgeDropdownPicker
                          entries={knowledgeEntries}
                          selectedIds={globalConfig.knowledgeEntryIds}
                          onChange={(ids) =>
                            setGlobalConfig((prev) => (prev ? { ...prev, knowledgeEntryIds: ids } : prev))
                          }
                          disabled={!isGlobalEnabled}
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          saveConfig(
                            { ...globalConfig, scope: "global" },
                            "global",
                            "全局 AI 自动客服配置已保存。"
                          )
                        }
                        disabled={savingGlobalConfig || !isGlobalEnabled}
                        className="inline-flex items-center gap-2 rounded-lg bg-owly-primary px-4 py-2 text-sm font-medium text-white hover:bg-owly-primary-dark disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {savingGlobalConfig ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4" />
                        )}
                        保存全局配置
                      </button>
                    </fieldset>
                  </div>
                </SectionCard>

                <SectionCard
                  title="单客户 AI 自动客服"
                  description="全局策略开启后，无法选择客户、修改配置或添加。"
                  className={isGlobalEnabled ? "opacity-50" : undefined}
                >
                  <fieldset disabled={isGlobalEnabled} className="space-y-4 disabled:cursor-not-allowed">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-owly-text-light">选择客户</label>
                      <select
                        value={serviceCustomerId}
                        onChange={(event) => setServiceCustomerId(event.target.value)}
                        className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        <option value="">请选择客户</option>
                        {customers.map((customer) => (
                          <option key={customer.id} value={customer.id}>
                            {customer.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {isGlobalEnabled ? (
                      <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
                        全局 AI 自动客服已开启，单客户配置已锁定。
                      </div>
                    ) : null}

                    {serviceCustomerId && customerConfig ? (
                      <>
                        <div className="rounded-xl bg-owly-bg p-4">
                          <p className="text-sm font-medium text-owly-text">
                            {selectedServiceCustomer?.name || "当前客户"}
                          </p>
                          <p className="mt-1 text-xs text-owly-text-light">
                            配置完成后点击“添加”，该客户会进入已使用 AI 自动客服的客户列表。
                          </p>
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <label className="mb-1 block text-xs font-medium text-owly-text-light">回复语气</label>
                            <input
                              value={customerConfig.tone}
                              onChange={(event) =>
                                setCustomerConfig({ ...customerConfig, tone: event.target.value })
                              }
                              className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                            />
                          </div>

                          <div>
                            <label className="mb-1 block text-xs font-medium text-owly-text-light">回复风格</label>
                            <input
                              value={customerConfig.replyStyle}
                              onChange={(event) =>
                                setCustomerConfig({ ...customerConfig, replyStyle: event.target.value })
                              }
                              className="w-full rounded-lg border border-owly-border bg-owly-bg px-3 py-2 text-sm outline-none focus:border-owly-primary focus:ring-2 focus:ring-owly-primary/20"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="mb-2 block text-xs font-medium text-owly-text-light">
                            客户专属 Knowledge Entry
                          </label>
                          <KnowledgeDropdownPicker
                            entries={knowledgeEntries}
                            selectedIds={customerConfig.knowledgeEntryIds}
                            onChange={(ids) => setCustomerConfig({ ...customerConfig, knowledgeEntryIds: ids })}
                          />
                        </div>

                        <button
                          type="button"
                          onClick={handleAddCustomerConfig}
                          disabled={savingCustomerConfig}
                          className="inline-flex items-center gap-2 rounded-lg border border-owly-primary px-4 py-2 text-sm font-medium text-owly-primary hover:bg-owly-primary-50 disabled:opacity-60"
                        >
                          {savingCustomerConfig ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Plus className="h-4 w-4" />
                          )}
                          添加
                        </button>
                      </>
                    ) : null}
                  </fieldset>
                </SectionCard>
              </div>

              <SectionCard title="使用 AI 自动客服的客户列表" description="这里展示已添加的单客户配置。">
                <div className={cn("overflow-hidden rounded-xl border border-owly-border", isGlobalEnabled && "opacity-50")}>
                  <div className="grid grid-cols-[1.2fr_120px_1fr_160px] gap-4 bg-owly-bg px-4 py-3 text-xs font-semibold uppercase tracking-wide text-owly-text-light">
                    <span>客户</span>
                    <span>状态</span>
                    <span>策略</span>
                    <span>更新时间</span>
                  </div>

                  <div className="divide-y divide-owly-border bg-owly-surface">
                    {configuredCustomers.length > 0 ? (
                      configuredCustomers.map((item) => (
                        <div
                          key={item.configId}
                          className="grid grid-cols-[1.2fr_120px_1fr_160px] items-center gap-4 px-4 py-4 text-sm"
                        >
                          <div>
                            <p className="font-medium text-owly-text">{item.customer?.name || item.customerId}</p>
                            <p className="mt-1 text-xs text-owly-text-light">
                              {item.customer?.email || item.customer?.whatsapp || item.customer?.phone || "--"}
                            </p>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleRemoveConfiguredCustomer(item)}
                            disabled={isGlobalEnabled}
                            className="inline-flex w-fit items-center gap-2 rounded-lg border border-red-200 px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            <LogOut className="h-3.5 w-3.5" />
                            移除
                          </button>

                          <div className="text-owly-text-light">
                            <p>{item.tone}</p>
                            <p className="mt-1 text-xs">{item.replyStyle}</p>
                          </div>

                          <div className="text-xs text-owly-text-light">
                            {item.updatedAt ? formatDate(item.updatedAt) : "--"}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="flex items-center justify-center px-6 py-12 text-sm text-owly-text-light">
                        还没有添加任何单客户 AI 自动客服配置。
                      </div>
                    )}
                  </div>
                </div>
              </SectionCard>
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
