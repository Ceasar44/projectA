"use client";

import { Header } from "@/components/layout/header";
import { cn } from "@/lib/utils";
import {
  Settings as SettingsIcon,
  Bot,
  Mic,
  Phone,
  Mail,
  MessageCircle,
  Save,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { useEffect, useState, useCallback } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SettingsData {
  businessName: string;
  businessDesc: string;
  welcomeMessage: string;
  tone: string;
  language: string;
  aiProvider: string;
  aiModel: string;
  aiApiKey: string;
  maxTokens: number;
  temperature: number;
  elevenLabsKey: string;
  elevenLabsVoice: string;
  twilioSid: string;
  twilioToken: string;
  twilioPhone: string;
  smtpHost: string;
  smtpPort: number;
  smtpUser: string;
  smtpPass: string;
  smtpFrom: string;
  imapHost: string;
  imapPort: number;
  imapUser: string;
  imapPass: string;
  whatsappMode: string;
  whatsappApiKey: string;
  whatsappPhone: string;
}

type SectionKey =
  | "general"
  | "ai"
  | "voice"
  | "phone"
  | "email"
  | "whatsapp";

interface TabDef {
  key: SectionKey;
  label: string;
  icon: React.ElementType;
}

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

const tabs: TabDef[] = [
  { key: "general", label: "通用", icon: SettingsIcon },
  { key: "ai", label: "AI 配置", icon: Bot },
  { key: "voice", label: "语音 (ElevenLabs)", icon: Mic },
  { key: "phone", label: "电话 (Twilio)", icon: Phone },
  { key: "email", label: "邮箱 (SMTP/IMAP)", icon: Mail },
  { key: "whatsapp", label: "WhatsApp", icon: MessageCircle },
];

// Which fields belong to each section (used for partial saves)
const sectionFields: Record<SectionKey, (keyof SettingsData)[]> = {
  general: ["businessName", "businessDesc", "welcomeMessage", "tone", "language"],
  ai: ["aiProvider", "aiModel", "aiApiKey", "maxTokens", "temperature"],
  voice: ["elevenLabsKey", "elevenLabsVoice"],
  phone: ["twilioSid", "twilioToken", "twilioPhone"],
  email: [
    "smtpHost",
    "smtpPort",
    "smtpUser",
    "smtpPass",
    "smtpFrom",
    "imapHost",
    "imapPort",
    "imapUser",
    "imapPass",
  ],
  whatsapp: ["whatsappMode", "whatsappApiKey", "whatsappPhone"],
};

// ---------------------------------------------------------------------------
// Toast component
// ---------------------------------------------------------------------------

interface Toast {
  id: number;
  type: "success" | "error";
  message: string;
}

function ToastContainer({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all animate-in slide-in-from-right",
            t.type === "success"
              ? "bg-owly-success text-white"
              : "bg-owly-danger text-white"
          )}
        >
          {t.type === "success" ? (
            <CheckCircle className="h-4 w-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
          )}
          {t.message}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reusable form components
// ---------------------------------------------------------------------------

function FormField({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-owly-text">
        {label}
      </label>
      {description && (
        <p className="text-xs text-owly-text-light">{description}</p>
      )}
      {children}
    </div>
  );
}

const inputClasses =
  "w-full px-3 py-2 text-sm border border-owly-border rounded-lg bg-owly-bg text-owly-text placeholder:text-owly-text-light/60 focus:outline-none focus:ring-2 focus:ring-owly-primary/30 focus:border-owly-primary transition-colors";

function TextInput({
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={inputClasses}
    />
  );
}

function NumberInput({
  value,
  onChange,
  min,
  max,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <input
      type="number"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      min={min}
      max={max}
      className={inputClasses}
    />
  );
}

function TextareaInput({
  value,
  onChange,
  placeholder,
  rows = 3,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className={cn(inputClasses, "resize-none")}
    />
  );
}

function SelectInput({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={inputClasses}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

function PasswordInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative">
      <input
        type={visible ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={cn(inputClasses, "pr-10")}
      />
      <button
        type="button"
        onClick={() => setVisible(!visible)}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-owly-text-light hover:text-owly-text rounded transition-colors"
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}

function SliderInput({
  value,
  onChange,
  min,
  max,
  step,
  displayValue,
}: {
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  displayValue?: string;
}) {
  return (
    <div className="flex items-center gap-4">
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="flex-1 h-2 rounded-full appearance-none bg-owly-border accent-owly-primary cursor-pointer"
      />
      <span className="text-sm font-medium text-owly-text w-16 text-right">
        {displayValue ?? value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section save button
// ---------------------------------------------------------------------------

function SaveButton({
  onClick,
  saving,
}: {
  onClick: () => void;
  saving: boolean;
}) {
  return (
    <div className="flex justify-end pt-4 border-t border-owly-border">
      <button
        onClick={onClick}
        disabled={saving}
        className={cn(
          "flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors",
          saving
            ? "bg-owly-primary/60 text-white cursor-not-allowed"
            : "bg-owly-primary hover:bg-owly-primary-dark text-white"
        )}
      >
        {saving ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Save className="h-4 w-4" />
        )}
        {saving ? "正在保存..." : "保存"}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section renderers
// ---------------------------------------------------------------------------

function GeneralSection({
  data,
  update,
}: {
  data: SettingsData;
  update: (field: keyof SettingsData, value: string | number) => void;
}) {
  return (
    <div className="space-y-5">
      <FormField label="业务名称" description="你的业务或组织名称。">
        <TextInput
          value={data.businessName}
          onChange={(v) => update("businessName", v)}
          placeholder="我的业务"
        />
      </FormField>
      <FormField label="业务描述" description="用于 AI 互动上下文的简短说明。">
        <TextareaInput
          value={data.businessDesc}
          onChange={(v) => update("businessDesc", v)}
          placeholder="描述你的业务内容..."
        />
      </FormField>
      <FormField label="欢迎语" description="发送给新客户的问候语。">
        <TextareaInput
          value={data.welcomeMessage}
          onChange={(v) => update("welcomeMessage", v)}
          placeholder="您好！今天有什么可以帮您？"
        />
      </FormField>
      <FormField label="语气" description="选择 AI 回复的沟通风格。">
        <SelectInput
          value={data.tone}
          onChange={(v) => update("tone", v)}
          options={[
            { value: "friendly", label: "友好" },
            { value: "professional", label: "专业" },
            { value: "formal", label: "正式" },
            { value: "technical", label: "技术型" },
          ]}
        />
      </FormField>
      <FormField label="语言" description="AI 回复的主要语言。自动检测会根据客户语言判断。">
        <SelectInput
          value={data.language}
          onChange={(v) => update("language", v)}
          options={[
            { value: "auto", label: "自动检测" },
            { value: "en", label: "英语" },
            { value: "tr", label: "土耳其语" },
            { value: "de", label: "德语" },
            { value: "fr", label: "法语" },
            { value: "es", label: "西班牙语" },
            { value: "pt", label: "葡萄牙语" },
            { value: "ar", label: "阿拉伯语" },
            { value: "zh", label: "中文" },
            { value: "ja", label: "日语" },
          ]}
        />
      </FormField>
    </div>
  );
}

function AISection({
  data,
  update,
}: {
  data: SettingsData;
  update: (field: keyof SettingsData, value: string | number) => void;
}) {
  const modelOptions: Record<string, { value: string; label: string }[]> = {
    openai: [
      { value: "gpt-4o", label: "GPT-4o" },
      { value: "gpt-4o-mini", label: "GPT-4o Mini" },
      { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
    ],
    claude: [
      { value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4" },
      { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
      { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
    ],
    ollama: [
      { value: "llama3", label: "Llama 3" },
      { value: "mistral", label: "Mistral" },
      { value: "codellama", label: "Code Llama" },
    ],
  };

  return (
    <div className="space-y-5">
      <FormField label="AI 服务商" description="选择用于生成回复的 AI 服务商。">
        <SelectInput
          value={data.aiProvider}
          onChange={(v) => {
            update("aiProvider", v);
            const models = modelOptions[v];
            if (models && models.length > 0) {
              update("aiModel", models[0].value);
            }
          }}
          options={[
            { value: "openai", label: "OpenAI" },
            { value: "claude", label: "Claude (Anthropic)" },
            { value: "ollama", label: "Ollama (本地)" },
          ]}
        />
      </FormField>
      <FormField label="模型" description="用于 AI 回复的具体模型。">
        <SelectInput
          value={data.aiModel}
          onChange={(v) => update("aiModel", v)}
          options={modelOptions[data.aiProvider] || []}
        />
      </FormField>
      <FormField label="API Key" description="你的服务商 API Key。Ollama 不需要。">
        <PasswordInput
          value={data.aiApiKey}
          onChange={(v) => update("aiApiKey", v)}
          placeholder={
            data.aiProvider === "ollama"
              ? "本地模型不需要"
              : "请输入 API Key"
          }
        />
      </FormField>
      <FormField label="最大 Token 数" description="每次 AI 回复可使用的最大 token 数。">
        <SliderInput
          value={data.maxTokens}
          onChange={(v) => update("maxTokens", v)}
          min={256}
          max={8192}
          step={256}
          displayValue={data.maxTokens.toLocaleString()}
        />
      </FormField>
      <FormField label="Temperature" description="控制随机性。数值越低回复越聚焦，越高则更有创造性。">
        <SliderInput
          value={data.temperature}
          onChange={(v) => update("temperature", v)}
          min={0}
          max={2}
          step={0.1}
          displayValue={data.temperature.toFixed(1)}
        />
      </FormField>
    </div>
  );
}

function VoiceSection({
  data,
  update,
}: {
  data: SettingsData;
  update: (field: keyof SettingsData, value: string | number) => void;
}) {
  return (
    <div className="space-y-5">
      <div className="p-4 rounded-lg bg-owly-primary-50/50 border border-owly-primary/20">
        <p className="text-sm text-owly-text">
          连接 ElevenLabs 账户，为电话通话启用 AI 语音回复。
        </p>
      </div>
      <FormField label="API Key" description="用于文字转语音的 ElevenLabs API Key。">
        <PasswordInput
          value={data.elevenLabsKey}
          onChange={(v) => update("elevenLabsKey", v)}
          placeholder="请输入 ElevenLabs API Key"
        />
      </FormField>
      <FormField label="Voice ID" description="用于语音合成的 ElevenLabs 声音 ID。">
        <TextInput
          value={data.elevenLabsVoice}
          onChange={(v) => update("elevenLabsVoice", v)}
          placeholder="e.g. 21m00Tcm4TlvDq8ikWAM"
        />
      </FormField>
    </div>
  );
}

function PhoneSection({
  data,
  update,
}: {
  data: SettingsData;
  update: (field: keyof SettingsData, value: string | number) => void;
}) {
  return (
    <div className="space-y-5">
      <div className="p-4 rounded-lg bg-owly-primary-50/50 border border-owly-primary/20">
        <p className="text-sm text-owly-text">
          配置 Twilio 以启用电话支持。你需要一个可用的 Twilio 账户和电话号码。
        </p>
      </div>
      <FormField label="Account SID" description="Twilio 控制台中的 Account SID。">
        <PasswordInput
          value={data.twilioSid}
          onChange={(v) => update("twilioSid", v)}
          placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        />
      </FormField>
      <FormField label="Auth Token" description="Twilio 认证 token。">
        <PasswordInput
          value={data.twilioToken}
          onChange={(v) => update("twilioToken", v)}
          placeholder="请输入 Twilio auth token"
        />
      </FormField>
      <FormField label="电话号码" description="E.164 格式的 Twilio 电话号码。">
        <TextInput
          value={data.twilioPhone}
          onChange={(v) => update("twilioPhone", v)}
          placeholder="+1234567890"
        />
      </FormField>
    </div>
  );
}

function EmailSection({
  data,
  update,
}: {
  data: SettingsData;
  update: (field: keyof SettingsData, value: string | number) => void;
}) {
  return (
    <div className="space-y-6">
      {/* SMTP */}
      <div>
        <h4 className="text-sm font-semibold text-owly-text mb-4 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-owly-primary" />
          发件邮箱 (SMTP)
        </h4>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="SMTP 主机">
              <TextInput
                value={data.smtpHost}
                onChange={(v) => update("smtpHost", v)}
                placeholder="smtp.gmail.com"
              />
            </FormField>
            <FormField label="SMTP 端口">
              <NumberInput
                value={data.smtpPort}
                onChange={(v) => update("smtpPort", v)}
                min={1}
                max={65535}
              />
            </FormField>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="用户名">
              <TextInput
                value={data.smtpUser}
                onChange={(v) => update("smtpUser", v)}
                placeholder="your@email.com"
              />
            </FormField>
            <FormField label="密码">
              <PasswordInput
                value={data.smtpPass}
                onChange={(v) => update("smtpPass", v)}
                placeholder="请输入 SMTP 密码"
              />
            </FormField>
          </div>
          <FormField label="发件地址" description="显示为发件人的邮箱地址。">
            <TextInput
              value={data.smtpFrom}
              onChange={(v) => update("smtpFrom", v)}
              placeholder="support@yourbusiness.com"
            />
          </FormField>
        </div>
      </div>

      {/* IMAP */}
      <div>
        <h4 className="text-sm font-semibold text-owly-text mb-4 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-owly-primary" />
          收件邮箱 (IMAP)
        </h4>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="IMAP 主机">
              <TextInput
                value={data.imapHost}
                onChange={(v) => update("imapHost", v)}
                placeholder="imap.gmail.com"
              />
            </FormField>
            <FormField label="IMAP 端口">
              <NumberInput
                value={data.imapPort}
                onChange={(v) => update("imapPort", v)}
                min={1}
                max={65535}
              />
            </FormField>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="用户名">
              <TextInput
                value={data.imapUser}
                onChange={(v) => update("imapUser", v)}
                placeholder="your@email.com"
              />
            </FormField>
            <FormField label="密码">
              <PasswordInput
                value={data.imapPass}
                onChange={(v) => update("imapPass", v)}
                placeholder="请输入 IMAP 密码"
              />
            </FormField>
          </div>
        </div>
      </div>
    </div>
  );
}

function WhatsAppSection({
  data,
  update,
}: {
  data: SettingsData;
  update: (field: keyof SettingsData, value: string | number) => void;
}) {
  return (
    <div className="space-y-5">
      <div className="p-4 rounded-lg bg-owly-primary-50/50 border border-owly-primary/20">
        <p className="text-sm text-owly-text">
          选择 WhatsApp Web（免费，需要扫码）或官方 WhatsApp Business API（付费，更稳定）。
        </p>
      </div>
      <FormField label="连接模式" description="选择 Owly 连接 WhatsApp 的方式。">
        <SelectInput
          value={data.whatsappMode}
          onChange={(v) => update("whatsappMode", v)}
          options={[
            { value: "web", label: "WhatsApp Web" },
            { value: "api", label: "WhatsApp Business API" },
          ]}
        />
      </FormField>
      {data.whatsappMode === "api" && (
        <>
          <FormField label="API Key" description="你的 WhatsApp Business API Key。">
            <PasswordInput
              value={data.whatsappApiKey}
              onChange={(v) => update("whatsappApiKey", v)}
              placeholder="请输入 WhatsApp API Key"
            />
          </FormField>
          <FormField label="电话号码" description="E.164 格式的 WhatsApp Business 电话号码。">
            <TextInput
              value={data.whatsappPhone}
              onChange={(v) => update("whatsappPhone", v)}
              placeholder="+1234567890"
            />
          </FormField>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main settings page
// ---------------------------------------------------------------------------

const defaultSettings: SettingsData = {
  businessName: "我的业务",
  businessDesc: "",
  welcomeMessage: "您好！今天有什么可以帮您？",
  tone: "friendly",
  language: "auto",
  aiProvider: "openai",
  aiModel: "gpt-4o-mini",
  aiApiKey: "",
  maxTokens: 2048,
  temperature: 0.7,
  elevenLabsKey: "",
  elevenLabsVoice: "",
  twilioSid: "",
  twilioToken: "",
  twilioPhone: "",
  smtpHost: "",
  smtpPort: 587,
  smtpUser: "",
  smtpPass: "",
  smtpFrom: "",
  imapHost: "",
  imapPort: 993,
  imapUser: "",
  imapPass: "",
  whatsappMode: "web",
  whatsappApiKey: "",
  whatsappPhone: "",
};

export default function SettingsPage() {
  const [data, setData] = useState<SettingsData>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<SectionKey>("general");
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: "success" | "error", message: string) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then((settings) => {
        const merged = { ...defaultSettings };
        for (const key of Object.keys(merged) as (keyof SettingsData)[]) {
          if (settings[key] !== undefined && settings[key] !== null) {
            (merged as Record<string, unknown>)[key] = settings[key];
          }
        }
        setData(merged);
      })
      .catch(() => addToast("error", "加载设置失败"))
      .finally(() => setLoading(false));
  }, [addToast]);

  const update = (field: keyof SettingsData, value: string | number) => {
    setData((prev) => ({ ...prev, [field]: value }));
  };

  const saveSection = async () => {
    setSaving(true);
    try {
      const fields = sectionFields[activeTab];
      const payload: Record<string, unknown> = {};
      for (const f of fields) {
        payload[f] = data[f];
      }

      const res = await fetch("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("保存失败");
      addToast("success", "设置已保存");
    } catch {
      addToast("error", "保存设置失败，请重试。");
    } finally {
      setSaving(false);
    }
  };

  const sectionRenderers: Record<SectionKey, React.ReactNode> = {
    general: <GeneralSection data={data} update={update} />,
    ai: <AISection data={data} update={update} />,
    voice: <VoiceSection data={data} update={update} />,
    phone: <PhoneSection data={data} update={update} />,
    email: <EmailSection data={data} update={update} />,
    whatsapp: <WhatsAppSection data={data} update={update} />,
  };

  if (loading) {
    return (
      <>
        <Header title="设置" description="配置你的 Owly 实例" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-owly-primary" />
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="设置" description="配置你的 Owly 实例" />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Tab navigation */}
          <div className="flex gap-1 p-1 bg-owly-bg rounded-xl border border-owly-border mb-6 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
                    isActive
                      ? "bg-owly-surface text-owly-primary shadow-sm"
                      : "text-owly-text-light hover:text-owly-text hover:bg-owly-surface/50"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Section content */}
          <div className="bg-owly-surface rounded-xl border border-owly-border p-6 space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-owly-text">
                {tabs.find((t) => t.key === activeTab)?.label}
              </h3>
              <p className="text-sm text-owly-text-light mt-0.5">
                {activeTab === "general" &&
                  "配置业务身份和沟通偏好。"}
                {activeTab === "ai" &&
                  "设置用于客户互动的 AI 模型。"}
                {activeTab === "voice" &&
                  "配置语音支持渠道的文字转语音能力。"}
                {activeTab === "phone" &&
                  "连接 Twilio 账户以处理电话通话。"}
                {activeTab === "email" &&
                  "设置用于支持工单的邮件收发。"}
                {activeTab === "whatsapp" &&
                  "配置 WhatsApp 集成以支持消息沟通。"}
              </p>
            </div>

            {sectionRenderers[activeTab]}

            <SaveButton onClick={saveSection} saving={saving} />
          </div>
        </div>
      </div>

      <ToastContainer toasts={toasts} />
    </>
  );
}
