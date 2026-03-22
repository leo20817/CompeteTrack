import Link from "next/link";
import { formatRelativeTime } from "@/lib/formatters";

interface BrandCardProps {
  id: string;
  name: string;
  brand_type: string;
  is_active: boolean;
  updated_at: string;
}

export default function BrandCard({ id, name, brand_type, is_active, updated_at }: BrandCardProps) {
  const typeBadge = brand_type === "own"
    ? "bg-blue-100 text-blue-700"
    : "bg-gray-100 text-gray-700";
  const typeLabel = brand_type === "own" ? "自有" : "競品";

  return (
    <Link href={`/brands/${id}`}>
      <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-lg truncate">{name}</h3>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeBadge}`}>
            {typeLabel}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          {is_active ? (
            <span className="text-green-600">● 追蹤中</span>
          ) : (
            <span className="text-gray-400">○ 已停用</span>
          )}
          <span className="ml-3">更新：{formatRelativeTime(updated_at)}</span>
        </div>
      </div>
    </Link>
  );
}
