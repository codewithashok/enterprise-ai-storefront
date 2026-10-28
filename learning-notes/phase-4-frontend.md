# Phase 4: Frontend (React 19 + TypeScript + Tailwind)

> Steps 1–3 are the classic storefront (built before the AI work). The AI chat drawer and the payment approval card come after Phase 3.

---

## Step 1: Let's scaffold the app and wire it to the backend

**🎯 Interview takeaway:** A dev-server proxy makes the browser call the API on the same origin, which avoids CORS in development and mirrors how a CDN routes `/api/*` to the backend in production.

| Developer Notes | Casual Explanation |
|---|---|
| `npm create vite@latest frontend -- --template react-ts` → React 19.3, Vite 8, TypeScript 7.<br>Tailwind CSS 4 via `@tailwindcss/vite`: just `@import "tailwindcss"` in `index.css`, no `tailwind.config.js` needed.<br>`vite.config.ts` proxy: `/api` → `http://localhost:8000`.<br>`types/index.ts` mirrors the backend Pydantic DTOs (`Product`, `Order`, `User`…).<br>`services/api.ts`: one `request<T>()` wrapper. It adds the Bearer token, sends JSON or form data, and turns FastAPI's `{detail}` errors into an `ApiError`.<br>Login sends **form data** with the email in `username` (OAuth2 rule). | We set up the shop's front room and ran a private hallway from it to the back office (the API).<br><br>Because the website and API look like they live at the same address, the browser's bouncer (CORS) doesn't even get involved, and in production CloudFront does the exact same trick.<br><br>All talking to the backend goes through one helper, so the login token and error handling are written once, not copy-pasted into every component.<br><br>**Things we used:**<br>• **Vite**: it's the dev server + bundler you already know. It's used to run the app with instant reloads and build it for production.<br>• **Vite `server.proxy`**: it's like a mini reverse proxy. It's used to forward `/api` calls from port 5173 to the backend on 8000.<br>• **Tailwind v4 (`@tailwindcss/vite`)**: it's the utility-class CSS you know, now config-free. It's used to style everything with classes.<br>• **`fetch` wrapper (`request<T>`)**: it's like a tiny axios. It's used to centralise headers, JSON parsing and errors.<br>• **`URLSearchParams`**: it's used to build query strings and send form-encoded bodies (the login form). |

---

## Step 2: Let's manage login and cart state

**🎯 Interview takeaway:** Treat the server as the source of truth for important state (like the cart), so the client renders what the API returns instead of re-implementing business rules.

| Developer Notes | Casual Explanation |
|---|---|
| `hooks/useAuth.tsx`: `AuthProvider` + `useAuth()`. JWT kept in `localStorage`, restored on load via `/auth/me`; a 401 logs out. `register` registers, then logs in.<br>`hooks/useCart.tsx`: `CartProvider` + `useCart()`. Every action (`add`, `setQuantity`, `remove`) calls the API and stores the **full cart it returns**, so there's no client-side total maths.<br>Signed out → cart is **derived** as `null` (not cleared in an effect).<br>Effects use a `cancelled` flag so stale responses never overwrite newer state.<br>React 19 bits: `<Context value>` (no `.Provider`) and `use(Context)`.<br>Note: `localStorage` tokens are fine for dev; production hardening = short expiry or an httpOnly cookie. | Two shared "brains" for the whole app: one remembers who you are, the other holds your basket.<br><br>The basket brain never does its own maths. It asks the server "add this" and the server hands back the whole updated basket with totals and stock rules already applied. One source of truth, zero "the badge says 3 but the cart says 2" bugs.<br><br>If your login wristband expired, the app notices on reload and quietly signs you out.<br><br>**Things we used:**<br>• **Context + custom hook**: it's the React pattern you know. It's used to share auth and cart state without prop drilling.<br>• **`use(Context)`**: React 19's new way to read context (like `useContext`, but can be used conditionally).<br>• **`useMemo` / `useCallback`**: used to keep the context value stable so consumers don't re-render for no reason.<br>• **Cancelled flag in effects**: it's like an `AbortController` lite. It's used to ignore responses that arrive after the component moved on.<br>• **Derived state**: it's used to compute values during render (`token ? cart : null`) instead of syncing them with extra effects. |

---

## Step 3: Let's build the storefront UI

**🎯 Interview takeaway:** Keep filters and pagination in the URL/query layer of the API and let the UI just send parameters, so the frontend stays thin and the same rules apply to every client.

| Developer Notes | Casual Explanation |
|---|---|
| `Navbar`: logo, sign in/out, cart button with live item-count badge.<br>`ProductGrid`: category chips, "Under $X" select, "Show sold-out items" toggle (→ `item_state=all`), "Load more" pagination (`offset`). Filter changes reset the page **in the handler**, not in an effect (avoids a wasted fetch).<br>`ProductCard`: category-coloured tile + Lucide icon (no product images yet), price, Add button; not signed in → opens login; inline error on 409 stock limits.<br>`CartDrawer`: slide-over, quantity steppers, remove, subtotal from server, Escape/overlay closes. Checkout button disabled until the AI checkout (Phase 3).<br>`AuthModal`: Sign in / Register tabs, shows API error messages.<br>✅ Verified: `tsc` + build clean; through the Vite proxy, products, register, login and add-to-cart all work. | The actual shop floor: browse by category, filter by price, flip a switch to see sold-out stuff, add things to your basket and tweak quantities in a slide-out panel.<br><br>The UI is deliberately "dumb": it just sends choices like "Apparel, under $100" to the server and shows what comes back. All the real rules (what's hidden, what's in stock, what things cost) live in the backend, which is exactly what the AI will rely on later.<br><br>**Things we used:**<br>• **Lucide React**: it's an icon library. It's used for every icon (cart, category tiles, spinners).<br>• **Tailwind transitions (`translate-x-full`)**: used to slide the cart drawer in and out with pure CSS.<br>• **`Intl.NumberFormat`**: it's the built-in way to format money (`$149.99`).<br>• **Controlled inputs + `FormEvent`**: standard React forms, used for the login/register modal.<br>• **oxlint**: it's a super-fast Rust linter (an ESLint alternative). It's used to catch React mistakes like setting state inside effects. |
