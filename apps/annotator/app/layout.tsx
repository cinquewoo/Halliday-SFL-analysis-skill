import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Halliday Lab · 语法隐喻标注",
  description: "在文本、理论与证据之间，建立可复核的语法隐喻标注。支持自动标注、人工审核、理论框架与 Excel 数据往返。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
