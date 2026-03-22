import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function proxyRequest(
  req: NextRequest,
  backendPath: string
): Promise<NextResponse> {
  const url = `${API_BASE}${backendPath}`;
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      const body = await req.text();
      if (body) init.body = body;
    } catch {
      // no body
    }
  }

  try {
    const res = await fetch(url, init);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Backend unreachable", data: null, timestamp: new Date().toISOString() },
      { status: 502 }
    );
  }
}
