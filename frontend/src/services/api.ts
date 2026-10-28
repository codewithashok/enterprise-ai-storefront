import type { Order, Product, ProductPage, ProductQuery, Token, User } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  token?: string | null
  json?: unknown
  form?: Record<string, string>
}

// FastAPI errors are either {detail: "msg"} or {detail: [{msg, loc}, ...]} for 422s
function errorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d: { msg?: string }) => d.msg?.replace(/^Value error, /, '')).join('. ')
  }
  return fallback
}

async function request<T>(path: string, { method = 'GET', token, json, form }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  let body: BodyInit | undefined

  if (token) headers.Authorization = `Bearer ${token}`
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (form) {
    body = new URLSearchParams(form)
  }

  const res = await fetch(`${BASE_URL}${path}`, { method, headers, body })
  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, errorMessage(data, res.statusText))
  return data as T
}

function toQueryString(query: ProductQuery): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export const api = {
  listProducts: (query: ProductQuery = {}) => request<ProductPage>(`/products${toQueryString(query)}`),
  getProduct: (id: number) => request<Product>(`/products/${id}`),
  listCategories: () => request<string[]>('/products/categories'),

  register: (email: string, password: string, full_name?: string) =>
    request<User>('/auth/register', { method: 'POST', json: { email, password, full_name: full_name || null } }),
  // OAuth2 password flow expects form fields, and the email goes in "username"
  login: (email: string, password: string) =>
    request<Token>('/auth/login', { method: 'POST', form: { username: email, password } }),
  me: (token: string) => request<User>('/auth/me', { token }),

  getCart: (token: string) => request<Order>('/cart', { token }),
  addToCart: (token: string, product_id: number, quantity = 1) =>
    request<Order>('/cart/items', { method: 'POST', token, json: { product_id, quantity } }),
  updateCartItem: (token: string, itemId: number, quantity: number) =>
    request<Order>(`/cart/items/${itemId}`, { method: 'PATCH', token, json: { quantity } }),
  removeCartItem: (token: string, itemId: number) =>
    request<Order>(`/cart/items/${itemId}`, { method: 'DELETE', token }),

  listOrders: (token: string) => request<Order[]>('/orders', { token }),
}
