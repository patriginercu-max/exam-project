import type {
  Course,
  LoginResponse,
  Note,
  RecordFilters,
  RecordListResponse,
  WrongRecord,
} from './types'

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

let onUnauthorized: (() => void) | null = null

/** 由应用层注册：任何接口返回 401 时跳回登录页。 */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

function describeDetail(payload: unknown, status: number): string {
  const detail = (payload as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string' && detail) {
    return detail
  }
  // FastAPI 的请求校验错误是数组
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item as { msg?: string })?.msg)
      .filter((msg): msg is string => Boolean(msg))
    if (messages.length > 0) {
      return messages.join('；')
    }
  }
  return `请求失败（HTTP ${status}）`
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(path, {
    credentials: 'include',
    ...init,
    headers,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = null
    }
  }

  if (!response.ok) {
    if (response.status === 401 && !path.endsWith('/auth/login')) {
      onUnauthorized?.()
    }
    const code = (payload as { code?: string } | null)?.code ?? 'error'
    throw new ApiError(response.status, code, describeDetail(payload, response.status))
  }

  return payload as T
}

function buildQuery(filters: RecordFilters): string {
  const params = new URLSearchParams()
  if (filters.courseId) params.set('courseId', filters.courseId)
  if (filters.knowledgePoint) params.set('knowledgePoint', filters.knowledgePoint)
  if (filters.keyword) params.set('keyword', filters.keyword)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export const api = {
  login(login: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ login, password }),
    })
  },

  logout(): Promise<void> {
    return request<void>('/api/auth/logout', { method: 'POST' })
  },

  me(): Promise<LoginResponse> {
    return request<LoginResponse>('/api/auth/me')
  },

  listCourses(): Promise<Course[]> {
    return request<Course[]>('/api/courses')
  },

  listKnowledgePoints(): Promise<string[]> {
    return request<string[]>('/api/knowledge-points')
  },

  listRecords(filters: RecordFilters): Promise<RecordListResponse> {
    return request<RecordListResponse>(`/api/records${buildQuery(filters)}`)
  },

  getRecord(recordId: string): Promise<WrongRecord> {
    return request<WrongRecord>(`/api/records/${encodeURIComponent(recordId)}`)
  },

  saveNote(recordId: string, cause: string, content: string): Promise<Note> {
    return request<Note>(`/api/records/${encodeURIComponent(recordId)}/note`, {
      method: 'PUT',
      body: JSON.stringify({ cause, content }),
    })
  },

  clearNote(recordId: string): Promise<Note> {
    return request<Note>(`/api/records/${encodeURIComponent(recordId)}/note`, {
      method: 'DELETE',
    })
  },
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error && error.message) {
    return `网络异常：${error.message}`
  }
  return '未知错误'
}
