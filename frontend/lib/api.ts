const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(error.error || `API error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  brands: {
    list: (limit = 50, offset = 0) =>
      fetchAPI(`/api/brands?limit=${limit}&offset=${offset}`),
    get: (id: string) => fetchAPI(`/api/brands/${id}`),
    create: (data: Record<string, unknown>) =>
      fetchAPI("/api/brands", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: Record<string, unknown>) =>
      fetchAPI(`/api/brands/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      fetchAPI(`/api/brands/${id}`, { method: "DELETE" }),
  },
  health: () => fetchAPI("/health"),
};
