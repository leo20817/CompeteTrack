interface Post {
  id: string;
  description: string;
  views?: number;
  likes?: number;
  comments?: number;
  thumbnail: string;
  url: string;
}

function formatNumber(n: number | undefined): string {
  if (!n) return "0";
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString();
}

export default function TopPostsGrid({
  posts,
  platform,
}: {
  posts: Post[];
  platform: "tiktok" | "instagram";
}) {
  if (!posts || posts.length === 0) return null;

  const metricLabel = platform === "tiktok" ? "觀看" : "讚";
  const metricKey = platform === "tiktok" ? "views" : "likes";

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-600 mb-2">Top 3 貼文</h4>
      <div className="space-y-2">
        {posts.map((post, i) => (
          <a
            key={post.id || i}
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
          >
            {post.thumbnail ? (
              <img
                src={post.thumbnail}
                alt=""
                className="w-12 h-12 rounded object-cover flex-shrink-0"
              />
            ) : (
              <div className="w-12 h-12 rounded bg-gray-200 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{post.description || "（無描述）"}</p>
              <p className="text-xs text-gray-500">
                {formatNumber(post[metricKey as keyof Post] as number)} {metricLabel}
              </p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
