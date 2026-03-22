import { formatVND } from "@/lib/formatters";

interface DiffItem {
  item_name: string;
  category: string | null;
  status: "added" | "removed" | "price_changed" | "unchanged";
  old_price: number | null;
  new_price: number | null;
  currency: string;
}

const statusStyles: Record<string, string> = {
  added: "bg-green-50 border-l-4 border-green-400",
  removed: "bg-red-50 border-l-4 border-red-400",
  price_changed: "bg-yellow-50 border-l-4 border-yellow-400",
  unchanged: "bg-white",
};

const statusLabels: Record<string, string> = {
  added: "新增",
  removed: "已下架",
  price_changed: "價格變動",
  unchanged: "無變化",
};

export default function MenuDiffView({ items }: { items: DiffItem[] }) {
  if (items.length === 0) {
    return <p className="text-gray-400">無菜單資料可比較。</p>;
  }

  return (
    <div className="space-y-1">
      {items.map((item) => (
        <div
          key={item.item_name}
          className={`flex items-center justify-between p-3 rounded ${statusStyles[item.status]}`}
        >
          <div className="flex-1">
            <span className="font-medium">{item.item_name}</span>
            {item.category && (
              <span className="ml-2 text-xs text-gray-400">{item.category}</span>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm">
            {item.status === "price_changed" && (
              <>
                <span className="text-gray-400 line-through">{formatVND(item.old_price)}</span>
                <span className="font-medium">→</span>
                <span className={item.new_price! > item.old_price! ? "text-red-600 font-medium" : "text-green-600 font-medium"}>
                  {formatVND(item.new_price)}
                </span>
              </>
            )}
            {item.status === "added" && (
              <span className="text-green-600 font-medium">{formatVND(item.new_price)}</span>
            )}
            {item.status === "removed" && (
              <span className="text-red-400 line-through">{formatVND(item.old_price)}</span>
            )}
            {item.status === "unchanged" && (
              <span className="text-gray-600">{formatVND(item.new_price)}</span>
            )}
            <span className={`text-xs px-2 py-0.5 rounded ${
              item.status === "added" ? "bg-green-200 text-green-800" :
              item.status === "removed" ? "bg-red-200 text-red-800" :
              item.status === "price_changed" ? "bg-yellow-200 text-yellow-800" :
              "bg-gray-100 text-gray-600"
            }`}>
              {statusLabels[item.status]}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
