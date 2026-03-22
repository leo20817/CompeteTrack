const colors: Record<string, string> = {
  high: "bg-red-500 text-white",
  medium: "bg-amber-500 text-white",
  low: "bg-gray-500 text-white",
};

const labels: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[severity] || "bg-gray-300"}`}>
      {labels[severity] || severity}
    </span>
  );
}
