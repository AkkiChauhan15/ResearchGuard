import { getAccessToken } from './auth'
import type {
  ApiConfig,
  AuthenticatedUser,
  Decision,
  ExperimentalContext,
  Review,
  ReviewInput,
  SavedReviewList,
  SavedReviewRecord,
  SavedReviewSummary,
  ChatMessageInput,
  ChatProviderId,
  ChatProviderStatus,
  ChatResponse,
  SavedChatList,
  SavedChatRecord,
  SavedChatSummary,
  ProviderId,
} from './types'

const sessionId = crypto.randomUUID()
const configuredApiOrigin = import.meta.env.VITE_API_BASE_URL?.trim().replace(/\/$/, '')

function apiUrl(path: string): string {
  if (!configuredApiOrigin) return path
  const parsed = new URL(configuredApiOrigin)
  const localHttp = parsed.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(parsed.hostname)
  if (
    parsed.origin !== configuredApiOrigin
    || (!localHttp && parsed.protocol !== 'https:')
    || parsed.username
    || parsed.password
    || parsed.pathname !== '/'
    || parsed.search
    || parsed.hash
  ) {
    throw new Error('VITE_API_BASE_URL must be one exact HTTPS origin, or a local HTTP origin.')
  }
  return `${parsed.origin}${path}`
}

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
  return `The backend service returned HTTP ${response.status}.`
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
    response = await fetch(apiUrl(path), {
      ...options,
      headers: {
        'X-Review-Session': sessionId,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError('The backend service is unavailable. Check its address and try again.', 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  return (await response.json()) as T
}

export const api = {
  config: () => request<ApiConfig>('/api/config', {}, 'none'),
  authMe: () => request<AuthenticatedUser>('/api/auth/me', {}, 'required'),
  chatProviders: () => request<ChatProviderStatus>('/api/chat/providers', {}, 'required'),
  chat: (
    provider: ChatProviderId,
    model: string,
    messages: ChatMessageInput[],
    allowFallback: boolean,
    chatId: string | null,
    expectedRevision: number | null,
  ) =>
    request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        provider,
        model,
        messages,
        allow_fallback: allowFallback,
        chat_id: chatId,
        expected_revision: expectedRevision,
      }),
    }, 'required'),
  listSavedChats: () => request<SavedChatList>('/api/chats', {}, 'required'),
  getSavedChat: (chatId: string) => request<SavedChatRecord>(`/api/chats/${chatId}`, {}, 'required'),
  deleteSavedChat: (chatId: string, expectedRevision: number) =>
    request<{ deleted: SavedChatSummary }>(
      `/api/chats/${chatId}?expected_revision=${expectedRevision}`,
      { method: 'DELETE' },
      'required',
    ),
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
  secondOpinion: (reviewId: string, claimId: string, provider: ProviderId) =>
    request<Review>(`/api/reviews/${reviewId}/claims/${claimId}/second-opinions`, {
      method: 'POST',
      body: JSON.stringify({ provider }),
    }, 'required'),
  decide: (reviewId: string, claimId: string, decision: Decision) =>
    request<Review>(`/api/reviews/${reviewId}/claims/${claimId}/decision`, {
      method: 'PUT',
      body: JSON.stringify({ decision }),
    }),
  listSavedReviews: () => request<SavedReviewList>('/api/saved-reviews', {}, 'required'),
  saveReview: (reviewId: string) =>
    request<SavedReviewRecord>('/api/saved-reviews', {
      method: 'POST',
      body: JSON.stringify({ review_id: reviewId }),
    }, 'required'),
  openSavedReview: (savedId: string) =>
    request<SavedReviewRecord>(`/api/saved-reviews/${savedId}/open`, { method: 'POST' }, 'required'),
  updateSavedReview: (savedId: string, reviewId: string, expectedRevision: number) =>
    request<SavedReviewRecord>(`/api/saved-reviews/${savedId}`, {
      method: 'PUT',
      body: JSON.stringify({ review_id: reviewId, expected_revision: expectedRevision }),
    }, 'required'),
  deleteSavedReview: (savedId: string, expectedRevision: number) =>
    request<{ deleted: SavedReviewSummary }>(
      `/api/saved-reviews/${savedId}?expected_revision=${expectedRevision}`,
      { method: 'DELETE' },
      'required',
    ),
}

export async function downloadSavedChatPdf(chatId: string): Promise<void> {
  let token: string
  try {
    token = (await getAccessToken(true))!
  } catch (reason) {
    throw new ApiError(reason instanceof Error ? reason.message : 'Sign in again before exporting.', 401)
  }
  let response: Response
  try {
    response = await fetch(apiUrl(`/api/chats/${chatId}/export.pdf`), {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new ApiError('The backend service is unavailable. The PDF was not created.', 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  const objectUrl = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = `research-guard-chat-${chatId}.pdf`
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000)
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
    response = await fetch(apiUrl(`/api/reviews/${review.review_id}/export?format=${format}`), {
      headers: {
        'X-Review-Session': sessionId,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
  } catch {
    throw new ApiError('The backend service is unavailable. The export was not created.', 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  const objectUrl = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = `research-guard-${review.mode}.${format}`
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000)
}

export async function downloadSavedExport(savedId: string, mode: 'demo' | 'live', format: 'json' | 'txt'): Promise<void> {
  let token: string
  try {
    token = (await getAccessToken(true))!
  } catch (reason) {
    throw new ApiError(reason instanceof Error ? reason.message : 'Sign in again before exporting.', 401)
  }
  let response: Response
  try {
    response = await fetch(apiUrl(`/api/saved-reviews/${savedId}/export?format=${format}`), {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new ApiError('The backend service is unavailable. The saved export was not created.', 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  const objectUrl = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = `research-guard-saved-${mode}.${format}`
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000)
}
