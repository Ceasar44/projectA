import { NextRequest, NextResponse } from "next/server";

const backendBase = (
  process.env.BACKEND_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

function buildBackendUrl(path: string[], request: NextRequest): string {
  const joined = path.join("/");
  const search = request.nextUrl.search || "";
  return `${backendBase}/api/${joined}${search}`;
}

function buildHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);
  headers.set("host", backendBase.replace(/^https?:\/\//, ""));
  return headers;
}

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  const { path } = await context.params;
  const url = buildBackendUrl(path, request);
  const method = request.method.toUpperCase();
  const headers = buildHeaders(request);

  let body: BodyInit | undefined;
  if (!["GET", "HEAD"].includes(method)) {
    body = await request.text();
  }

  const response = await fetch(url, {
    method,
    headers,
    body,
    redirect: "manual",
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  responseHeaders.delete("transfer-encoding");

  const setCookie = response.headers.get("set-cookie");
  if (setCookie) {
    responseHeaders.set("set-cookie", setCookie);
  }

  const proxiedResponse = new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });

  const isAuthRoute = path.length > 0 && path[0] === "auth";
  if (response.status === 401 && !isAuthRoute) {
    proxiedResponse.cookies.delete("owly-token");
    proxiedResponse.headers.set("x-owly-auth-expired", "1");
  }

  return proxiedResponse;
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function OPTIONS(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}
