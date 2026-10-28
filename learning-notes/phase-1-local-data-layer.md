# Phase 1: Local Data Layer

---

## Step 1: Let's get Postgres running in Docker

**🎯 Interview takeaway:** A container is an isolated, reproducible box that runs one service (here Postgres + pgvector) the same way on every machine.

| Developer Notes | Casual Explanation |
|---|---|
| Image: `pgvector/pgvector:pg16`, Postgres 16 with the vector plugin already installed.<br>Container name `storefront_db`, data kept in a Docker **volume**.<br>Port mapping **`5433:5432`** = laptop port 5433 → container port 5432.<br>Why 5433? A Windows Postgres 18 was already on 5432 and was secretly answering our app. | Instead of installing a database on your laptop and making a mess, we run it in a little sealed box. Break it? Throw it away, make a new one.<br><br>We hit a sneaky one: *two* databases were listening on the same door (5432), and the wrong one kept picking up. So we gave ours its own door, 5433.<br><br>**Things we used:**<br>• **Docker**: it's like CodeSandbox for servers. Docker is a container tool; it's used to run apps in isolated boxes that behave the same on every machine.<br>• **docker-compose.yml**: it's like `package.json` scripts, but for containers. It's a config file; it's used to describe which containers to run and how (`docker compose up -d`).<br>• **Volume**: it's like `localStorage` for the container. It's a storage folder; it's used to keep DB data alive when the container restarts.<br>• **Port mapping**: it's like Vite moving to 5174 when 5173 is busy. It's used to connect a laptop port to a port inside the container. |

---

## Step 2: Let's put the code on GitHub

**🎯 Interview takeaway:** `.gitignore` keeps secrets and generated files (like `.env` and `venv/`) out of version control so only real source code is shared.

| Developer Notes | Casual Explanation |
|---|---|
| `.gitignore` excludes `venv/`, `__pycache__/`, `.env`, `.vscode/`.<br>`user.name` / `user.email` set **per repo** (no `--global`) for the right GitHub account.<br>Remote URL includes the username: `https://codewithashok@github.com/...` so Windows picks the right login. | GitHub is the cloud backup + history of your code.<br><br>`.gitignore` is the "don't pack this" list: the huge stuff you can rebuild and, most importantly, your passwords. You had two GitHub accounts, so we told Git exactly which one to use for this project.<br><br>**Things we used:**<br>• **venv**: it's like `node_modules`. It's a virtual environment; it's used to install Python packages for this project only.<br>• **`__pycache__`**: it's like Vite's `.vite` cache folder. It's auto-generated; it's used to store compiled Python so it loads faster.<br>• **`__init__.py`**: it's like an `index.ts` that marks a folder as importable. It's used to turn a folder into a Python package.<br>• **Git Credential Manager**: it's like your browser's saved passwords, but for Git. It's used to remember which GitHub login to use. |

---

## Step 3: Let's create one place for all settings

**🎯 Interview takeaway:** A typed settings object loads config from environment variables once (singleton) and fails fast on bad or missing values.

| Developer Notes | Casual Explanation |
|---|---|
| `app/core/config.py` → `Settings(BaseSettings)`.<br>Safe defaults in code; **real secrets in `.env`** (gitignored); `.env.example` = blank template.<br>`SecretStr` hides keys in logs (`**********`).<br>`@lru_cache` on `get_settings()` → built once → **Singleton pattern**.<br>`DATABASE_URL` is a computed `@property`. | Think of it as the app's control panel. Every setting (DB address, API keys) lives in one spot, with rules about what's allowed.<br><br>Passwords stay in a private `.env` file that never goes online. Typo in a setting? The app refuses to start right away instead of blowing up later in front of a customer.<br><br>**Things we used:**<br>• **pydantic-settings (`BaseSettings`)**: it's like a Zod schema wrapped around `import.meta.env`. It's a settings class; it's used to read env vars and check their types.<br>• **`.env` file**: it's like `.env.local` in Vite. It's a private file; it's used to store secrets on your machine only.<br>• **`SecretStr`**: it's like `<input type="password">`. It's a special string type; it's used to show `**********` instead of the real value when printed.<br>• **`lru_cache`**: it's like `useMemo` in React. `lru_cache` is a decorator; it's used to remember a function's result so the next call returns the saved answer instead of running again.<br>• **Decorator (`@something`)**: it's like a Higher-Order Component (HOC). It's a wrapper; it's used to add extra behaviour to a function without changing its code.<br>• **`@property`**: it's like a JS `get` getter or a derived value. It's used to compute a value (like the DB URL) from other fields when you read it. |

---

## Step 4: Let's create the database connection

**🎯 Interview takeaway:** Connection pooling keeps a set of open database connections ready and reuses them, because opening a new connection for every request is slow and can overwhelm the database.

| Developer Notes | Casual Explanation |
|---|---|
| `app/db/session.py`.<br>**Engine** = created once at module level → owns the **connection pool** (Singleton + Object Pool).<br>`pool_size=5, max_overflow=5`, kept small for AWS RDS limits.<br>`pool_pre_ping` = check the connection is alive before using it.<br>**Session factory** (`async_sessionmaker`) → one session per request = **Unit of Work**.<br>`get_db()` = FastAPI **dependency**: hands out a session, always closes it after. | Opening a fresh line to the database every time is like dialling a call centre and waiting through the menu for every question. A pool keeps a few lines already open and passes them around.<br><br>Each request borrows a line, does its thing, and gives it back, even if something crashed. Nobody hogs it, nothing leaks.<br><br>**Things we used:**<br>• **SQLAlchemy**: it's like Prisma or TypeORM. It's an ORM; it's used to talk to the database with Python instead of raw SQL.<br>• **asyncpg**: it's like the `pg` package in Node. It's a database driver; it's used to actually send queries to Postgres, asynchronously.<br>• **`create_async_engine`**: it's like creating one `axios.create()` instance for the whole app. It's used to set up the shared connection pool.<br>• **`async_sessionmaker`**: it's like a factory function `createSession()`. It's used to make a fresh session with the same settings every time.<br>• **`AsyncSession`**: it's like a shopping basket. It's a unit of work; it's used to collect changes and save them all at once (commit) or drop them all (rollback).<br>• **`async` / `await`**: same as in JavaScript. It's used to wait for slow stuff (DB, network) without freezing everything else.<br>• **`yield` in `get_db`**: it's like the cleanup `return` in `useEffect`. It's used to hand the session over, then run the "close it" code afterwards. |

---

## Step 5: Let's design our tables

**🎯 Interview takeaway:** An ORM maps Python classes to database tables, and a vector column with an HNSW index enables fast "find similar meaning" search.

| Developer Notes | Casual Explanation |
|---|---|
| `app/db/models.py`: `User`, `Product`, `Order`, `OrderItem`.<br>`Mapped[str]` = NOT NULL, `Mapped[str \| None]` = nullable.<br>`TimestampMixin` adds `created_at`/`updated_at` everywhere.<br>Cart = an `Order` with status `cart` (no separate cart table).<br>Hidden columns: `cost_price`, `is_active`, `is_deleted`, never exposed to API/AI.<br>`embedding Vector(1536)` + **HNSW index** (cosine).<br>`unit_price` snapshot on order items. | We describe our tables as Python classes and the tool writes the SQL for us.<br><br>Products get a secret "meaning fingerprint" (1536 numbers) so the AI can later find "something warm for skiing" even if those exact words aren't in the name.<br><br>Some columns are staff-only, like what we paid for an item; customers and the AI never see those. And your order remembers the price you paid, even if it changes tomorrow.<br><br>**Things we used:**<br>• **`DeclarativeBase`**: it's like a base class every model `extends`. It's used to register all tables in one place.<br>• **`Mapped[...]` + `mapped_column`**: it's like a TypeScript `interface` that also creates the DB column. It's used to define column name, type and rules.<br>• **`relationship()`**: it's like a nested object in an interface (`order.items`). It's used to jump between linked tables without writing JOINs.<br>• **`ForeignKey`**: it's like an ID reference (`userId`). It's used to link one table's row to another's.<br>• **Mixin**: it's like spreading a shared object `{...timestamps}`. It's a small reusable class; it's used to add the same fields to many models.<br>• **`enum.Enum`**: it's like a TS union type `'cart' \| 'paid'`. It's used to allow only a fixed set of values.<br>• **pgvector `Vector(1536)`**: it's like an array column `number[]` with superpowers. It's used to store embeddings and search by similarity.<br>• **HNSW index**: it's like a search index for meaning. It's used to find the nearest vectors fast without checking every row. |

---

## Step 6: Let's create the tables in the database

**🎯 Interview takeaway:** An idempotent setup script produces the same result no matter how many times you run it.

| Developer Notes | Casual Explanation |
|---|---|
| `scripts/init_db.py`, run with `python -m scripts.init_db`.<br>Step 1: `CREATE EXTENSION IF NOT EXISTS vector` (must come first).<br>Step 2: `Base.metadata.create_all` creates missing tables only.<br>`engine.begin()` = one transaction, auto commit or auto rollback.<br>`--drop` flag to wipe and rebuild while designing.<br>Later: replace with **Alembic migrations**. | We had blueprints; now we actually build the rooms.<br><br>First we switch on the vector plugin, then create the tables. Run it twice? No drama, it skips what already exists. Everything happens as one package deal: either it all works, or nothing changes.<br><br>**Things we used:**<br>• **`CREATE EXTENSION`**: it's like `npm install` for a Postgres plugin. It's used to switch on pgvector in this database.<br>• **`create_all`**: it's like `prisma db push`. It's used to create every table from the model classes.<br>• **`engine.begin()`**: it's like a `try { ... } catch { undo }` around DB work. It's a transaction; it's used to save everything or nothing.<br>• **`run_sync`**: it's like wrapping an old callback API so it works with `await`. It's used to run sync SQLAlchemy helpers on an async connection.<br>• **`argparse`**: it's like `yargs` / `process.argv` parsing. It's used to read command-line flags like `--drop`.<br>• **`asyncio.run()`**: it's like top-level `await` in a script. It's used to start the async engine and run the main function.<br>• **`python -m`**: it's like `npx` running something from the project root. It's used to run a script as a module so `from app...` imports work. |

---

## Step 7: Let's fill the store with products (and their AI fingerprints)

**🎯 Interview takeaway:** Embeddings turn text into vectors so similar meanings sit close together, and cosine similarity measures that closeness.

| Developer Notes | Casual Explanation |
|---|---|
| `scripts/seed_catalog.py`: 30 products, 5 categories.<br>Embed `name + category + description` with `text-embedding-3-small`.<br>**One batched API call** for all 30 (≈ $0.00004).<br>**Upsert** by SKU (`ON CONFLICT DO UPDATE`), safe to re-run.<br>`async with AsyncOpenAI()` closes the client (fixed "Event loop is closed").<br>Test data traps: 3 out-of-stock + 1 discontinued (`HK-006`).<br>Check: earbuds → speaker 0.42, watch 0.42, then weak matches. | We stocked the shelves and asked OpenAI to give each product its "meaning fingerprint", all in one go instead of 30 separate trips.<br><br>Search for things like earbuds and you get a speaker and a fitness watch: nice. But it also dragged in trekking poles 🙃. Vector search *always* finds something, so later we'll add filters (price, stock, category). That combo is called **hybrid search**.<br><br>**Things we used:**<br>• **`AsyncOpenAI`**: it's like the OpenAI JS SDK. It's an API client; it's used to call OpenAI without blocking.<br>• **`text-embedding-3-small`**: it's an OpenAI model; it's used to turn text into 1536 numbers that capture its meaning.<br>• **Batching**: it's like `Promise.all`, but even better, because it's one request instead of many. It's used to save time and money.<br>• **`async with`**: it's like `try/finally` that auto-closes things. It's used to make sure the OpenAI client shuts down properly.<br>• **Upsert (`on_conflict_do_update`)**: it's like Prisma's `upsert`. It's used to insert new rows or update existing ones in one go.<br>• **`<=>` operator**: it's pgvector's "how different are these two?" operator. It's used to measure cosine distance between vectors. |
