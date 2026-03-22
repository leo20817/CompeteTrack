"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/formatters";
import BrandFormModal from "@/components/BrandFormModal";

export default function BrandsPage() {
  const [brands, setBrands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editBrand, setEditBrand] = useState<any>(null);

  useEffect(() => { loadBrands(); }, []);

  async function loadBrands() {
    setLoading(true);
    const res = await api.brands.list();
    if (res.success) setBrands((res.data as any)?.items || []);
    setLoading(false);
  }

  async function handleCreate(data: any) {
    const res = await api.brands.create(data);
    if (!res.success) throw new Error(res.error || "建立失敗");
    loadBrands();
  }

  async function handleUpdate(data: any) {
    if (!editBrand) return;
    const res = await api.brands.update(editBrand.id, data);
    if (!res.success) throw new Error(res.error || "更新失敗");
    setEditBrand(null);
    loadBrands();
  }

  async function handleDisable(id: string, name: string) {
    if (!confirm(`確定停用「${name}」？`)) return;
    await api.brands.delete(id);
    loadBrands();
  }

  async function handleCollect(id: string) {
    const res = await api.brands.collect(id);
    if (res.success) {
      alert("資料收集完成！");
      loadBrands();
    } else {
      alert(`收集失敗：${res.error || "未知錯誤"}`);
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
        <h2 className="text-2xl font-bold">品牌管理</h2>
        <button
          onClick={() => { setEditBrand(null); setShowModal(true); }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          + 新增品牌
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">名稱</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">類型</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">狀態</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">更新時間</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {brands.map((b: any) => (
              <tr key={b.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <Link href={`/brands/${b.id}`} className="text-blue-600 hover:underline font-medium">
                    {b.name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    b.brand_type === "own" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-700"
                  }`}>
                    {b.brand_type === "own" ? "自有" : "競品"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {b.is_active ? (
                    <span className="text-green-600 text-sm">● 啟用</span>
                  ) : (
                    <span className="text-gray-400 text-sm">○ 停用</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {formatDateTime(b.updated_at)}
                </td>
                <td className="px-4 py-3 text-right space-x-2">
                  <button
                    onClick={() => handleCollect(b.id)}
                    className="text-sm text-green-600 hover:underline"
                  >
                    收集
                  </button>
                  <button
                    onClick={() => { setEditBrand(b); setShowModal(true); }}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    編輯
                  </button>
                  <button
                    onClick={() => handleDisable(b.id, b.name)}
                    className="text-sm text-red-500 hover:underline"
                  >
                    停用
                  </button>
                </td>
              </tr>
            ))}
            {brands.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  尚無品牌。點擊「新增品牌」開始追蹤。
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <BrandFormModal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditBrand(null); }}
        onSubmit={editBrand ? handleUpdate : handleCreate}
        initialData={editBrand || undefined}
        title={editBrand ? "編輯品牌" : "新增品牌"}
      />
    </div>
  );
}
