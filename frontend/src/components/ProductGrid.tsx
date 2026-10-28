import { CircleAlert, LoaderCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

import { api } from '../services/api'
import type { Product, ProductQuery } from '../types'
import { ProductCard } from './ProductCard'

const PAGE_SIZE = 12
const PRICE_CAPS = [undefined, 50, 100, 200] as const

interface ProductGridProps {
  onRequireAuth: () => void
}

export function ProductGrid({ onRequireAuth }: ProductGridProps) {
  const [categories, setCategories] = useState<string[]>([])
  const [category, setCategoryState] = useState<string | undefined>()
  const [maxPrice, setMaxPriceState] = useState<number | undefined>()
  const [includeSoldOut, setIncludeSoldOutState] = useState(false)

  const [products, setProducts] = useState<Product[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.listCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  // Any filter change restarts from page 1 (done in the handler, not an effect, to avoid a wasted fetch)
  function withReset<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value)
      setOffset(0)
    }
  }
  const setCategory = withReset(setCategoryState)
  const setMaxPrice = withReset(setMaxPriceState)
  const setIncludeSoldOut = withReset(setIncludeSoldOutState)

  useEffect(() => {
    const query: ProductQuery = {
      category,
      max_price: maxPrice,
      item_state: includeSoldOut ? 'all' : 'available',
      limit: PAGE_SIZE,
      offset,
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    api
      .listProducts(query)
      .then((page) => {
        if (cancelled) return
        setProducts((prev) => (offset === 0 ? page.items : [...prev, ...page.items]))
        setTotal(page.total)
      })
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Failed to load products'))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [category, maxPrice, includeSoldOut, offset])

  const chip = (active: boolean) =>
    `rounded-full border px-3 py-1.5 text-sm font-medium transition ${
      active ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
    }`

  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex flex-col gap-4">
        <div className="flex flex-wrap gap-2">
          <button className={chip(category === undefined)} onClick={() => setCategory(undefined)}>
            All
          </button>
          {categories.map((c) => (
            <button key={c} className={chip(category === c)} onClick={() => setCategory(c)}>
              {c}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-700">
          <label className="flex items-center gap-2">
            Max price
            <select
              value={maxPrice ?? ''}
              onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : undefined)}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1.5"
            >
              {PRICE_CAPS.map((cap) => (
                <option key={cap ?? 'any'} value={cap ?? ''}>
                  {cap ? `Under $${cap}` : 'Any'}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeSoldOut}
              onChange={(e) => setIncludeSoldOut(e.target.checked)}
              className="size-4 accent-indigo-600"
            />
            Show sold-out items
          </label>
          <span className="ml-auto text-slate-500">{total} products</span>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <CircleAlert className="size-5" /> {error}
        </div>
      )}

      {!error && products.length === 0 && !loading && (
        <p className="py-16 text-center text-slate-500">No products match these filters.</p>
      )}

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} onRequireAuth={onRequireAuth} />
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        {loading ? (
          <LoaderCircle className="size-6 animate-spin text-slate-400" />
        ) : (
          products.length < total && (
            <button
              onClick={() => setOffset(products.length)}
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
            >
              Load more
            </button>
          )
        )}
      </div>
    </section>
  )
}
