const days = ["一", "二", "三", "四", "五", "六", "日"];
const hours = Array.from({ length: 24 }, (_, i) => i);

interface PopularTimesHeatmapProps {
  data: Record<string, number[]> | null;
}

export default function PopularTimesHeatmap({ data }: PopularTimesHeatmapProps) {
  if (!data) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-400">
        資料不足，無法顯示熱門時段。
      </div>
    );
  }

  const dayKeys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead>
          <tr>
            <th className="p-1"></th>
            {hours.map((h) => (
              <th key={h} className="p-1 text-gray-400 font-normal">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dayKeys.map((dayKey, i) => {
            const values = data[dayKey] || [];
            return (
              <tr key={dayKey}>
                <td className="p-1 font-medium text-gray-600">{days[i]}</td>
                {hours.map((h) => {
                  const val = values[h] || 0;
                  const maxVal = Math.max(...Object.values(data).flat(), 1);
                  const intensity = val / maxVal;
                  const bg = intensity === 0
                    ? "bg-gray-100"
                    : intensity < 0.3
                    ? "bg-blue-100"
                    : intensity < 0.6
                    ? "bg-blue-300"
                    : "bg-blue-500";
                  return (
                    <td
                      key={h}
                      className={`p-1 w-5 h-5 ${bg} rounded-sm`}
                      title={`${days[i]} ${h}:00 — ${val}%`}
                    />
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
