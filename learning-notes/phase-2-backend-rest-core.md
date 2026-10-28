# Phase 2: Backend REST Core

---

## Step 1: Let's start the API server

**🎯 Interview takeaway:** A lifespan hook runs setup once at startup and cleanup once at shutdown, so shared resources are created once and closed cleanly.

| Developer Notes | Casual Explanation |
|---|---|
| `app/main.py` → `FastAPI(lifespan=lifespan)`.<br>Before `yield`: DB check (`SELECT 1`, fail fast) + one shared OpenAI client on `app.state`.<br>After `yield`: close OpenAI client, `engine.dispose()`.<br>**CORS** allows the React dev server (`localhost:5173`).<br>`GET /api/health` → checks DB, returns status.<br>All routes start with `/api` (CloudFront routes `/api/*` to the backend later).<br>Run: `uvicorn app.main:app --reload --port 8000`. | This is the shop opening and closing. Open: check the database is answering, set up the AI phone line once. Close: hang up properly, lock the doors.<br><br>CORS is the bouncer: the browser won't let our React site talk to the API unless the API says "yep, they're on the list." Health check = "you alive?" "yep."<br><br>**Things we used:**<br>• **FastAPI**: it's like Express.js, but with built-in types and validation. It's a web framework; it's used to build the API.<br>• **uvicorn**: it's like `node server.js` / the Vite dev server. It's an ASGI server; it's used to actually run FastAPI and listen on a port. `--reload` = auto-restart on save.<br>• **`lifespan` (`@asynccontextmanager`)**: it's like `useEffect(() => { setup; return cleanup }, [])` for the whole server. It's used to run startup and shutdown code.<br>• **`app.state`**: it's like a top-level React Context value. It's used to share one object (the OpenAI client) across the whole app.<br>• **`CORSMiddleware`**: it's like the `cors` package in Express. It's middleware; it's used to tell browsers which websites may call the API.<br>• **Swagger `/docs`**: it's like an auto-generated Postman. It's used to see and try every endpoint in the browser. |

---

## Step 2: Let's lock passwords and hand out login tokens

**🎯 Interview takeaway:** Passwords are stored as slow, salted one-way hashes (bcrypt), and a JWT is a signed token proving who you are without the server keeping session state.

| Developer Notes | Casual Explanation |
|---|---|
| `app/core/security.py`.<br>Swapped `passlib`/`python-jose` → `bcrypt`/`PyJWT` (maintained).<br>`hash_password` / `verify_password` with bcrypt (salt built into the hash).<br>`create_access_token` → JWT with only `sub` (user id), `iat`, `exp` (60 min).<br>`JWT_SECRET_KEY` **required, no default**.<br>`get_current_user` dependency: verify token → load user → reject inactive.<br>`CurrentUser` alias = protect any route in one line. | We never keep your real password, just a scrambled version that can't be unscrambled. Even we can't read it.<br><br>When you log in, you get a wristband (JWT). Show it on each visit and you're in. Anyone can *read* the wristband, but nobody can *fake* one without our secret stamp. And no stamp = the app won't even start.<br><br>**Things we used:**<br>• **bcrypt**: it's like `bcryptjs` in Node. It's a password-hashing library; it's used to scramble passwords slowly on purpose so hackers can't guess fast.<br>• **PyJWT**: it's like `jsonwebtoken` in Node. It's used to create and verify login tokens.<br>• **JWT**: it's like a signed concert wristband. It's a token (`header.payload.signature`); it's used to prove who you are on every request.<br>• **`OAuth2PasswordBearer`**: it's like an axios interceptor, in reverse. It's used to pull the `Authorization: Bearer <token>` header out of each request.<br>• **`Depends`**: it's like `useContext`. It's dependency injection; it's used to say "give me the logged-in user" and FastAPI provides it.<br>• **`Annotated`**: it's like a TS type alias with extra info attached. It's used to create reusable shortcuts like `CurrentUser`.<br>• **`HTTPException`**: it's like `res.status(401).json(...)` in Express. It's used to stop and send an error response. |

---

## Step 3: Let's define what data comes in and goes out

**🎯 Interview takeaway:** A DTO is a separate data shape for API input/output that validates incoming data and hides internal fields from responses.

| Developer Notes | Casual Explanation |
|---|---|
| `app/schemas/auth.py`.<br>`UserCreate` (input): `EmailStr`, password 8–72 chars, email lowercased.<br>Extra check: password ≤ **72 bytes** (bcrypt's real limit; emojis are multi-byte).<br>`UserRead` (output): `id`, `email`, `full_name` only, **no hash**.<br>`from_attributes=True` → convert a DB row straight into the DTO.<br>Bad input → automatic **422** with per-field errors. | It's the form at the front desk. Wrong email format or too-short password? Bounced before it gets anywhere near the database.<br><br>And on the way out, we only hand back the safe bits. Even if the code accidentally grabs the whole user record, the password hash gets stripped off at the door.<br><br>**Things we used:**<br>• **Pydantic `BaseModel`**: it's like a Zod schema. It's a data class; it's used to define and validate the shape of data.<br>• **`EmailStr`**: it's like `z.string().email()`. It's used to accept only valid emails (needs the `email-validator` package).<br>• **`Field(min_length=8)`**: it's like `z.string().min(8)`. It's used to add rules to a single field.<br>• **`@field_validator`**: it's like Zod's `.refine()` / `.transform()`. It's used for custom checks or cleanup (like lowercasing email).<br>• **`ConfigDict(from_attributes=True)`**: it's like mapping a class instance into a plain object. It's used to build the DTO straight from a DB row.<br>• **`response_model`**: it's like returning `pick(user, ['id','email'])`. It's used to filter what the API sends back. |

---

## Step 4: Let's build sign-up, login and "who am I"

**🎯 Interview takeaway:** Secure login returns the same error and takes the same time for every failure, so attackers can't tell which emails are registered.

| Developer Notes | Casual Explanation |
|---|---|
| `app/api/v1/auth.py` → `APIRouter(prefix="/auth")`, mounted at `/api/v1`.<br>`POST /register` → 201; duplicate email → DB unique index → **409**.<br>`POST /login` → OAuth2 form (`username`, `password`) → token. Swagger "Authorize" works.<br>`GET /me` → `user: CurrentUser`; no token → **401**.<br>`run_in_threadpool` for bcrypt, so slow CPU work doesn't freeze the async server.<br>`_DUMMY_HASH` = same timing for unknown emails.<br>✅ Tested: register → login → `/me` 200, no token 401. | Sign up, log in, check who you are: the basics.<br><br>Hashing is slow on purpose, so we do it in a side room so the shop doesn't freeze for everyone else.<br><br>A wrong login always says "email or password is wrong" and takes the same time, so a hacker can't fish for which emails have accounts. And if two people sign up with the same email at the exact same moment, the database itself says "nope" to the second one.<br><br>**Things we used:**<br>• **`APIRouter`**: it's like `express.Router()`. It's used to group related routes in their own file.<br>• **`include_router`**: it's like `app.use('/api/v1', router)`. It's used to plug a router into the main app with a URL prefix.<br>• **`OAuth2PasswordRequestForm`**: it's like reading `req.body` from a login form. It's used to accept `username` + `password` as form data (OAuth2 standard).<br>• **`python-multipart`**: it's like `multer` / body parsers in Express. It's used to read form data.<br>• **`run_in_threadpool`**: it's like a Web Worker. It's used to move heavy CPU work off the main event loop.<br>• **`IntegrityError`**: it's the DB saying "that breaks a rule" (like a duplicate email). It's used to catch it and return a friendly 409.<br>• **`select()` + `db.scalar()`**: it's like Prisma's `findFirst({ where })`. It's used to fetch one row from the database. |

---

## Step 5: Let's define the public product shape and filters

**🎯 Interview takeaway:** An alias layer exposes simple business terms (like `available`) instead of raw database flags, so clients (and later the LLM) can only ask for safe, predefined views of the data.

| Developer Notes | Casual Explanation |
|---|---|
| `app/schemas/catalog.py`.<br>`ProductRead`: only public fields; `cost_price`, `is_active`, `is_deleted`, `embedding` aren't declared, so they can't leak.<br>`inventory_count` read but `exclude=True`; shoppers get computed `in_stock: bool`.<br>`Money` type = `Decimal` in Python, number in JSON.<br>`ItemState = Literal["available", "all"]`, the alias layer.<br>`ProductQuery`: filters + pagination, cross-field check `min_price <= max_price`.<br>`ProductPage`: `items`, `total`, `limit`, `offset`.<br>✅ Tested: internal fields stripped, bad price range → error, `item_state='deleted'` → rejected. | This is the shop window. Customers see name, price, "in stock" and that's it, not what we paid or how many are in the back room.<br><br>Filters are a menu, not a free-text box: you can pick "available" or "all", and there's simply no option for "show me deleted stuff". Later the AI gets the same menu, so it physically can't ask for secret data.<br><br>Prices use exact decimals, because computers are weirdly bad at money with normal numbers (`0.1 + 0.2 = 0.30000000000000004` 😬).<br><br>**Things we used:**<br>• **`Literal["available", "all"]`**: it's like a TS union type `'available' \| 'all'`. It's used to allow only those exact values.<br>• **`Decimal`**: it's like using a money library (`dinero.js`) instead of plain numbers. It's used for exact money maths.<br>• **`PlainSerializer`**: it's like a custom `toJSON()`. It's used to change how a value looks when sent as JSON.<br>• **`Field(exclude=True)`**: it's like reading a prop but not passing it down. It's used to use a value internally but leave it out of the response.<br>• **`@computed_field`**: it's like a derived value with `useMemo`. It's used to add a calculated field (`in_stock`) to the output.<br>• **`@model_validator(mode="after")`**: it's like Zod's `.superRefine()`. It's used for rules that compare several fields together. |
