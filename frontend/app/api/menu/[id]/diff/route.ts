import { NextRequest } from "next/server";
import { proxyRequest } from "@/lib/proxy";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const search = req.nextUrl.searchParams.toString();
  return proxyRequest(req, `/api/menu/${id}/diff${search ? `?${search}` : ""}`);
}
