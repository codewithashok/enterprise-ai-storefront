# Project Learning Notes: Enterprise AI Storefront

---

# Phase 1: Local Data Layer

## Step 1: Let's get Postgres running in Docker

**🎯 Interview takeaway:** A container is an isolated, reproducible box that runs one service (here Postgres + pgvector) the same way on every machine.

| Developer Notes | Casual Explanation |
|---|---|
| Image: `pgvector/pgvector:pg16`, Postgres 16 with the vector plugin already installed.<br>Container name `storefront_db`, data kept in a Docker **volume**.<br>Port mapping **`5433:5432`** = laptop port 5433 → container port 5432.<br>Why 5433? A Windows Postgres 18 was already on 5432 and was secretly answering our app. | Instead of installing a database on your laptop and making a mess, we run it in a little sealed box. Break it? Throw it away, make a new one.<br><br>We hit a sneaky one: *two* databases were listening on the same door (5432), and the wrong one kept picking up. So we gave ours its own door, 5433. |

---

## Step 2: Let's put the code on GitHub

**🎯 Interview takeaway:** `.gitignore` keeps secrets and generated files (like `.env` and `venv/`) out of version control so only real source code is shared.

| Developer Notes | Casual Explanation |
|---|---|
| `.gitignore` excludes `venv/`, `__pycache__/`, `.env`, `.vscode/`.<br>`user.name` / `user.email` set **per repo** (no `--global`) for the right GitHub account.<br>Remote URL includes the username: `https://codewithashok@github.com/...` so Windows picks the right login. | GitHub is the cloud backup + history of your code.<br><br>`.gitignore` is the "don't pack this" list: the huge stuff you can rebuild and, most importantly, your passwords. You had two GitHub accounts, so we told Git exactly which one to use for this project. |

---

## Step 3: Let's create one place for all settings

**🎯 Interview takeaway:** A typed settings object loads config from environment variables once (singleton) and fails fast on bad or missing values.

| Developer Notes | Casual Explanation |
|---|---|
| `app/core/config.py` → `Settings(BaseSettings)` (pydantic-settings).<br>Safe defaults in code; **real secrets in `.env`** (gitignored); `.env.example` = blank template.<br>`SecretStr` hides keys in logs (`**********`).<br>`@lru_cache` on `get_settings()` → built once → **Singleton pattern**. | Think of it as the app's control panel. Every setting (DB address, API keys) lives in one spot, with rules about what's allowed.<br><br>Passwords stay in a private `.env` file that never goes online. Typo in a setting? The app refuses to start right away instead of blowing up later in front of a customer. |

---

## Step 4: Let's create the database connection

**🎯 Interview takeaway:** Connection pooling keeps a set of open database connections ready and reuses them, because opening a new connection for every request is slow and can overwhelm the database.

| Developer Notes | Casual Explanation |
|---|---|
| `app/db/session.py`.<br>**Engine** = created once at module level → owns the **connection pool** (Singleton + Object Pool).<br>`pool_size=5, max_overflow=5`, kept small for AWS RDS limits.<br>`pool_pre_ping` = check the connection is alive before using it.<br>**Session factory** (`async_sessionmaker`) → one session per request = **Unit of Work**.<br>`get_db()` = FastAPI **dependency**: hands out a session, always closes it after. | Opening a fresh line to the database every time is like dialling a call centre and waiting through the menu for every question. A pool keeps a few lines already open and passes them around.<br><br>Each request borrows a line, does its thing, and gives it back, even if something crashed. Nobody hogs it, nothing leaks. |

---

## Step 5: Let's design our tables

**🎯 Interview takeaway:** An ORM maps Python classes to database tables, and a vector column with an HNSW index enables fast "find similar meaning" search.

| Developer Notes | Casual Explanation |
|---|---|
| `app/db/models.py`: `User`, `Product`, `Order`, `OrderItem`.<br>`Mapped[str]` = NOT NULL, `Mapped[str \| None]` = nullable.<br>`TimestampMixin` adds `created_at`/`updated_at` everywhere.<br>Cart = an `Order` with status `cart` (no separate cart table).<br>Hidden columns: `cost_price`, `is_active`, `is_deleted`, never exposed to API/AI.<br>`embedding Vector(1536)` + **HNSW index** (cosine).<br>`unit_price` snapshot on order items. | We describe our tables as Python classes and the tool writes the SQL for us.<br><br>Products get a secret "meaning fingerprint" (1536 numbers) so the AI can later find "something warm for skiing" even if those exact words aren't in the name.<br><br>Some columns are staff-only, like what we paid for an item; customers and the AI never see those. And your order remembers the price you paid, even if it changes tomorrow. |

---

## Step 6: Let's create the tables in the database

**🎯 Interview takeaway:** An idempotent setup script produces the same result no matter how many times you run it.

| Developer Notes | Casual Explanation |
|---|---|
| `scripts/init_db.py`, run with `python -m scripts.init_db`.<br>Step 1: `CREATE EXTENSION IF NOT EXISTS vector` (must come first).<br>Step 2: `Base.metadata.create_all` creates missing tables only.<br>`engine.begin()` = one transaction, auto commit or auto rollback.<br>`--drop` flag to wipe and rebuild while designing.<br>Later: replace with **Alembic migrations**. | We had blueprints; now we actually build the rooms.<br><br>First we switch on the vector plugin, then create the tables. Run it twice? No drama, it skips what already exists. Everything happens as one package deal: either it all works, or nothing changes. |

---

## Step 7: Let's fill the store with products (and their AI fingerprints)

**🎯 Interview takeaway:** Embeddings turn text into vectors so similar meanings sit close together, and cosine similarity measures that closeness.

| Developer Notes | Casual Explanation |
|---|---|
| `scripts/seed_catalog.py`: 30 products, 5 categories.<br>Embed `name + category + description` with `text-embedding-3-small`.<br>**One batched API call** for all 30 (≈ $0.00004).<br>**Upsert** by SKU (`ON CONFLICT DO UPDATE`), safe to re-run.<br>`async with AsyncOpenAI()` closes the client (fixed "Event loop is closed").<br>Test data traps: 3 out-of-stock + 1 discontinued (`HK-006`).<br>Check: earbuds → speaker 0.42, watch 0.42, then weak matches. | We stocked the shelves and asked OpenAI to give each product its "meaning fingerprint", all in one go instead of 30 separate trips.<br><br>Search for things like earbuds and you get a speaker and a fitness watch: nice. But it also dragged in trekking poles 🙃. Vector search *always* finds something, so later we'll add filters (price, stock, category). That combo is called **hybrid search**. |

---

# Phase 2: Backend REST Core

## Step 8: Let's start the API server

**🎯 Interview takeaway:** A lifespan hook runs setup once at startup and cleanup once at shutdown, so shared resources are created once and closed cleanly.

| Developer Notes | Casual Explanation |
|---|---|
| `app/main.py` → `FastAPI(lifespan=lifespan)`.<br>Before `yield`: DB check (`SELECT 1`, fail fast) + one shared OpenAI client on `app.state`.<br>After `yield`: close OpenAI client, `engine.dispose()`.<br>**CORS** allows the React dev server (`localhost:5173`).<br>`GET /api/health` → checks DB, returns status.<br>All routes start with `/api` (CloudFront routes `/api/*` to the backend later).<br>Run: `uvicorn app.main:app --reload --port 8000`. | This is the shop opening and closing. Open: check the database is answering, set up the AI phone line once. Close: hang up properly, lock the doors.<br><br>CORS is the bouncer: the browser won't let our React site talk to the API unless the API says "yep, they're on the list." Health check = "you alive?" "yep." |

---

## Step 9: Let's lock passwords and hand out login tokens

**🎯 Interview takeaway:** Passwords are stored as slow, salted one-way hashes (bcrypt), and a JWT is a signed token proving who you are without the server keeping session state.

| Developer Notes | Casual Explanation |
|---|---|
| `app/core/security.py`.<br>Swapped `passlib`/`python-jose` → `bcrypt`/`PyJWT` (maintained).<br>`hash_password` / `verify_password` with bcrypt (salt built into the hash).<br>`create_access_token` → JWT with only `sub` (user id), `iat`, `exp` (60 min).<br>`JWT_SECRET_KEY` **required, no default**.<br>`get_current_user` dependency: verify token → load user → reject inactive.<br>`CurrentUser` alias = protect any route in one line. | We never keep your real password, just a scrambled version that can't be unscrambled. Even we can't read it.<br><br>When you log in, you get a wristband (JWT). Show it on each visit and you're in. Anyone can *read* the wristband, but nobody can *fake* one without our secret stamp. And no stamp = the app won't even start. |

---

## Step 10: Let's define what data comes in and goes out

**🎯 Interview takeaway:** A DTO is a separate data shape for API input/output that validates incoming data and hides internal fields from responses.

| Developer Notes | Casual Explanation |
|---|---|
| `app/schemas/auth.py`.<br>`UserCreate` (input): `EmailStr`, password 8–72 chars, email lowercased.<br>Extra check: password ≤ **72 bytes** (bcrypt's real limit; emojis are multi-byte).<br>`UserRead` (output): `id`, `email`, `full_name` only, **no hash**.<br>`from_attributes=True` → convert a DB row straight into the DTO.<br>Bad input → automatic **422** with per-field errors. | It's the form at the front desk. Wrong email format or too-short password? Bounced before it gets anywhere near the database.<br><br>And on the way out, we only hand back the safe bits. Even if the code accidentally grabs the whole user record, the password hash gets stripped off at the door. |

---

## Step 11: Let's build sign-up, login and "who am I"

**🎯 Interview takeaway:** Secure login returns the same error and takes the same time for every failure, so attackers can't tell which emails are registered.

| Developer Notes | Casual Explanation |
|---|---|
| `app/api/v1/auth.py` → `APIRouter(prefix="/auth")`, mounted at `/api/v1`.<br>`POST /register` → 201; duplicate email → DB unique index → **409**.<br>`POST /login` → OAuth2 form (`username`, `password`) → token. Swagger "Authorize" works.<br>`GET /me` → `user: CurrentUser`; no token → **401**.<br>`run_in_threadpool` for bcrypt, so slow CPU work doesn't freeze the async server.<br>`_DUMMY_HASH` = same timing for unknown emails.<br>✅ Tested: register → login → `/me` 200, no token 401. | Sign up, log in, check who you are: the basics.<br><br>Hashing is slow on purpose, so we do it in a side room so the shop doesn't freeze for everyone else.<br><br>A wrong login always says "email or password is wrong" and takes the same time, so a hacker can't fish for which emails have accounts. And if two people sign up with the same email at the exact same moment, the database itself says "nope" to the second one. |
