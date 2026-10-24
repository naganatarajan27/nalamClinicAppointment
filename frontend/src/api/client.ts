import type { ApiErrorBody } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function readCsrfCookie(): string | null {
  const match = document.cookie.match(/(?:^|; )nalam_csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

function extractErrorMessage(body: unknown, fallback: string): string {
  const detail = (body as ApiErrorBody | undefined)?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) return detail[0].msg ?? fallback
  return fallback
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, string | number | undefined | null>
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query } = options

  const url = new URL(`${API_BASE_URL}${path}`)
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value))
    }
  }

  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') {
    const csrfToken = readCsrfCookie()
    if (csrfToken) headers['X-CSRF-Token'] = csrfToken
  }

  let response: Response
  try {
    response = await fetch(url.toString(), {
      method,
      credentials: 'include',
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Please check your connection and try again.')
  }

  if (response.status === 204) return undefined as T

  let parsed: unknown = null
  const text = await response.text()
  if (text) {
    try {
      parsed = JSON.parse(text)
    } catch {
      parsed = null
    }
  }

  if (!response.ok) {
    throw new ApiError(
      response.status,
      extractErrorMessage(parsed, 'Something went wrong. Please try again.'),
    )
  }

  return parsed as T
}
