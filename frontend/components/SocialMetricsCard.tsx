interface MetricItem {
  label: string;
  value: string | number | null;
}

interface SocialMetricsCardProps {
  platform: string;
  platformLabel: string;
  platformColor: string;
  username: string | null;
  data: {
    snapshot_date: string;
    followers: number;
    metrics: Record<string, any>;
    top_posts: any[] | null;
  } | null;
  metrics: MetricItem[];
  children?: React.ReactNode;
}

function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString();
}

export default function SocialMetricsCard({
  platform,
  platformLabel,
  platformColor,
  username,
  data,
  metrics,
  children,
}: SocialMetricsCardProps) {
  if (!username) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className={`text-lg font-bold ${platformColor}`}>{platformLabel}</span>
        </div>
        <p className="text-gray-400 text-sm">尚未設定帳號</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className={`text-lg font-bold ${platformColor}`}>{platformLabel}</span>
          <span className="text-sm text-gray-400">@{username}</span>
        </div>
        <p className="text-gray-400 text-sm">尚未收集資料</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${platformColor}`}>{platformLabel}</span>
          <span className="text-sm text-gray-400">@{username}</span>
        </div>
        <span className="text-xs text-gray-400">{data.snapshot_date}</span>
      </div>

      <div className="text-3xl font-bold mb-4">{formatNumber(data.followers)} <span className="text-sm font-normal text-gray-500">粉絲</span></div>

      <div className="grid grid-cols-2 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className="bg-gray-50 rounded p-2">
            <p className="text-xs text-gray-500">{m.label}</p>
            <p className="font-semibold">{typeof m.value === "number" ? formatNumber(m.value) : m.value ?? "—"}</p>
          </div>
        ))}
      </div>

      {children}
    </div>
  );
}
