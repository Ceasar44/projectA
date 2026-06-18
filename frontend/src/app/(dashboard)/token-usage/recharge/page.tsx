"use client";

import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { cn } from "@/lib/utils";
import { ArrowLeft, CreditCard, Loader2, QrCode } from "lucide-react";
import { useState } from "react";

const packages = [
  { name: "基础包", tokens: 5000, amountCents: 9900, description: "适合轻量使用与试运行" },
  { name: "增长包", tokens: 20000, amountCents: 29900, description: "适合稳定运行 AI 工作页" },
  { name: "企业包", tokens: 50000, amountCents: 69900, description: "适合高频客服与营销自动化" },
];

const paymentMethods = [
  { value: "alipay", label: "支付宝" },
  { value: "wechat", label: "微信" },
];

export default function TokenRechargePage() {
  const router = useRouter();
  const [selectedPackage, setSelectedPackage] = useState(packages[1]);
  const [paymentMethod, setPaymentMethod] = useState("alipay");
  const [creating, setCreating] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [orderId, setOrderId] = useState("");

  const handleCreateOrder = async () => {
    setCreating(true);
    try {
      const res = await fetch("/api/tokens/recharge/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          packageName: selectedPackage.name,
          paymentMethod,
          amountCents: selectedPackage.amountCents,
          tokens: selectedPackage.tokens,
        }),
      });
      if (res.ok) {
        const json = await res.json();
        setOrderId(json.id);
      }
    } finally {
      setCreating(false);
    }
  };

  const handleCompleteOrder = async () => {
    if (!orderId) return;
    setCompleting(true);
    try {
      const res = await fetch(`/api/tokens/recharge/orders/${orderId}/complete`, {
        method: "POST",
      });
      if (res.ok) {
        router.push("/token-usage");
      }
    } finally {
      setCompleting(false);
    }
  };

  return (
    <>
      <Header
        title="Token 充值"
        description="选择充值套餐，并通过支付宝或微信完成 token 充值。"
        actions={
          <button
            onClick={() => router.push("/token-usage")}
            className="inline-flex items-center gap-2 rounded-lg border border-owly-border px-4 py-2 text-sm font-medium text-owly-text hover:bg-owly-primary-50"
          >
            <ArrowLeft className="h-4 w-4" />
            返回统计页
          </button>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto grid max-w-[1200px] gap-6 xl:grid-cols-[1fr_0.9fr]">
          <section className="rounded-xl border border-owly-border bg-owly-surface">
            <div className="border-b border-owly-border px-5 py-4">
              <h3 className="text-sm font-semibold text-owly-text">选择充值套餐</h3>
              <p className="mt-1 text-xs text-owly-text-light">充值完成后，token 余额会立即更新到统计页。</p>
            </div>
            <div className="space-y-4 p-5">
              {packages.map((item) => (
                <button
                  key={item.name}
                  onClick={() => setSelectedPackage(item)}
                  className={cn(
                    "w-full rounded-xl border p-4 text-left transition-colors",
                    selectedPackage.name === item.name
                      ? "border-owly-primary bg-owly-primary-50"
                      : "border-owly-border hover:border-owly-primary/30"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-base font-semibold text-owly-text">{item.name}</p>
                      <p className="mt-1 text-sm text-owly-text-light">{item.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-base font-semibold text-owly-text">¥{(item.amountCents / 100).toFixed(2)}</p>
                      <p className="mt-1 text-xs text-owly-text-light">{item.tokens.toLocaleString()} tokens</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-owly-border bg-owly-surface">
            <div className="border-b border-owly-border px-5 py-4">
              <h3 className="text-sm font-semibold text-owly-text">支付方式</h3>
              <p className="mt-1 text-xs text-owly-text-light">支持支付宝和微信两种充值方式。</p>
            </div>
            <div className="space-y-5 p-5">
              <div className="grid grid-cols-2 gap-3">
                {paymentMethods.map((method) => (
                  <button
                    key={method.value}
                    onClick={() => setPaymentMethod(method.value)}
                    className={cn(
                      "rounded-xl border px-4 py-3 text-sm font-medium transition-colors",
                      paymentMethod === method.value
                        ? "border-owly-primary bg-owly-primary-50 text-owly-primary"
                        : "border-owly-border text-owly-text-light hover:border-owly-primary/30"
                    )}
                  >
                    {method.label}
                  </button>
                ))}
              </div>

              <div className="rounded-xl bg-owly-bg p-5">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-owly-surface p-3">
                    <QrCode className="h-8 w-8 text-owly-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-owly-text">订单摘要</p>
                    <p className="mt-1 text-xs text-owly-text-light">
                      {selectedPackage.name} · {selectedPackage.tokens.toLocaleString()} tokens · ¥
                      {(selectedPackage.amountCents / 100).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {!orderId ? (
                <button
                  onClick={handleCreateOrder}
                  disabled={creating}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-owly-primary px-4 py-3 text-sm font-medium text-white hover:bg-owly-primary-dark disabled:opacity-60"
                >
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
                  创建 {paymentMethod === "wechat" ? "微信" : "支付宝"} 订单
                </button>
              ) : (
                <div className="space-y-3 rounded-xl border border-green-200 bg-green-50 p-4">
                  <p className="text-sm font-medium text-green-700">订单已创建</p>
                  <p className="text-xs text-green-700/80">订单号：{orderId}</p>
                  <button
                    onClick={handleCompleteOrder}
                    disabled={completing}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60"
                  >
                    {completing ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
                    完成支付并更新余额
                  </button>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
