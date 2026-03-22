import type { Metadata } from "next";
import Link from "next/link";
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
            <div className="flex items-center gap-6">
              <Link href="/dashboard" className="text-xl font-bold text-blue-600">
                CompeteTrack
              </Link>
              <div className="flex gap-4 text-sm">
                <Link href="/dashboard" className="text-gray-600 hover:text-blue-600">
                  儀表板
                </Link>
                <Link href="/brands" className="text-gray-600 hover:text-blue-600">
                  品牌管理
                </Link>
              </div>
            </div>
            <span className="text-sm text-gray-500">競品監控平台</span>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
