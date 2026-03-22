import { NextRequest } from "next/server";
import { proxyRequest } from "@/lib/proxy";

export async function GET(req: NextRequest) {
  const search = req.nextUrl.searchParams.toString();
  return proxyRequest(req, `/api/brands${search ? `?${search}` : ""}`);
}

export async function POST(req: NextRequest) {
  return proxyRequest(req, "/api/brands");
}
