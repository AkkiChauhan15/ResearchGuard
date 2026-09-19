import { getAccessToken } from './auth'
import type { ApiConfig, AuthenticatedUser, Decision, ExperimentalContext, Review, ReviewInput } from './types'

const sessionId = crypto.randomUUID()

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { error?: unknown }
    if (typeof payload.error === 'string' && payload.error.trim()) return payload.error
  } catch {
    // The API normally returns JSON errors; keep a safe fallback for proxy/network pages.
  }
  return `The local service returned HTTP ${response.status}.`
}

type AuthMode = 'none' | 'optional' | 'required'

async function request<T>(path: string, options: RequestInit = {}, authMode: AuthMode = 'optional'): Promise<T> {
  let token: string | null = null
  if (authMode === 'required') {
    try {
      token = await getAccessToken(true)
    } catch (reason) {
      throw new ApiError(reason instanceof Error ? reason.message : 'Sign in with Google first.', 401)
    }
  }
  if (authMode === 'optional') {
    try {
      token = await getAccessToken(false)
    } catch {
      token = null
    }
  }
  let response: Response
  try {
    response = await fetch(path, {
      ...options,
      headers: {
        'X-Review-Session': sessionId,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError('The local backend is unavailable. Start FastAPI on port 8000 and try again.', 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  return (await response.json()) as T
}

export const api = {
  config: () => request<ApiConfig>('/api/config', {}, 'none'),
  authMe: () => request<AuthenticatedUser>('/api/auth/me', {}, 'required'),
  createReview: (input: ReviewInput) =>
    request<Review>('/api/reviews', { method: 'POST', body: JSON.stringify(input) }, 'required'),
  createDemo: () => request<Review>('/api/reviews/demo', { method: 'POST' }, 'none'),
  editClaim: (reviewId: string, claimId: string, text: string) =>
    request<Review>(`/api/reviews/${reviewId}/claims/${claimId}`, {
      method: 'PATCH',
      body: JSON.stringify({ text }),
    }),
  editContext: (reviewId: string, context: ExperimentalContext) =>
    request<Review>(`/api/reviews/${reviewId}/context`, {
      method: 'PATCH',
      body: JSON.stringify(context),
    }),
  extract: (reviewId: string) =>
    request<Review>(`/api/reviews/${reviewId}/extraction`, { method: 'POST' }),
  retrieve: (reviewId: string, claimId: string, query: string) =>
    request<Review>(`/api/reviews/${reviewId}/claims/${claimId}/retrievals`, {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),
  assess: (reviewId: string, claimId: string) =>
    request<Review>(`/api/reviews/${reviewId}/claims/${claimId}/assessment`, { method: 'POST' }),
  decide: (reviewId: string, claimId: string, decision: Decision) =>
    request<Review>(`/api/reviews/${reviewId}/claims/${claimId}/decision`, {
      method: 'PUT',
      body: JSON.stringify({ decision }),
    }),
}

export async function downloadExport(review: Review, format: 'json' | 'txt'): Promise<void> {
  let token: string | null = null
  try {
    token = await getAccessToken(false)
  } catch {
    if (review.mode === 'live') throw new ApiError('Sign in again before exporting this live review.', 401)
  }
  let response: Response
  try {
    response = await fetch(`/api/reviews/${review.review_id}/export?format=${format}`, {
      headers: {
        'X-Review-Session': sessionId,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
  } catch {
    throw new ApiError('The local backend is unavailable. The export was not created.', 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  const objectUrl = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = `research-guard-${review.mode}.${format}`
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000)
}
