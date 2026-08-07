# 32 · Concept: FastAPI (30 questions)

[← Concept: ASP.NET Core Web API](31-concept-aspnet-webapi.md) · [Home](README.md) · [Next → Web API vs FastAPI](33-concept-webapi-vs-fastapi.md)

This file explains **FastAPI** (Python) simply and in depth. I built the FastAPI ETL services on TCW (Project A) that ingest BlackRock Aladdin data, so I answer from real code.

> Simple one-liner: *"FastAPI is a modern, very fast Python framework for building APIs. It uses standard Python type hints to automatically validate data and generate interactive API documentation — so you write less code and get more safety."*

**Jump to (fundamentals):** [F1 What it is](#f1--what-is-fastapi) · [F2 Path & endpoints](#f2--endpoints-and-path-operations) · [F3 Pydantic validation](#f3--pydantic-and-automatic-validation) · [F4 async](#f4--async-and-performance) · [F5 Dependency injection](#f5--dependency-injection) · [F6 Auto docs](#f6--automatic-documentation) · [F7 Errors & middleware](#f7--error-handling-and-middleware) · [F8 Why for ETL/AI](#f8--why-fastapi-for-etl-and-ai)
> **Request handling:** [F9 Params in depth](#f9--path-query-body-and-headers) · [F10 Pydantic deep](#f10--pydantic-models-in-depth) · [F11 Response models](#f11--response-models-and-status-codes) · [F12 Nested DI](#f12--dependency-injection-in-depth) · [F13 Async vs sync](#f13--async-vs-sync-and-the-event-loop) · [F14 Background tasks](#f14--background-tasks-and-heavy-work)
> **Architecture:** [F15 Project structure](#f15--structuring-a-large-fastapi-app) · [F16 Database & ORM](#f16--databases-sqlalchemy-and-async) · [F17 Config & settings](#f17--configuration-and-settings) · [F18 Auth](#f18--authentication-and-oauth2) · [F19 Middleware & CORS](#f19--middleware-cors-and-gzip) · [F20 Routers](#f20--routers-and-modular-endpoints)
> **Production & performance:** [F21 ASGI servers](#f21--asgi-uvicorn-and-gunicorn) · [F22 Performance](#f22--performance-tuning) · [F23 Caching](#f23--caching) · [F24 Error strategy](#f24--error-handling-strategy) · [F25 Logging](#f25--logging-and-observability) · [F26 Testing](#f26--testing-fastapi)
> **Deploy, security & data:** [F27 Deployment](#f27--deployment-and-containers) · [F28 Security](#f28--security-hardening) · [F29 ETL patterns](#f29--etl-patterns-in-practice) · [F30 AI/RAG serving](#f30--serving-ai-and-rag) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of FastAPI in plain English. I built the FastAPI ETL services on TCW (A) that ingest BlackRock Aladdin data, and used FastAPI-style Python services on Sculptor/Bain ETL (D), so this is how I actually use it. Hold these ideas and every question below is a detail hanging off one of them.

**1. Type hints do the heavy lifting.** FastAPI's standout trick is using ordinary **Python type hints** to validate incoming data, convert types, and generate documentation — automatically. I write a typed function signature and get validation and docs for free. Less code, more safety.

**2. It stands on Starlette and Pydantic.** **Starlette** gives the fast async web machinery; **Pydantic** gives data validation and models. Understanding that split explains everything: web behaviour comes from Starlette, data correctness comes from Pydantic.

**3. Pydantic validates at the boundary.** Request bodies become Pydantic models, validated before my code runs. Bad or malformed data is rejected with a clean 422 at the edge — so on A, dodgy Aladdin data is caught at ingestion, never reaching the database. That boundary check is the whole point for ETL.

**4. async and the event loop are core.** FastAPI is async-native. For I/O-bound work (DB calls, HTTP fetches, file reads) `async def` frees the loop to handle other requests while waiting, giving throughput close to Node.js or Go. I must know when to use `async def` vs `def` (CPU-bound work belongs in threads/processes).

**5. Dependency injection is elegant and everywhere.** FastAPI's `Depends` system injects database sessions, settings, auth and shared logic into endpoints — and dependencies can nest. It keeps endpoints small and makes testing easy by swapping dependencies.

**6. Auto docs come free.** Because everything is typed, FastAPI generates interactive OpenAPI/Swagger docs automatically. The contract documents itself and stays in sync with the code — a real productivity and correctness win.

**7. Structure and data access for real apps.** A large app needs routers for modular endpoints, settings/config management, SQLAlchemy (async) for the database, middleware and CORS, and OAuth2 auth. This is what turns a demo into a maintainable service.

**The full-stack / architect lens:** the later Q&As go into production — ASGI servers (Uvicorn/Gunicorn), performance tuning, caching, error strategy, logging and observability, testing, containers and deployment, security hardening — plus the two things I use it *for*: real ETL patterns and serving AI/RAG. That's where FastAPI earns its place in a data platform, not just a tutorial.

**One rule I never break:** *validate at the boundary with Pydantic — trust nothing that crosses into my service until types and rules have passed.*

---

## F1 · What is FastAPI?

**Simple explanation.** FastAPI is a Python web framework for building APIs quickly and with high performance. Its standout feature: it uses **Python type hints** to do a lot of work for you — validating incoming data, converting types, and generating documentation — automatically.

It's built on two foundations: **Starlette** (for the fast async web parts) and **Pydantic** (for data validation). It's one of the fastest Python frameworks, close to Node.js and Go for I/O work.

*"On TCW I use FastAPI for the ETL services that pull Aladdin data — the type hints and validation catch bad data at the boundary before it ever reaches the database."*

**Follow-ups**
- *"FastAPI vs Flask/Django?"* — Flask is minimal and sync-first; Django is a big batteries-included framework; FastAPI is modern, async-native, type-driven, and faster for APIs.
- *"Why is it 'fast'?"* — Async support (ASGI) plus efficient validation — it doesn't block threads while waiting on I/O.

---

## F2 · Endpoints and path operations

**Simple explanation.** You define endpoints with decorators on functions — called **path operations**. The decorator sets the HTTP method and URL; the function does the work.

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/reports/{report_type}")          # GET /reports/equity
async def get_report(report_type: str, as_of: str | None = None):
    # report_type comes from the path, as_of from the query string (?as_of=...)
    return {"type": report_type, "as_of": as_of}
```

FastAPI reads the type hints: `report_type: str` is a **path parameter**, and `as_of: str | None = None` becomes an optional **query parameter** — automatically.

**Follow-ups**
- *"How does it know path vs query?"* — If the name is in the URL path (`{report_type}`) it's a path param; otherwise it's a query param. FastAPI infers it.
- *"Type conversion?"* — If you hint `count: int`, FastAPI converts and validates it — a non-integer returns an automatic 422 error.

---

## F3 · Pydantic and automatic validation

**Simple explanation.** **Pydantic** models describe the shape of your data as a Python class. FastAPI uses them to **validate and parse** request bodies automatically — if the data doesn't match, the client gets a clear error, and your code only ever sees valid data.

```python
from pydantic import BaseModel, Field

class Position(BaseModel):
    ticker: str
    quantity: int = Field(gt=0)          # must be > 0
    market_value: float

@app.post("/positions")
async def add_position(position: Position):   # body auto-validated into a Position
    return {"stored": position.ticker}
```

If a client posts `quantity: -5`, FastAPI returns a `422` with a helpful message — **I wrote zero validation code.**

**Follow-ups**
- *"This is the ASP.NET model-binding equivalent?"* — Yes — same idea: bind + validate the request body into a typed object before the handler runs.
- *"Why is this great for ETL?"* — I validate incoming Aladdin records against a Pydantic model, so malformed data is rejected at the door, not discovered in a report.

---

## F4 · async and performance

**Simple explanation.** FastAPI is **async-native**. Like `async/await` in C#, an `async def` endpoint releases the worker while waiting on I/O (a database, an external API), so the service handles many requests at once.

```python
@app.get("/aladdin/{portfolio}")
async def fetch(portfolio: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://aladdin/api/{portfolio}")  # non-blocking wait
    return resp.json()
```

**Rule:** use `async def` with async libraries (like `httpx`). If you must call a slow *blocking* library, use a normal `def` — FastAPI runs it in a threadpool so it doesn't block the event loop.

**Follow-ups**
- *"async def vs def in FastAPI?"* — `async def` for async I/O; plain `def` for blocking/CPU work (FastAPI offloads it to a thread automatically).
- *"Does async speed up CPU-heavy work?"* — No — async helps I/O-bound work. For CPU-bound work use multiprocessing or background workers.

---

## F5 · Dependency injection

**Simple explanation.** FastAPI has a clean, built-in **dependency injection** system using the `Depends` function. You declare what an endpoint needs, and FastAPI provides it — great for shared things like a DB session or the current user.

```python
from fastapi import Depends

async def get_db():
    db = SessionLocal()
    try:
        yield db          # provided to the endpoint
    finally:
        db.close()        # cleanup after the response

@app.get("/reports")
async def list_reports(db = Depends(get_db)):   # db injected here
    return db.query(Report).all()
```

**Follow-ups**
- *"How is this like ASP.NET DI?"* — Same goal — supply shared resources without the endpoint creating them — which makes testing easy (inject a fake).
- *"What's the `yield` for?"* — Code before `yield` sets up; code after runs as cleanup — like `useEffect` cleanup or a `using` block.

---

## F6 · Automatic documentation

**Simple explanation.** Because FastAPI knows your types and models, it **generates interactive API docs for free** at `/docs` (Swagger UI) and `/redoc`. You can try endpoints right in the browser. It also emits an **OpenAPI** spec other tools consume.

**Why it matters:** front-end and integration teams get an always-accurate contract without me writing docs by hand — a big productivity win.

**Follow-ups**
- *"Do the docs stay accurate?"* — Yes — they're generated from the actual code and types, so they can't drift out of date.
- *"Can front-end teams auto-generate clients?"* — Yes — from the OpenAPI spec they can generate typed client code.

---

## F7 · Error handling and middleware

**Simple explanation.** FastAPI returns clean JSON errors. You raise `HTTPException` for expected errors, and add custom exception handlers for the rest. **Middleware** (like ASP.NET's pipeline) wraps every request — for logging, timing, CORS.

```python
from fastapi import HTTPException

@app.get("/reports/{id}")
async def get(id: int):
    report = await find(id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
```

**Follow-ups**
- *"How do you log every request?"* — A middleware function that records the path, status and duration — I used this for the ETL services' structured logging.
- *"Handling unexpected errors?"* — A global exception handler returns a safe 500 without leaking internals, and logs the detail server-side.

---

## F8 · Why FastAPI for ETL and AI?

**Simple explanation.** FastAPI is popular for **data and AI** work for good reasons: Python is the language of data/ML, it's async (great for calling many external APIs), and Pydantic validation is perfect for enforcing data contracts. That's exactly why I chose it on TCW.

- **ETL:** validate incoming Aladdin records with Pydantic, fetch concurrently with async, expose pipeline triggers/status as endpoints.
- **AI:** the LLM/RAG ecosystem (LangChain, etc.) is Python-first, so a FastAPI service naturally fronts a RAG app ([Project B](25-star-story-bank.md#b3--influencing-without-authority)).

**Follow-ups**
- *"Why not do the ETL in C#?"* — I split by strength: C# for the app/API tier, Python/FastAPI for data and AI where the ecosystem and libraries are strongest.
- *"Does FastAPI scale in production?"* — Yes — run it behind an ASGI server (Uvicorn/Gunicorn) with multiple workers, containerised on Azure.

---

## F9 · Path, query, body, and headers

**Simple explanation.** FastAPI infers where each parameter comes from by its type and name. Path params are in the URL; simple types become query params; Pydantic models become the JSON body; and you can declare headers, cookies and form data explicitly.

```python
from fastapi import Header
@app.get("/reports/{type}")
async def get(type: str, page: int = 1, x_tenant: str = Header(...)):
    ...   # type=path, page=query (?page=2), x_tenant=header
```

**Follow-ups**
- *"How to add validation to a query param?"* — Use `Query(default, ge=1, le=100)` to set bounds and metadata — FastAPI enforces and documents it.
- *"Multiple body params?"* — Pass several Pydantic models; FastAPI nests them in the JSON body by parameter name.

---

## F10 · Pydantic models in depth

**Simple explanation.** Pydantic is the heart of FastAPI. Models validate types and constraints, apply defaults, and (in v2) run fast Rust-backed validation. You add field rules with `Field`, custom checks with validators, and config for behaviour.

```python
from pydantic import BaseModel, Field, field_validator
class Position(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    quantity: int = Field(gt=0)
    @field_validator("ticker")
    @classmethod
    def upper(cls, v): return v.upper()
```

**Follow-ups**
- *"Pydantic v1 vs v2?"* — v2 is much faster (Rust core) and changed some APIs (`field_validator`, `model_config`). New projects use v2.
- *"How do you validate cross-field rules?"* — A `model_validator` that sees the whole object (e.g. end date after start date).

---

## F11 · Response models and status codes

**Simple explanation.** You declare what an endpoint *returns* with `response_model`, so FastAPI filters/validates the output and documents it. You set status codes per route.

```python
@app.post("/positions", response_model=PositionOut, status_code=201)
async def create(p: PositionIn) -> PositionOut:
    ...   # response_model strips internal fields, guarantees the contract
```

**Follow-ups**
- *"Why separate PositionIn and PositionOut?"* — Input and output shapes differ (input has no id; output hides internal fields) — like DTOs in .NET.
- *"Does response_model cost performance?"* — A little validation overhead; you can disable it on hot paths, but I keep it for safety.

---

## F12 · Dependency injection in depth

**Simple explanation.** `Depends` composes: dependencies can depend on other dependencies, be cached per request, and be overridden in tests. Common uses: DB session, current user, pagination params, settings.

```python
async def current_user(token: str = Depends(oauth2_scheme)) -> User: ...
@app.get("/me")
async def me(user: User = Depends(current_user)): return user
```

**Follow-ups**
- *"How do you fake a dependency in tests?"* — `app.dependency_overrides[get_db] = fake_db` — clean, no monkey-patching.
- *"Are dependencies cached?"* — Within one request the same dependency resolves once by default — efficient for a shared DB session.

---

## F13 · async vs sync and the event loop

**Simple explanation.** FastAPI runs on an **event loop** (asyncio). `async def` endpoints must use `await` with async libraries to stay non-blocking. A plain `def` endpoint is run in a threadpool so blocking libraries don't freeze the loop. Never call a blocking function directly inside `async def`.

**Follow-ups**
- *"What happens if I block the event loop?"* — Every other request stalls — the classic FastAPI performance bug. Use async libs or offload to a thread.
- *"CPU-bound work in an endpoint?"* — Push it to a worker/process pool (or a queue), not the event loop — async doesn't help CPU work.

---

## F14 · Background tasks and heavy work

**Simple explanation.** For quick after-response work (send an email, write a log) use `BackgroundTasks`. For heavy or long jobs (large ETL runs, ML) use a real task queue like **Celery** or an Azure queue worker — don't tie them to the request.

```python
from fastapi import BackgroundTasks
@app.post("/ingest")
async def ingest(bt: BackgroundTasks):
    bt.add_task(write_audit_log)   # runs after the response is sent
    return {"status": "accepted"}
```

**Follow-ups**
- *"BackgroundTasks vs Celery?"* — BackgroundTasks for light, in-process work; Celery/queue for heavy, retryable, independently-scaled jobs.
- *"How do you trigger a big ETL safely?"* — Return `202 Accepted`, enqueue the job, and expose a status endpoint — the request doesn't wait.

---

## F15 · Structuring a large FastAPI app

**Simple explanation (architect lens).** I organise by feature with routers, keeping API, schemas (Pydantic), services (logic) and data access separate — the same layering discipline as my .NET apps.

```
app/
  api/routers/       (positions.py, reports.py — endpoints)
  schemas/           (Pydantic models)
  services/          (business logic)
  db/                (models, session)
  core/              (config, security, logging)
  main.py            (app factory, include routers)
```

**Follow-ups**
- *"Why an app factory?"* — A `create_app()` function makes testing and multiple configs easy — no global app state.
- *"Keep endpoints thin?"* — Yes — routers call services; business logic never lives in the endpoint function.

---

## F16 · Databases: SQLAlchemy and async

**Simple explanation.** FastAPI has no built-in ORM; **SQLAlchemy** is the standard (with **Alembic** for migrations). Use the **async** engine with an async DB driver so DB calls don't block the loop, and provide the session via a dependency.

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**Follow-ups**
- *"SQLAlchemy vs raw SQL?"* — ORM for productivity; raw SQL (`text()`) for tuned hot queries — same trade-off as EF Core vs Dapper.
- *"How do migrations work?"* — Alembic generates and versions schema changes — the Python equivalent of EF Core migrations.

---

## F17 · Configuration and settings

**Simple explanation.** I use **pydantic-settings** to load config from environment variables (and `.env` locally), validated into a typed `Settings` object — secrets come from environment / Azure Key Vault, never hard-coded.

```python
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    aladdin_api_key: str
    db_url: str
    model_config = {"env_file": ".env"}
```

**Follow-ups**
- *"Where do secrets come from in Azure?"* — Key Vault → environment variables (or the SDK with Managed Identity) — the app just reads typed settings.
- *"Why typed settings?"* — A missing/invalid config fails fast at startup, not at runtime in production.

---

## F18 · Authentication and OAuth2

**Simple explanation.** FastAPI has helpers for **OAuth2 with JWT bearer tokens**. A dependency extracts and validates the token and returns the user; `Depends(current_user)` protects routes. In Azure I validate **Entra ID** tokens.

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
async def current_user(token: str = Depends(oauth2_scheme)) -> User:
    return decode_and_verify(token)   # validate signature, expiry, audience
```

**Follow-ups**
- *"How do you do role-based auth?"* — A dependency that checks the user's roles/scopes and raises `403` if missing.
- *"Validate Entra ID tokens how?"* — Verify signature against the JWKS keys, plus issuer, audience and expiry — same claims a .NET API checks.

---

## F19 · Middleware, CORS, and GZip

**Simple explanation.** Middleware wraps every request — for CORS, compression, timing and correlation IDs. FastAPI/Starlette ship common ones.

```python
app.add_middleware(CORSMiddleware, allow_origins=["https://myapp"], allow_methods=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Follow-ups**
- *"Why restrict CORS origins?"* — Only my front-end origin should call the API from a browser — `*` in production is a risk.
- *"Custom middleware use?"* — Request logging with a correlation ID and duration — exactly what I add on the ETL services.

---

## F20 · Routers and modular endpoints

**Simple explanation.** `APIRouter` groups related endpoints into modules that you include in the main app — like controllers in .NET. It keeps a large API organised with shared prefixes, tags and dependencies.

```python
router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(current_user)])
app.include_router(router)
```

**Follow-ups**
- *"Router-level dependencies?"* — Apply auth once to a whole router instead of every endpoint — DRY and consistent.
- *"How do tags help?"* — They group endpoints in the auto-generated docs for readability.

---

## F21 · ASGI, Uvicorn, and Gunicorn

**Simple explanation.** FastAPI is an **ASGI** app (the async successor to WSGI). You run it with an ASGI server — **Uvicorn** — often managed by **Gunicorn** with multiple Uvicorn workers to use all CPU cores in production.

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4
```

**Follow-ups**
- *"Why multiple workers?"* — One Python process uses one core (GIL); multiple workers use all cores for real concurrency.
- *"How many workers?"* — A common start is `2 × cores + 1`, then tune by load testing.

---

## F22 · Performance tuning

**Simple explanation.** FastAPI is fast, but I still tune: never block the event loop, use **async DB/HTTP** libraries, fetch external calls **concurrently** with `asyncio.gather`, add caching, paginate, and run enough workers. Measure before optimising.

```python
results = await asyncio.gather(*[fetch(p) for p in portfolios])   # concurrent, not serial
```

**Follow-ups**
- *"Biggest FastAPI performance mistake?"* — A blocking call inside `async def` — it stalls the whole loop.
- *"How did concurrency help your ETL?"* — Fetching many Aladdin endpoints in parallel with `gather` cut ingestion time versus calling them one by one.

---

## F23 · Caching

**Simple explanation.** Cache slow, read-heavy, slow-changing data. For a single instance, an in-memory cache works; across instances I use **Redis**. Always set an expiry.

**Follow-ups**
- *"In-memory vs Redis in FastAPI?"* — In-memory is per-worker (inconsistent when scaled out); Redis is shared — same reasoning as .NET.
- *"What not to cache?"* — Frequently-changing or per-user-sensitive data unless keyed and expired carefully.

---

## F24 · Error handling strategy

**Simple explanation.** Raise `HTTPException` for expected errors; register **exception handlers** for custom exceptions and a catch-all for unexpected ones that logs the detail and returns a safe message. Pydantic validation errors auto-return `422` with a clear body.

```python
@app.exception_handler(ReportNotFound)
async def handle(_, exc): return JSONResponse(status_code=404, content={"detail": str(exc)})
```

**Follow-ups**
- *"Why custom exceptions?"* — Business code raises meaningful errors (`ReportNotFound`); handlers map them to HTTP codes — clean separation.
- *"Leak internals on 500?"* — Never — log server-side, return a generic message.

---

## F25 · Logging and observability

**Simple explanation.** I use **structured JSON logging** (structlog / standard logging) with correlation IDs, and export traces/metrics via **OpenTelemetry** to Azure Monitor — so a Python ETL service is observable alongside the .NET APIs.

**Follow-ups**
- *"Why structured logs?"* — Queryable by field (all logs for one ingestion run) — essential for triaging pipeline failures.
- *"How do you trace across services?"* — OpenTelemetry propagates a trace ID from the .NET API through the FastAPI service.

---

## F26 · Testing FastAPI

**Simple explanation.** FastAPI ships a `TestClient` (and `httpx.AsyncClient` for async) so you call endpoints in tests with **pytest**, overriding dependencies for fakes — fast and realistic.

```python
def test_get_report():
    app.dependency_overrides[get_db] = fake_db
    r = TestClient(app).get("/reports/equity")
    assert r.status_code == 200
```

**Follow-ups**
- *"How do you test the DB layer?"* — Against a test/SQLite or a containerised Postgres, with transactions rolled back per test.
- *"Dependency overrides value?"* — Swap real deps for fakes cleanly — no monkey-patching, just like .NET's injected mocks.

---

## F27 · Deployment and containers

**Simple explanation.** I containerise the FastAPI app (Docker), run Uvicorn/Gunicorn inside, and deploy to **Azure Container Apps / App Service / AKS** with CI/CD. Health endpoints let the platform manage restarts and readiness.

**Follow-ups**
- *"Why containers for Python?"* — They pin the exact Python version and dependencies — no "works on my machine" drift.
- *"Where does it run in your stack?"* — On Azure alongside the .NET API; they talk over HTTP, so language differences don't matter.

---

## F28 · Security hardening

**Simple explanation.** Same principles as any API: validate all input (Pydantic helps hugely), parameterised queries via SQLAlchemy (no string SQL), tight CORS, HTTPS, secrets in Key Vault, auth on every protected route, and rate limiting at the gateway.

**Follow-ups**
- *"How does Pydantic aid security?"* — It rejects malformed/oversized input at the boundary, shrinking the attack surface.
- *"SQL injection in Python?"* — Avoided by using SQLAlchemy parameters, never f-string SQL with user input.

---

## F29 · ETL patterns in practice

**Simple explanation (from real TCW work).** My FastAPI ETL: (1) validate incoming Aladdin records with Pydantic at the boundary, (2) fetch sources concurrently with async, (3) transform and reconcile, (4) load to the store, (5) expose trigger/status endpoints and structured logs. Heavy runs go to a queue/worker, not the request.

**Follow-ups**
- *"How do you handle bad records?"* — Reject at validation, route to a dead-letter/error table, and alert — the good data still flows.
- *"Idempotent loads?"* — Upserts keyed by natural id so a retried run doesn't duplicate data.

---

## F30 · Serving AI and RAG

**Simple explanation (architect lens).** Python owns the LLM ecosystem, so a FastAPI service naturally fronts a **RAG** app: an endpoint takes a question, retrieves relevant chunks (vector search), builds a grounded prompt, calls the model (Azure OpenAI), and returns the answer with sources. Async suits the many external calls; Pydantic shapes the request/response.

*"This maps to the RAG reference architecture I authored on TCW (Project B) and the first production RAG app I delivered — retrieval, grounding, orchestration and evaluation, served over FastAPI."*

**Follow-ups**
- *"Why FastAPI for AI over .NET?"* — The LLM/RAG libraries (LangChain, vector clients) are Python-first — fastest path to a safe, working app.
- *"How do you stream tokens?"* — A streaming response (SSE) so the UI shows the answer as it's generated.
- *"Where does Azure AI Foundry fit?"* — It provides the models, grounding, evaluation and safety; my FastAPI service orchestrates calls to it (see file 37, Z10).

---

## Section index

| # | Concept | One-line takeaway |
|---|---|---|
| F1 | What it is | Modern, fast, type-driven Python API framework |
| F2 | Endpoints | Decorators + type hints define path/query params |
| F3 | Pydantic | Automatic request validation from typed models |
| F4 | async | Async-native; frees workers during I/O |
| F5 | Dependency injection | `Depends` supplies DB/user; `yield` for cleanup |
| F6 | Auto docs | Free interactive Swagger/OpenAPI from your types |
| F7 | Errors & middleware | `HTTPException` + middleware for logging/CORS |
| F8 | ETL & AI fit | Python + async + validation = ideal for data & LLM work |
| F9 | Params in depth | Path/query/body/header inferred from type & name |
| F10 | Pydantic deep | Field rules, validators; v2 Rust core is fast |
| F11 | Response models | `response_model` filters/validates output; In vs Out |
| F12 | DI in depth | `Depends` composes & caches; overridable in tests |
| F13 | async vs sync | Never block the event loop; def runs in a threadpool |
| F14 | Background tasks | BackgroundTasks light; Celery/queue for heavy jobs |
| F15 | Project structure | Feature routers + schemas + services + db; app factory |
| F16 | DB & ORM | SQLAlchemy (async) + Alembic migrations |
| F17 | Config | pydantic-settings; secrets from env/Key Vault |
| F18 | Auth | OAuth2 + JWT; validate Entra ID tokens |
| F19 | Middleware & CORS | CORS/GZip/logging wrap every request |
| F20 | Routers | APIRouter modularises endpoints (like controllers) |
| F21 | ASGI servers | Uvicorn + Gunicorn workers use all cores |
| F22 | Performance | Non-blocking + asyncio.gather + caching; measure first |
| F23 | Caching | In-memory per-worker vs shared Redis |
| F24 | Error strategy | HTTPException + handlers; 422 auto for validation |
| F25 | Logging | Structured JSON + OpenTelemetry to Azure Monitor |
| F26 | Testing | TestClient + pytest + dependency overrides |
| F27 | Deployment | Containers on Azure with CI/CD + health checks |
| F28 | Security | Pydantic validation, parameterised SQL, tight CORS, Key Vault |
| F29 | ETL patterns | Validate, fetch concurrently, transform, idempotent load |
| F30 | AI/RAG serving | FastAPI fronts retrieval + grounding + model calls |

---

[← Concept: ASP.NET Core Web API](31-concept-aspnet-webapi.md) · [Home](README.md) · [Next → Web API vs FastAPI](33-concept-webapi-vs-fastapi.md)
