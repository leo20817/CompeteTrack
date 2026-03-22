// All API calls go through Next.js API routes (server-side proxy).
// NEVER call FastAPI directly from client components.

interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  error: string | null;
  timestamp: string;
}

async function fetchAPI<T>(
  path: string,
  options?: RequestInit
): Promise<APIResponse<T>> {
  const res = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  const json = await res.json().catch(() => ({
    success: false,
    data: null,
    error: `HTTP ${res.status}`,
    timestamp: new Date().toISOString(),
  }));

  return json;
}

export const api = {
  dashboard: {
    summary: () => fetchAPI("/api/dashboard/summary"),
    timeline: (days = 30) => fetchAPI(`/api/dashboard/timeline?days=${days}`),
  },
  brands: {
    list: (limit = 50, offset = 0) =>
      fetchAPI(`/api/brands?limit=${limit}&offset=${offset}`),
    get: (id: string) => fetchAPI(`/api/brands/${id}`),
    create: (data: Record<string, unknown>) =>
      fetchAPI("/api/brands", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Record<string, unknown>) =>
      fetchAPI(`/api/brands/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: string) =>
      fetchAPI(`/api/brands/${id}`, { method: "DELETE" }),
    collect: (id: string) =>
      fetchAPI(`/api/brands/${id}/collect`, { method: "POST" }),
  },
  menu: {
    latest: (brandId: string) => fetchAPI(`/api/menu/${brandId}`),
    snapshots: (brandId: string) => fetchAPI(`/api/menu/${brandId}/snapshots`),
    diff: (brandId: string, oldId?: string, newId?: string) => {
      let url = `/api/menu/${brandId}/diff`;
      if (oldId && newId) url += `?old_snapshot_id=${oldId}&new_snapshot_id=${newId}`;
      return fetchAPI(url);
    },
  },
  hours: {
    latest: (brandId: string) => fetchAPI(`/api/hours/${brandId}`),
  },
  changes: {
    list: (params?: { brand_id?: string; severity?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.brand_id) q.set("brand_id", params.brand_id);
      if (params?.severity) q.set("severity", params.severity);
      if (params?.limit) q.set("limit", String(params.limit));
      return fetchAPI(`/api/changes?${q.toString()}`);
    },
  },
  scheduler: {
    runNow: () => fetchAPI("/api/scheduler/run-now", { method: "POST" }),
  },
};
