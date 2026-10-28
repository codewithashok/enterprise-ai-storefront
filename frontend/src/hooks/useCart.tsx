import { createContext, use, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { api } from '../services/api'
import type { Order } from '../types'
import { useAuth } from './useAuth'

interface CartContextValue {
  cart: Order | null
  loading: boolean
  add: (productId: number, quantity?: number) => Promise<void>
  setQuantity: (itemId: number, quantity: number) => Promise<void>
  remove: (itemId: number) => Promise<void>
  refresh: () => Promise<void>
}

const CartContext = createContext<CartContextValue | null>(null)

// The server owns the cart: every mutation returns the full, recalculated cart,
// so the client never computes totals or stock rules itself.
export function CartProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth()
  const [serverCart, setCart] = useState<Order | null>(null)
  const [loading, setLoading] = useState(false)
  const cart = token ? serverCart : null // signed out means no cart: derived, not synced in an effect

  const refresh = useCallback(async () => {
    if (!token) return
    setCart(await api.getCart(token))
  }, [token])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    setLoading(true)
    api
      .getCart(token)
      .then((c) => !cancelled && setCart(c))
      .catch(() => !cancelled && setCart(null))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [token])

  const requireToken = useCallback(() => {
    if (!token) throw new Error('Sign in to use the cart')
    return token
  }, [token])

  const add = useCallback(
    async (productId: number, quantity = 1) => setCart(await api.addToCart(requireToken(), productId, quantity)),
    [requireToken],
  )
  const setQuantity = useCallback(
    async (itemId: number, quantity: number) => setCart(await api.updateCartItem(requireToken(), itemId, quantity)),
    [requireToken],
  )
  const remove = useCallback(
    async (itemId: number) => setCart(await api.removeCartItem(requireToken(), itemId)),
    [requireToken],
  )

  const value = useMemo(
    () => ({ cart, loading, add, setQuantity, remove, refresh }),
    [cart, loading, add, setQuantity, remove, refresh],
  )
  return <CartContext value={value}>{children}</CartContext>
}

export function useCart(): CartContextValue {
  const ctx = use(CartContext)
  if (!ctx) throw new Error('useCart must be used inside <CartProvider>')
  return ctx
}
