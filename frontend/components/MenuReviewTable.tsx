"use client";

import { useState } from "react";
import { formatVND } from "@/lib/formatters";

interface MenuItem {
  item_name: string;
  category: string | null;
  price: number | null;
  description: string | null;
}

interface MenuReviewTableProps {
  brandId: string;
  items: MenuItem[];
  photoUrls: string[];
  notes: string | null;
  onConfirmed: () => void;
}

export default function MenuReviewTable({
  brandId,
  items: initialItems,
  photoUrls,
  notes,
  onConfirmed,
}: MenuReviewTableProps) {
  const [items, setItems] = useState<MenuItem[]>(initialItems);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function updateItem(index: number, field: keyof MenuItem, value: any) {
    setItems((prev) =>
      prev.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    );
  }

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  function addItem() {
    setItems((prev) => [
      ...prev,
      { item_name: "", category: null, price: null, description: null },
    ]);
  }

  async function handleConfirm() {
    const validItems = items.filter((i) => i.item_name.trim());
    if (validItems.length === 0) {
      setError("至少需要一個品項");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const resp = await fetch(`/api/menu-upload/${brandId}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: validItems,
          photo_urls: photoUrls,
        }),
      });
      const json = await resp.json();

      if (json.success) {
        onConfirmed();
      } else {
        setError(json.error || "儲存失敗");
      }
    } catch {
      setError("儲存失敗，請重試");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold">AI 解析結果 — 請確認後儲存</h4>
        <span className="text-sm text-gray-500">{items.length} 個品項</span>
      </div>

      {notes && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4 text-sm">
          <strong>AI 備註：</strong>{notes}
        </div>
      )}

      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-gray-600">品名</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600">分類</th>
              <th className="text-right px-3 py-2 font-medium text-gray-600">價格 (VND)</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600">描述</th>
              <th className="px-3 py-2 w-10"></th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((item, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-3 py-2">
                  <input
                    type="text"
                    value={item.item_name}
                    onChange={(e) => updateItem(i, "item_name", e.target.value)}
                    className="w-full border rounded px-2 py-1 text-sm"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    type="text"
                    value={item.category || ""}
                    onChange={(e) => updateItem(i, "category", e.target.value || null)}
                    className="w-full border rounded px-2 py-1 text-sm"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    value={item.price ?? ""}
                    onChange={(e) => updateItem(i, "price", e.target.value ? parseInt(e.target.value) : null)}
                    className="w-24 border rounded px-2 py-1 text-sm text-right"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    type="text"
                    value={item.description || ""}
                    onChange={(e) => updateItem(i, "description", e.target.value || null)}
                    className="w-full border rounded px-2 py-1 text-sm"
                  />
                </td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => removeItem(i)}
                    className="text-red-400 hover:text-red-600 text-xs"
                  >
                    刪除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <button
          onClick={addItem}
          className="text-sm text-blue-600 hover:underline"
        >
          + 手動新增品項
        </button>

        <button
          onClick={handleConfirm}
          disabled={saving}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
        >
          {saving && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />}
          {saving ? "儲存中..." : "確認並儲存"}
        </button>
      </div>
    </div>
  );
}
