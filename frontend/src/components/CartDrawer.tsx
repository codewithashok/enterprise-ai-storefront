import { LoaderCircle, Minus, Plus, ShoppingCart, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'

import { useAuth } from '../hooks/useAuth'
import { useCart } from '../hooks/useCart'
import type { OrderItem } from '../types'
import { categoryStyle, formatPrice } from './categoryStyle'

interface CartDrawerProps {
  open: boolean
  onClose: () => void
  onRequireAuth: () => void
}

export function CartDrawer({ open, onClose, onRequireAuth }: CartDrawerProps) {
  const { user } = useAuth()
  const { cart, loading } = useCart()

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  const items = cart?.items ?? []

  return (
    <div className={`fixed inset-0 z-40 ${open ? '' : 'pointer-events-none'}`} aria-hidden={!open}>
      <div
        className={`absolute inset-0 bg-slate-900/40 transition-opacity ${open ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />
      <aside
        className={`absolute right-0 top-0 flex h-full w-full max-w-md flex-col bg-white shadow-xl transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
        role="dialog"
        aria-label="Shopping cart"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="text-lg font-semibold">Your cart</h2>
          <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-slate-100" aria-label="Close cart">
            <X className="size-5" />
          </button>
        </div>

        {!user ? (
          <EmptyState message="Sign in to start a cart.">
            <button
              onClick={onRequireAuth}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Sign in
            </button>
          </EmptyState>
        ) : loading && !cart ? (
          <div className="grid flex-1 place-items-center">
            <LoaderCircle className="size-6 animate-spin text-slate-400" />
          </div>
        ) : items.length === 0 ? (
          <EmptyState message="Your cart is empty." />
        ) : (
          <ul className="flex-1 divide-y divide-slate-100 overflow-y-auto px-5">
            {items.map((item) => (
              <CartLine key={item.id} item={item} />
            ))}
          </ul>
        )}

        {user && items.length > 0 && cart && (
          <div className="border-t border-slate-200 px-5 py-4">
            <div className="mb-4 flex justify-between text-base font-semibold">
              <span>Subtotal</span>
              <span>{formatPrice(cart.total_amount)}</span>
            </div>
            <button
              disabled
              title="Checkout runs through the AI assistant with your approval (Phase 3)"
              className="w-full cursor-not-allowed rounded-lg bg-slate-300 px-4 py-3 text-sm font-semibold text-white"
            >
              Checkout (coming soon)
            </button>
          </div>
        )}
      </aside>
    </div>
  )
}

function EmptyState({ message, children }: { message: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center text-slate-500">
      <ShoppingCart className="size-10 text-slate-300" />
      <p>{message}</p>
      {children}
    </div>
  )
}

function CartLine({ item }: { item: OrderItem }) {
  const { setQuantity, remove } = useCart()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { icon: Icon, tile } = categoryStyle(item.product.category)

  async function run(action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setBusy(false)
    }
  }

  const stepper = 'grid size-7 place-items-center rounded-md border border-slate-200 hover:bg-slate-50 disabled:opacity-40'

  return (
    <li className="flex gap-3 py-4">
      <div className={`grid size-16 shrink-0 place-items-center rounded-xl bg-gradient-to-br ${tile}`}>
        <Icon className="size-7" strokeWidth={1.5} />
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <div className="flex justify-between gap-2">
          <p className="text-sm font-medium leading-snug">{item.product.name}</p>
          <p className="text-sm font-semibold">{formatPrice(item.line_total)}</p>
        </div>
        <p className="text-xs text-slate-500">{formatPrice(item.unit_price)} each</p>
        <div className="mt-1 flex items-center gap-2">
          <button
            className={stepper}
            disabled={busy || item.quantity <= 1}
            onClick={() => run(() => setQuantity(item.id, item.quantity - 1))}
            aria-label="Decrease quantity"
          >
            <Minus className="size-3.5" />
          </button>
          <span className="w-6 text-center text-sm tabular-nums">{item.quantity}</span>
          <button
            className={stepper}
            disabled={busy}
            onClick={() => run(() => setQuantity(item.id, item.quantity + 1))}
            aria-label="Increase quantity"
          >
            <Plus className="size-3.5" />
          </button>
          <button
            className="ml-auto rounded-md p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-40"
            disabled={busy}
            onClick={() => run(() => remove(item.id))}
            aria-label="Remove item"
          >
            <Trash2 className="size-4" />
          </button>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
      </div>
    </li>
  )
}
