import { LogOut, ShoppingCart, Store, User as UserIcon } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'
import { useCart } from '../hooks/useCart'

interface NavbarProps {
  onOpenCart: () => void
  onOpenAuth: () => void
}

export function Navbar({ onOpenCart, onOpenAuth }: NavbarProps) {
  const { user, logout } = useAuth()
  const { cart } = useCart()
  const count = cart?.item_count ?? 0

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <a href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <Store className="size-6 text-indigo-600" />
          <span>Storefront</span>
        </a>

        <div className="flex items-center gap-2">
          {user ? (
            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 text-sm text-slate-600 sm:flex">
                <UserIcon className="size-4" />
                {user.full_name || user.email}
              </span>
              <button
                onClick={logout}
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut className="size-5" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              Sign in
            </button>
          )}

          <button
            onClick={onOpenCart}
            className="relative rounded-lg p-2 text-slate-700 hover:bg-slate-100"
            aria-label={`Open cart (${count} items)`}
          >
            <ShoppingCart className="size-6" />
            {count > 0 && (
              <span className="absolute -right-0.5 -top-0.5 grid min-w-5 place-items-center rounded-full bg-indigo-600 px-1 text-xs font-semibold text-white">
                {count}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
