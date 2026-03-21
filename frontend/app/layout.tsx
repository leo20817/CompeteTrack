import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CompeteTrack",
  description: "Vietnam F&B competitive intelligence platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hant">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <h1 className="text-xl font-bold text-blue-600">CompeteTrack</h1>
            <span className="text-sm text-gray-500">競品監控平台</span>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
