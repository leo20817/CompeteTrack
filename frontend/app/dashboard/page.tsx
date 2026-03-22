"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";
import BrandCard from "@/components/BrandCard";
import ChangeTimeline from "@/components/ChangeTimeline";

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningUpdate, setRunningUpdate] = useState(false);
  const [updateMsg, setUpdateMsg] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [sumRes, tlRes, brRes] = await Promise.all([
        api.dashboard.summary(),
        api.dashboard.timeline(),
        api.brands.list(),
      ]);
      if (sumRes.success) setSummary(sumRes.data);
      if (tlRes.success) setTimeline((tlRes.data as any)?.items || []);
      if (brRes.success) setBrands((brRes.data as any)?.items || []);
    } catch (err) {
      console.error("Failed to load dashboard", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRunNow() {
    setRunningUpdate(true);
    setUpdateMsg("");
    try {
      const res = await api.scheduler.runNow();
      if (res.success) {
        setUpdateMsg("更新完成！");
        loadData();
      } else {
        setUpdateMsg(`失敗：${res.error}`);
      }
    } catch {
      setUpdateMsg("更新失敗");
    } finally {
      setRunningUpdate(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <div className="flex items-center gap-3">
          {updateMsg && (
            <span className={`text-sm ${updateMsg.includes("失敗") ? "text-red-500" : "text-green-600"}`}>
              {updateMsg}
            </span>
          )}
          <button
            onClick={handleRunNow}
            disabled={runningUpdate}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {runningUpdate && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            立即更新所有品牌
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">追蹤品牌數</p>
          <p className="text-3xl font-bold">{summary?.brand_count ?? 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">本週變化數</p>
          <p className="text-3xl font-bold">{summary?.week_changes ?? 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">待讀通知</p>
          <p className="text-3xl font-bold">{summary?.unnotified ?? 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">最後更新</p>
          <p className="text-lg font-medium text-gray-600">
            {formatRelativeTime(summary?.last_updated)}
          </p>
        </div>
      </div>

      {brands.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3">追蹤品牌</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {brands.map((b: any) => (
              <BrandCard
                key={b.id}
                id={b.id}
                name={b.name}
                brand_type={b.brand_type}
                is_active={b.is_active}
                updated_at={b.updated_at}
              />
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">變化時間軸</h3>
        <ChangeTimeline items={timeline} />
      </div>
    </div>
  );
}
