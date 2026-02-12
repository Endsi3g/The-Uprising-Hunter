const DEFAULT_BASE_URL = "/api/proxy"

export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_BASE_URL
  return raw.endsWith("/") ? raw.slice(0, -1) : raw
}

export async function requestApi<T>(path: string, init?: RequestInit): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  const url = path.startsWith("http") ? path : `${getApiBaseUrl()}${normalizedPath}`
  const headers = new Headers(init?.headers || undefined)
  const response = await fetch(url, {
    ...init,
    headers,
    cache: "no-store",
  })
  if (!response.ok) {
    let message = `API request failed (${response.status}) for ${normalizedPath}`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload?.detail) {
        message = payload.detail
      }
    } catch {
      const text = await response.text()
      if (text) {
        message = text
      }
    }
    throw new Error(message)
  }
  return (await response.json()) as T
}

export async function fetchApi<T>(path: string): Promise<T> {
  return requestApi<T>(path)
}
