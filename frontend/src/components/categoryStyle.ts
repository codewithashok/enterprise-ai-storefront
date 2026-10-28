import { CookingPot, Dumbbell, Headphones, Package, Shirt, Tent, type LucideIcon } from 'lucide-react'

interface CategoryStyle {
  icon: LucideIcon
  tile: string
}

const STYLES: Record<string, CategoryStyle> = {
  Electronics: { icon: Headphones, tile: 'from-indigo-100 to-sky-100 text-indigo-600' },
  'Home & Kitchen': { icon: CookingPot, tile: 'from-amber-100 to-orange-100 text-amber-700' },
  Apparel: { icon: Shirt, tile: 'from-rose-100 to-pink-100 text-rose-600' },
  'Sports & Outdoors': { icon: Tent, tile: 'from-emerald-100 to-teal-100 text-emerald-700' },
  'Health & Fitness': { icon: Dumbbell, tile: 'from-violet-100 to-fuchsia-100 text-violet-600' },
}

const FALLBACK: CategoryStyle = { icon: Package, tile: 'from-slate-100 to-slate-200 text-slate-600' }

export function categoryStyle(category: string): CategoryStyle {
  return STYLES[category] ?? FALLBACK
}

export const formatPrice = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
