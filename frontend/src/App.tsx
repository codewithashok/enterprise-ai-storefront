import { useCallback, useState } from 'react'

import { AuthModal } from './components/AuthModal'
import { CartDrawer } from './components/CartDrawer'
import { Navbar } from './components/Navbar'
import { ProductGrid } from './components/ProductGrid'
import { AuthProvider } from './hooks/useAuth'
import { CartProvider } from './hooks/useCart'

export default function App() {
  const [cartOpen, setCartOpen] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)

  const openAuth = useCallback(() => setAuthOpen(true), [])
  const closeCart = useCallback(() => setCartOpen(false), [])

  return (
    <AuthProvider>
      <CartProvider>
        <Navbar onOpenCart={() => setCartOpen(true)} onOpenAuth={openAuth} />
        <main>
          <div className="mx-auto max-w-6xl px-4 pt-10">
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Shop the collection</h1>
            <p className="mt-2 text-slate-600">Gear for the trail, the kitchen, the gym and your desk.</p>
          </div>
          <ProductGrid onRequireAuth={openAuth} />
        </main>
        <CartDrawer open={cartOpen} onClose={closeCart} onRequireAuth={openAuth} />
        <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
      </CartProvider>
    </AuthProvider>
  )
}
