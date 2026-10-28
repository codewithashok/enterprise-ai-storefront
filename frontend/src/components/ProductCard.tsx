import { LoaderCircle, ShoppingBag } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../hooks/useAuth'
import { useCart } from '../hooks/useCart'
import type { Product } from '../types'
import { categoryStyle, formatPrice } from './categoryStyle'

interface ProductCardProps {
  product: Product
  onRequireAuth: () => void
}

export function ProductCard({ product, onRequireAuth }: ProductCardProps) {
  const { user } = useAuth()
  const { add } = useCart()
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { icon: Icon, tile } = categoryStyle(product.category)

  async function handleAdd() {
    if (!user) return onRequireAuth()
    setAdding(true)
    setError(null)
    try {
      await add(product.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add to cart')
    } finally {
      setAdding(false)
    }
  }

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md">
      <div className={`relative grid aspect-[4/3] place-items-center bg-gradient-to-br ${tile}`}>
        <Icon className="size-14" strokeWidth={1.5} />
        {!product.in_stock && (
          <span className="absolute left-3 top-3 rounded-full bg-slate-900/80 px-2.5 py-1 text-xs font-medium text-white">
            Out of stock
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{product.category}</p>
        <h3 className="font-semibold leading-snug">{product.name}</h3>
        <p className="line-clamp-2 text-sm text-slate-600">{product.description}</p>

        <div className="mt-auto flex items-center justify-between pt-3">
          <span className="text-lg font-semibold">{formatPrice(product.price)}</span>
          <button
            onClick={handleAdd}
            disabled={!product.in_stock || adding}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {adding ? <LoaderCircle className="size-4 animate-spin" /> : <ShoppingBag className="size-4" />}
            {product.in_stock ? 'Add' : 'Sold out'}
          </button>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
      </div>
    </article>
  )
}
