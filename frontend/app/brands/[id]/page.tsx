"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatVND, formatDate, formatDateTime } from "@/lib/formatters";
import SeverityBadge from "@/components/SeverityBadge";
import MenuDiffView from "@/components/MenuDiffView";
import PopularTimesHeatmap from "@/components/PopularTimesHeatmap";

const tabs = ["菜單", "價格歷史", "營業時段", "變化記錄"];

const changeTypeLabels: Record<string, string> = {
  price_increase: "漲價",
  price_decrease: "降價",
  new_item: "新品上架",
  removed_item: "商品下架",
};

export default function BrandDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [brand, setBrand] = useState<any>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);

  // Tab data
  const [menu, setMenu] = useState<any>(null);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [diff, setDiff] = useState<any>(null);
  const [changes, setChanges] = useState<any[]>([]);
  const [severityFilter, setSeverityFilter] = useState("");

  // Hours data from menu latest snapshot
  const [hoursData, setHoursData] = useState<any>(null);

  useEffect(() => {
    loadBrand();
  }, [id]);

  useEffect(() => {
    if (activeTab === 0) loadMenu();
    if (activeTab === 3) loadChanges();
  }, [activeTab, id]);

  async function loadBrand() {
    setLoading(true);
    const res = await api.brands.get(id);
    if (res.success) setBrand(res.data);
    setLoading(false);
  }

  async function loadMenu() {
    const [menuRes, snapRes] = await Promise.all([
      api.menu.latest(id),
      api.menu.snapshots(id),
    ]);
    if (menuRes.success) setMenu(menuRes.data);
    if (snapRes.success) setSnapshots((snapRes.data as any)?.items || []);
  }

  async function loadDiff(oldId?: string, newId?: string) {
    const res = await api.menu.diff(id, oldId, newId);
    if (res.success) setDiff(res.data);
  }

  async function loadChanges() {
    const params: any = { brand_id: id, limit: 100 };
    if (severityFilter) params.severity = severityFilter;
    const res = await api.changes.list(params);
    if (res.success) setChanges((res.data as any)?.items || []);
  }

  useEffect(() => {
    if (activeTab === 3) loadChanges();
  }, [severityFilter]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!brand) {
    return <div className="text-center py-12 text-gray-400">品牌不存在</div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link href="/brands" className="text-gray-400 hover:text-gray-600">← 返回</Link>
        <h2 className="text-2xl font-bold">{brand.name}</h2>
        <span className={`px-2 py-0.5 rounded text-xs ${
          brand.brand_type === "own" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-700"
        }`}>
          {brand.brand_type === "own" ? "自有" : "競品"}
        </span>
        {brand.google_place_id && (
          <span className="text-xs text-gray-400">Place ID: {brand.google_place_id}</span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {tabs.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === i
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab 0: 菜單 */}
      {activeTab === 0 && (
        <div>
          {menu?.items && menu.items.length > 0 ? (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">品項</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">分類</th>
                    <th className="text-right px-4 py-3 text-sm font-medium text-gray-600">價格</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {menu.items.map((item: any) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{item.item_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{item.category || "—"}</td>
                      <td className="px-4 py-3 text-right">{formatVND(item.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400">尚無菜單資料。</p>
          )}

          {/* Diff section */}
          {snapshots.length >= 2 && (
            <div className="mt-6">
              <div className="flex items-center gap-3 mb-3">
                <h3 className="font-semibold">快照比較</h3>
                <button
                  onClick={() => loadDiff()}
                  className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
                >
                  比較最近兩次
                </button>
              </div>
              {diff && <MenuDiffView items={diff.diff || []} />}
            </div>
          )}
        </div>
      )}

      {/* Tab 1: 價格歷史 */}
      {activeTab === 1 && (
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-400">價格歷史圖表將在有多次快照資料後顯示。</p>
          {snapshots.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">快照記錄</h4>
              <div className="space-y-2">
                {snapshots.map((s: any) => (
                  <div key={s.id} className="flex justify-between text-sm p-2 bg-gray-50 rounded">
                    <span>{formatDate(s.snapshot_date)}</span>
                    <span className="text-gray-500">{s.item_count ?? 0} 項</span>
                    <span className="text-gray-400">{s.source}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: 營業時段 */}
      {activeTab === 2 && (
        <div>
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="font-semibold mb-3">每週營業時間</h3>
            {menu?.snapshot ? (
              <p className="text-gray-400">營業時段資料請從 Google Places 收集。</p>
            ) : (
              <p className="text-gray-400">尚無營業時段資料。</p>
            )}
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-3">熱門時段</h3>
            <PopularTimesHeatmap data={null} />
          </div>
        </div>
      )}

      {/* Tab 3: 變化記錄 */}
      {activeTab === 3 && (
        <div>
          <div className="flex gap-3 mb-4">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="border rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="">全部嚴重度</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>

          {changes.length > 0 ? (
            <div className="space-y-2">
              {changes.map((c: any) => (
                <div key={c.id} className="bg-white rounded-lg shadow p-4 flex items-start gap-3">
                  <SeverityBadge severity={c.severity} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">
                        {changeTypeLabels[c.change_type] || c.change_type}
                      </span>
                      <span className="text-xs text-gray-400">{c.field_changed}</span>
                    </div>
                    {c.ai_summary && (
                      <p className="text-sm text-gray-600 mb-1">{c.ai_summary}</p>
                    )}
                    <div className="text-xs text-gray-400">
                      {c.old_value && (
                        <span>
                          {JSON.stringify(c.old_value.price || c.old_value.item_name)} →{" "}
                          {JSON.stringify(c.new_value.price || c.new_value.item_name)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">{formatDateTime(c.detected_at)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400">尚無變化記錄。</p>
          )}
        </div>
      )}
    </div>
  );
}
