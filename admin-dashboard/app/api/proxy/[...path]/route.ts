import { NextRequest } from "next/server"

function getBaseUrl(): string {
  const raw = process.env.API_BASE_URL || "http://localhost:8000"
  return raw.endsWith("/") ? raw.slice(0, -1) : raw
}

function getAuthHeader(): string {
  const raw = process.env.ADMIN_AUTH
  if (!raw) {
    throw new Error("Missing ADMIN_AUTH in server environment.")
  }
  return `Basic ${Buffer.from(raw).toString("base64")}`
}

async function forwardRequest(
  request: NextRequest,
  path: string[],
): Promise<Response> {
  const baseUrl = getBaseUrl()
  const normalizedPath = path.join("/")
  const targetUrl = `${baseUrl}/${normalizedPath}${request.nextUrl.search}`

  const headers = new Headers(request.headers)
  headers.set("Authorization", getAuthHeader())
  headers.delete("host")
  headers.delete("content-length")

  const method = request.method.toUpperCase()
  const body =
    method === "GET" || method === "HEAD" ? undefined : await request.text()

  const upstream = await fetch(targetUrl, {
    method,
    headers,
    body,
    cache: "no-store",
  })

  const responseHeaders = new Headers(upstream.headers)
  responseHeaders.delete("content-encoding")
  responseHeaders.delete("transfer-encoding")

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  })
}

type ProxyContext = {
  params:
    | {
        path: string[]
      }
    | Promise<{
        path: string[]
      }>
}

async function handler(request: NextRequest, context: ProxyContext): Promise<Response> {
  const { path } = await Promise.resolve(context.params)
  return forwardRequest(request, path)
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE }
