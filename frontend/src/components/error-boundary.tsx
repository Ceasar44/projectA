"use client";

import React from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return <ErrorFallback onRetry={this.handleRetry} />;
    }

    return this.props.children;
  }
}

function ErrorFallback({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex min-h-[400px] items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-red-50">
          <AlertTriangle className="h-8 w-8 text-owly-danger" />
        </div>
        <h2 className="text-lg font-semibold text-owly-text">
          页面出错了
        </h2>
        <p className="mt-2 text-sm text-owly-text-light">
          发生了意外错误。你可以重试，或返回仪表盘。
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg border border-owly-border bg-owly-surface px-4 py-2 text-sm font-medium text-owly-text hover:bg-owly-bg transition-colors"
          >
            <Home className="h-4 w-4" />
            返回首页
          </a>
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg bg-owly-primary px-4 py-2 text-sm font-medium text-white hover:bg-owly-primary-dark transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            重试
          </button>
        </div>
      </div>
    </div>
  );
}
