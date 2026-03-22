import { NextRequest } from "next/server";
import { proxyRequest } from "@/lib/proxy";

export async function GET(req: NextRequest) {
  const search = req.nextUrl.searchParams.toString();
  return proxyRequest(req, `/api/changes${search ? `?${search}` : ""}`);
}
