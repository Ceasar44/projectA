import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import { ThemeInit } from "@/components/theme-init";
import "./globals.css";

export const metadata: Metadata = {
  title: "Owly - AI 客户支持",
  description: "开源 AI 客户支持助手",
  icons: {
    icon: "/owly.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="h-full">
          <Providers>
            <ThemeInit />
            {children}
          </Providers>
        </body>
    </html>
  );
}
