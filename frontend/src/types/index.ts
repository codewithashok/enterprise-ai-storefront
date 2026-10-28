// Mirrors backend Pydantic DTOs (app/schemas/*). Keep in sync when those change.

export interface Product {
  id: number
  sku: string
  name: string
  description: string
  category: string
  price: number
  in_stock: boolean
}

export interface ProductPage {
  items: Product[]
  total: number
  limit: number
  offset: number
}

export type ItemState = 'available' | 'all'

export interface ProductQuery {
  category?: string
  min_price?: number
  max_price?: number
  item_state?: ItemState
  limit?: number
  offset?: number
}

export interface User {
  id: string
  email: string
  full_name: string | null
}

export interface Token {
  access_token: string
  token_type: 'bearer'
}

export type OrderStatus = 'cart' | 'awaiting_payment' | 'paid' | 'shipped' | 'delivered' | 'cancelled'

export interface OrderItem {
  id: number
  quantity: number
  unit_price: number
  line_total: number
  product: Pick<Product, 'id' | 'sku' | 'name' | 'category'>
}

export interface Order {
  id: number
  status: OrderStatus
  total_amount: number
  created_at: string
  items: OrderItem[]
  item_count: number
}
