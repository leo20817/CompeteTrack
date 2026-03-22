import SeverityBadge from "./SeverityBadge";
import { formatDateTime } from "@/lib/formatters";

const changeTypeLabels: Record<string, string> = {
  price_increase: "漲價",
  price_decrease: "降價",
  new_item: "新品上架",
  removed_item: "商品下架",
};

interface TimelineItem {
  id: string;
  brand_name: string;
  change_type: string;
  severity: string;
  ai_summary: string | null;
  detected_at: string;
}

export default function ChangeTimeline({ items }: { items: TimelineItem[] }) {
  if (items.length === 0) {
    return <p className="text-gray-400">尚無變化記錄。新增品牌後開始追蹤。</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
          <div className="flex-shrink-0 mt-0.5">
            <SeverityBadge severity={item.severity} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium">{item.brand_name}</span>
              <span className="text-sm text-gray-500">
                {changeTypeLabels[item.change_type] || item.change_type}
              </span>
            </div>
            {item.ai_summary && (
              <p className="text-sm text-gray-600">{item.ai_summary}</p>
            )}
          </div>
          <div className="flex-shrink-0 text-xs text-gray-400">
            {formatDateTime(item.detected_at)}
          </div>
        </div>
      ))}
    </div>
  );
}
