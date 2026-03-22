"use client";

import { useState, useEffect } from "react";

interface BrandFormData {
  name: string;
  brand_type: string;
  google_place_id: string;
  website_url: string;
  foody_url: string;
  notes: string;
}

interface BrandFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: BrandFormData) => Promise<void>;
  initialData?: Partial<BrandFormData>;
  title: string;
}

const emptyForm: BrandFormData = {
  name: "",
  brand_type: "competitor",
  google_place_id: "",
  website_url: "",
  foody_url: "",
  notes: "",
};

export default function BrandFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  title,
}: BrandFormModalProps) {
  const [form, setForm] = useState<BrandFormData>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      setForm({ ...emptyForm, ...initialData });
      setError("");
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("品牌名稱為必填");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onSubmit(form);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">品牌名稱 *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="例：Phở 24"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">類型</label>
            <select
              value={form.brand_type}
              onChange={(e) => setForm({ ...form, brand_type: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="own">自有品牌</option>
              <option value="competitor">競品</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Google Place ID</label>
            <input
              type="text"
              value={form.google_place_id}
              onChange={(e) => setForm({ ...form, google_place_id: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="ChIJ..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">網站 URL</label>
            <input
              type="text"
              value={form.website_url}
              onChange={(e) => setForm({ ...form, website_url: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Foody URL</label>
            <input
              type="text"
              value={form.foody_url}
              onChange={(e) => setForm({ ...form, foody_url: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">備註</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
              rows={2}
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "處理中..." : "儲存"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border rounded-lg py-2 hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
