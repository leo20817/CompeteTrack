import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    // Forward the multipart form data directly
    const formData = await req.formData();
    const resp = await fetch(`${API_BASE}/api/menu-upload/${id}/upload`, {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch {
    return NextResponse.json(
      { success: false, error: "Backend unreachable", data: null },
      { status: 502 }
    );
  }
}
