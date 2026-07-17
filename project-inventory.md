# Project Inventory — Snapshot

> **Snapshot date:** 2026-07-17
> **Branch at capture:** `version_before_restcodegen`
> **Nature:** One-time, dated snapshot of the project's current state. **Not** a
> living document — regenerate on request rather than editing in place.

> ⚠️ **This snapshot describes the project _before_ the restcodegen code generator
> was introduced.** Here the account API clients (`AccountApi`, `LoginApi`) are
> **hand-written** on top of the external [`restclient`](https://github.com/SDET-org/rest_client)
> package, and the pydantic models live in **one file per model**. The
> restcodegen-based (generated) variant is developed on the
> `prof_ch4_datamodel0_code_generator` branch and is intentionally **not** part of
> this branch.

A Python framework for **automated functional testing of a REST API**. The
system under test is the **DM.API Account** service (user registration,
activation, login/logout, email & password change), verified end-to-end against
a live server together with a **MailHog** inbox used to read activation and
password-reset emails.

---

## 1. System Under Test

| Item | Value |
|------|-------|
| API under test | **DM.API Account** (OpenAPI 3.0.1, title `DM.API Account`) |
| Account service host | `http://185.185.143.231:5051` |
| MailHog host | `http://185.185.143.231:5025` |
| Contract | `swagger/swagger_account.json` |
| Auth mechanism | Header `x-dm-auth-token` (obtained from login response headers) |

Endpoints exercised:

| Path | Methods |
|------|---------|
| `/v1/account` | `POST` (register), `GET` (current user) |
| `/v1/account/{token}` | `PUT` (activate) |
| `/v1/account/password` | `POST` (request reset), `PUT` (change) |
| `/v1/account/email` | `PUT` (change email) |
| `/v1/account/login` | `POST` (login), `DELETE` (logout) |
| `/v1/account/login/all` | `DELETE` (logout everywhere) |

MailHog endpoint used by the framework: `GET /api/v2/messages`.

---

## 2. Tech Stack

| Area | Choice |
|------|--------|
| Language | Python — `requires-python = ">=3.13,<4.0"`; **venv is 3.14.3**; CI runs 3.14 |
| Dependency manager | **Poetry**, `package-mode = false` (installed with `--no-root`) |
| HTTP client | **httpx** (`httpx.AsyncClient`) — fully async |
| API clients | **Hand-written**, subclassing the external `restclient` package's `RestClient` (see §4). **No code generator on this branch.** |
| Test runner | **pytest 9.1.0** + **pytest-asyncio** (`asyncio_mode = auto`, session-scoped loop) |
| Data models / validation | **pydantic v2** (`extra="forbid"`, `serialization_alias` for camelCase) |
| Assertions | **PyHamcrest** matchers + **assertpy** soft assertions |
| Reporting | **Allure** (`allure-pytest`) |
| API coverage | **swagger-coverage 3.5.2** (Java-based report generator) |
| Logging | **structlog** + **curlify2** — via the external `RestClient` (curl reproduction of each request) |
| Config | **vyper-config** (YAML env files + CLI overrides) |
| Notifications | **pytest-telegram-notifier** + **pyTelegramBotAPI** (`telebot`) |
| Shared REST client | **`rest-client`** — external git dependency (`git+https://github.com/SDET-org/rest_client.git@main`), imported as `restclient` |
| Linter / formatter | **Ruff** (line length 120; rules `E`,`F`,`I`,`UP`,`ANN`,`B`,`SIM`) — see §2.2 |
| Type checker | **mypy** (strict-leaning; see §2.2) |
| Git hooks | **pre-commit** (ruff format, ruff check, mypy) |

### 2.1 Declared-but-unused dependencies (cleanup candidates)

Pinned in `pyproject.toml` but **not imported anywhere** in the code (import-grep
verified 2026-07-14; the dependency set is unchanged since):

`aiohttp`, `marshmallow`, `distconfig3`, `environs`, `retrying`, `rootpath`,
`watchdog`, `faker`, `toml`, `six`.

Notably:
- **`aiohttp`** is declared but the async HTTP stack is **httpx**, not aiohttp.
- **`marshmallow`** is declared but all models are **pydantic**.
- **`retrying`** is declared but retries use a **hand-written `retrier` decorator** (`helpers/account_helper.py`).
- **`faker`** is declared (and auto-loads as a pytest plugin) but test data is generated from `time.time_ns()`, not Faker.

Actually-imported third-party libs: `httpx`, `pydantic`, `hamcrest`, `assertpy`,
`vyper`, `telebot`, `allure`, `pytest`, and — through the external `restclient`
package — `structlog`, `curlify2`, `swagger_coverage_py`.

### 2.2 Linter configuration

Both tools live in **`pyproject.toml`** (`[tool.ruff]` / `[tool.mypy]`) so there
is one config file (there is no standalone `mypy.ini`).

**The problem this solves.** `disallow_untyped_defs` only requires that an
annotation *exists*, not that it is informative: `-> Any` and a bare `dict` both
satisfy it, and mypy reports success. `Any` therefore became the cheapest way to
silence the checker. The flags below make the annotations mean something.

| Flag / rule | What it catches |
|-------------|-----------------|
| `warn_return_any` | `Any` leaking out through a declared return type |
| `disallow_any_generics` | bare `dict` / `Callable` (implicitly `Any`-parameterised) |
| `warn_unused_ignores` | a `# type: ignore` that suppresses nothing |
| `warn_redundant_casts`, `no_implicit_optional`, `strict_equality`, `warn_unreachable` | no-op casts, implicit `Optional`, impossible comparisons, dead branches |
| ruff `ANN401` | a bare `Any` in a signature |
| ruff `UP` | keeps syntax on the 3.13 baseline (`list[x]`, `x \| None`, `StrEnum`) |
| ruff `I`, `B`, `SIM` | import order; bugbear / simplify traps |

**Deliberately not enabled:** `disallow_untyped_calls` and
`disallow_untyped_decorators` — allure ships `py.typed` but annotates nothing, so
every `@allure.step` / `@allure.title` would error with no fix on our side.

**Import overrides.**
- `vyper`, `curlify2`, `swagger_coverage_py`, `assertpy` genuinely lack types —
  listed explicitly rather than via a project-wide `ignore_missing_imports`,
  which would also mask a typo'd import.
- **`restclient.*` → `follow_untyped_imports`**: the external `rest-client`
  package ships no `py.typed` marker, so mypy would otherwise treat it as `Any`
  and every client method call would leak `Any` out through a declared return
  type. Its source *is* fully annotated, so `follow_untyped_imports` makes mypy
  read those real annotations.
- `checkers.*` → `disable_error_code = ["arg-type"]`: pyhamcrest stubs declare
  matchers as `Matcher[Never]`, so correct matcher usage fails `arg-type` (a stub
  defect, not a code defect).

**Per-file ruff ignore:** `tests/**` ignores `ANN201` (test functions return
`None` by definition; annotating every one adds noise).

**Remaining `Any`, deliberate and documented at the definition:** the parsed
MailHog message body (`dict[str, Any]` — arbitrary JSON) in `_get_token_by_login`.
Elsewhere, where a value is genuinely unknown, the code uses **`object`** instead
(e.g. the `info` before-validator, `UserDetailsEnvelope.metadata`) — it accepts
anything but forces a narrowing check, whereas `Any` disables checking entirely.

---

## 3. Repository Structure

```
.
├── clients/http/                     # Low-level API clients (transport + typed methods)
│   ├── dm_api_account/                # Hand-written account client (NOT generated)
│   │   ├── apis/
│   │   │   ├── account_api.py         # AccountApi(RestClient): POST/GET account, PUT token/email/password, POST password
│   │   │   └── login_api.py           # LoginApi(RestClient): POST login, DELETE login, DELETE login/all
│   │   └── models/                    # pydantic DTOs — ONE FILE PER MODEL (see §6)
│   │       ├── registration.py
│   │       ├── login_credentials.py
│   │       ├── change_email.py
│   │       ├── change_password.py
│   │       ├── reset_password.py
│   │       ├── user_envelope.py         # UserEnvelope → User (+ Rating, UserRole enum)
│   │       ├── user_details_envelope.py # UserDetailsEnvelope → UserDetails (+ settings/info value objects, info field_validator)
│   │       ├── bad_request_error.py
│   │       ├── general_error.py
│   │       └── problem_details.py       # ProblemDetails (the body actually returned on 401/403 — see §12)
│   └── api_mailhog/apis/mailhog_api.py# MailhogApi(RestClient): GET /api/v2/messages
├── services/                          # Facades that group clients per service
│   ├── dm_api_account.py              # DmApiAccount → {account_api, login_api}
│   └── api_mailhog.py                 # MailHogApi → {mailhog_api}
├── helpers/
│   └── account_helper.py             # AccountHelper: business flows across services + retrier decorator
├── checkers/                          # Reusable response assertions
│   ├── http_checkers.py              # check_status_code_http (context manager)
│   ├── get_v1_account_checker.py     # GetV1AccountChecker (hamcrest + assertpy)
│   └── post_v1_account_checker.py    # PostV1AccountChecker (hamcrest)
├── tg_notifier/
│   └── bot.py                        # Standalone Telegram sender for the swagger-coverage report
├── tests/
│   ├── conftest.py                   # Fixtures, CLI options, config loading, swagger-cov setup
│   ├── user.py                       # User NamedTuple (test-user credentials)
│   ├── functional/                   # Functional tests (see §5)
│   │   ├── account_service/account/  # GET/POST/PUT account tests
│   │   ├── account_service/login/    # POST login, DELETE logout tests
│   │   └── post_v1_account/          # Base end-to-end test (register→activate→login)
│   └── smoke/                        # (empty placeholder package)
├── config/                            # Per-environment config
│   ├── stg.yaml                      # 'stg' environment (default)
│   └── prod.yaml                     # 'prod' — currently IDENTICAL to stg.yaml
├── swagger/swagger_account.json       # OpenAPI 3.0.1 contract for the account service
├── .github/workflows/python-tests.yml # CI caller → reusable workflow in SDET-org/common-pipeline
├── Dockerfile                         # Plain test image
├── Dockerfile-sw-coverage             # Test image with JRE for swagger-coverage
├── pyproject.toml / poetry.lock       # Dependencies (lint group: ruff, mypy) + [tool.ruff] / [tool.mypy] config
├── .pre-commit-config.yaml            # Git hook config
├── .env.example                       # Template for Telegram secrets (real .env is gitignored)
├── telegram-notifier-config.ini       # What/when the notifier sends
├── swagger-coverage-config-*.json     # swagger-coverage report writer config
├── README.md                          # Setup & tooling guide (Poetry, ruff, mypy, hooks, coverage, Telegram)
├── project-inventory.md               # THIS dated snapshot (tracked on this branch)
└── to_think_about.md                  # Backlog of deferred technical ideas (RU)
```

**Non-tracked / on-disk-only artifacts** (present locally, gitignored — see §11):
`.env`, `tg_bot_creds.txt`, `.venv/`, `.books/`, `.claude/`, `api-notes.md`,
`CLAUDE.md`, `allure-results/`, `.pytest_cache/`, and stale `__pycache__`-only
dirs `api_mailhog/`, `dm_api_account/` at the repo root (leftovers from before the
source was moved under `clients/` — safe to delete).

---

## 4. Architecture — Layered Design

Requests flow through clearly separated layers, each with one responsibility.
Both the **account** and the **MailHog** clients ride on the external
`RestClient` (which they subclass):

```
Test  →  Checker (assert)         Test  →  AccountHelper (business flow)
                                            │
                                            ▼
                                   DmApiAccount            MailHogApi   ← service facades
                                            │                   │
                                   ┌────────┴────────┐          ▼
                                   ▼                 ▼        MailhogApi
                              AccountApi         LoginApi        │
                                   │                 │           │
                                   └──── subclass RestClient ────┘   ← shared transport
                                                     │  (external `restclient` pkg)
                                                     ▼
                                   Configuration (host, headers, verify)
```

- **API clients** (`AccountApi`, `LoginApi`, `MailhogApi`) — **hand-written** and
  each **subclasses the external `RestClient`**. They call `self.post(...)` /
  `self.get(...)` / `self.put(...)` / `self.delete(...)` with `path=` and, for
  bodies, `json=model.model_dump(by_alias=True, exclude_none=True)`; success
  bodies are parsed with `Model(**response.json())`. There is **no code
  generator and no `api_client` wrapper on this branch** — the client *is* the
  `RestClient` subclass.
- **`RestClient`** (external [`restclient`](https://github.com/SDET-org/rest_client)
  package; `restclient/client.py`) — the single transport for **all** clients: a
  thin async wrapper over `httpx.AsyncClient` centralizing structured logging,
  curl generation, Allure attachment (`@allure_attach`), optional swagger-coverage
  recording, and `raise_for_status()` (non-2xx → `httpx.HTTPStatusError`, which
  the checkers catch). It also re-exports `Configuration`.
- **Service facades** (`DmApiAccount`, `MailHogApi`) — group the clients that
  belong to one service behind a single object sharing one `Configuration`.
  `DmApiAccount` builds `AccountApi(configuration=...)` and
  `LoginApi(configuration=...)` — **two separate `RestClient` instances**.
- **`AccountHelper`** — composite facade encapsulating multi-step **business
  flows** (register → activate → login, change password with token retrieval,
  authenticate client, etc.). Because the two account clients are separate
  transports, `authenticate_client` persists the auth token on **both**
  (`account_api.set_headers(...)` and `login_api.set_headers(...)`). Reaches into
  MailHog for tokens.
- **Concrete return types via `@overload`.** Every client/helper method whose
  behaviour depends on a `validate_response` flag is **overloaded on a
  `Literal[True]/[False]`**, so callers receive `UserEnvelope`
  (or `UserDetailsEnvelope`) vs. `httpx.Response` directly — **no `Any`, no union
  to narrow at the call site**.
- **Checkers** — reusable assertion units, decoupled from the calling code.
- **Tests** — orchestrate fixtures + helpers + checkers; contain no transport logic.

---

## 5. Test Design & Conventions

- **Count at snapshot:** **14 tests collected** (12 test functions across 9 files;
  the negative registration test contributes 3 parametrized cases). `tests/smoke/`
  is an empty placeholder.
- **Async:** every test is `async def`; `asyncio_mode = "auto"` means no explicit
  `@pytest.mark.asyncio` is needed. Loop scope is **session**.
- **Naming:** files `test_<method>_<path>.py`; classes
  `Tests<Method><Path><Positive|Negative|...>`; methods `test_<...>`.
- **Allure taxonomy:** classes tagged with `@allure.suite` / `@allure.sub_suite`
  ("Positive tests" / "Negative tests"); tests with `@allure.title`; helper &
  client methods with `@allure.step`.
- **Parametrization:** negative registration test uses `pytest.param(..., id=...)`
  with lambda transformers to mutate one credential field at a time
  (`invalid_login`, `invalid_email`, `invalid_password`).
- **Assertions — three complementary styles:**
  - `check_status_code_http(expected_status_code, expected_message)` context
    manager — asserts status code + `title` message, driven by httpx's
    `raise_for_status()` / `HTTPStatusError`.
  - **PyHamcrest** matchers (`assert_that`, `has_property`, `all_of`, …) for deep
    structural checks in checkers.
  - **assertpy** `soft_assertions()` for grouped soft checks.
- **No custom pytest markers** are registered; the only custom CLI options are
  `--env`, `--swagger-coverage`, and per-config `--service.*` / `--user.*` overrides.

### Fixtures (`tests/conftest.py`)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `set_config` | session, autouse | Loads `config/<env>.yaml` into Vyper, applies CLI overrides |
| `setup_swagger_coverage` | session, autouse | No-op unless `--swagger-coverage`; sets up/generates coverage report |
| `mailhog_api_fxt` | session | MailHog client (read activation emails) |
| `dm_account_api_fxt` | function | Low-level `DmApiAccount` client |
| `account_helper_fxt` | function | Unauthenticated `AccountHelper` (test drives registration itself) |
| `user_data_fxt` | function | Unique test user (`login = ab<time_ns>`, `@test.com` emails) |
| `account_helper_auth_existing_fxt` | function | Helper logged in as a **pre-existing** hardcoded user |
| `account_helper_auth_new_fxt` | function | Helper that **creates + activates + logs in** a fresh user |

---

## 6. Data Models (pydantic v2)

**One file per model** under `clients/http/dm_api_account/models/` (there is **no**
single generated `api_models.py` on this branch). All request/response envelopes
use `ConfigDict(extra="forbid")`.

- **camelCase mapping via `serialization_alias`** (not a plain `alias`): fields
  keep their snake_case Python names and are **built by name**
  (`LoginCredentials(remember_me=...)`, `ChangePassword(old_password=...,
  new_password=...)`), then dumped to camelCase with
  `model_dump(by_alias=True, exclude_none=True)`. This sidesteps the
  build-by-alias requirement (and the pydantic-mypy `populate_by_name` gotcha)
  entirely.
- **Requests:** `Registration`, `LoginCredentials` (`rememberMe`), `ChangeEmail`,
  `ResetPassword`, `ChangePassword` (`oldPassword`/`newPassword`).
- **Responses:** `UserEnvelope` → `User` (+ `Rating`, `UserRole` enum);
  `UserDetailsEnvelope` → `UserDetails` (superset with `settings`, `info`, etc.).
- **Enums / value objects:** `UserRole`, `BbParseMode`, `ColorSchema`,
  `UserSettings`, `PagingSettings`, `InfoBbText`.
- **Errors:** `BadRequestError` (`invalidProperties`), `GeneralError`,
  `ProblemDetails` — all present as **their own hand-written model files**.

> **`UserDetails.info` `field_validator`** (`user_details_envelope.py`) normalizes
> an empty-string `info` to `None` — the API serializes an absent `InfoBbText` as
> `""` rather than `null`/object, so without this `GET /v1/account` fails to parse
> (see §12 / `api-notes.md`). Because the models are hand-written here, this
> validator is **just part of the source** — there is no regeneration step that
> could overwrite it (unlike on the restcodegen branch).

---

## 7. Design Patterns in Use

| Pattern | Where |
|---------|-------|
| **Adapter / wrapper** | `RestClient` (external) wraps `httpx.AsyncClient` to add logging, curl, Allure, swagger-coverage, raise-for-status |
| **Template-method-ish subclassing** | `AccountApi` / `LoginApi` / `MailhogApi` **subclass `RestClient`** and add endpoint methods |
| **Facade** | `DmApiAccount`, `MailHogApi` group clients behind one object |
| **Composite facade** | `AccountHelper` composes multiple service calls into flows |
| **Decorator (custom)** | `retrier(attempts)` (PEP 695 generic, narrows `T \| None` → `T`) for token polling; `allure_attach` (in the external transport) for reporting |
| **Context manager** | `check_status_code_http` for scoped response validation |
| **DTO / Model mapping** | pydantic models with camelCase `serialization_alias` |
| **Raw-vs-parsed via `@overload`** | `validate_response=True` → parsed model; `False` → raw `httpx.Response`, resolved as concrete types by overloads |

> **No "code generation" pattern on this branch** — that is the defining
> difference from `prof_ch4_datamodel0_code_generator`, where restcodegen
> generates the clients and models.

---

## 8. Configuration & Environments

- **Vyper** reads `config/<env>.yaml` (default `--env stg`). Keys:
  `service.dm_api_account`, `service.mailhog`, `user.login`, `user.password`,
  `user.new_password`. Each is overridable via a matching `--<key>` CLI option.
- `prod.yaml` and `stg.yaml` are **currently identical** (same host + same
  credentials) — `prod` is not a distinct environment at present.
- **Secrets** (Telegram) come only from a gitignored `.env`
  (`TELEGRAM_BOT_CHAT_ID`, `TELEGRAM_BOT_ACCESS_TOKEN`), loaded via
  `load_dotenv()` in `conftest.py` and `tg_notifier/bot.py`.

---

## 9. Infrastructure

- **CI/CD** — `.github/workflows/python-tests.yml`, triggered on push/PR. It is a
  thin **caller** that delegates to a shared **reusable workflow**
  (`SDET-org/common-pipeline/.github/workflows/tests-common-python.yml@main`,
  `secrets: inherit`). The shared pipeline runs linters (mypy, ruff) then the test
  job (Java 21 + Poetry, `pytest` with swagger-coverage), uploads `allure-results`,
  builds the Allure HTML report, and publishes it to **GitHub Pages**.
- **Docker** — `Dockerfile` (plain `pytest tests`) and `Dockerfile-sw-coverage`
  (adds a JRE + runs with `--swagger-coverage`; used because report generation
  needs Java and a filesystem allowing `:` in paths, which Windows lacks).
- **Allure** — `addopts = --alluredir=allure-results`; results always produced.
- **swagger-coverage** — **off by default** (guarded by `--swagger-coverage` and
  the `SWAGGER_COVERAGE_ENABLED` env var) so the suite runs on Windows.
- **Telegram notifications** — plugin flags are commented out in `pyproject.toml`
  by default (they block when unconfigured); enable explicitly.
- **pre-commit** — ruff format, ruff check, mypy (as local hooks reusing the
  Poetry venv).

---

## 10. How to Run

```bash
# Environment (Poetry keeps the venv in-project)
poetry config virtualenvs.in-project true
poetry install --no-root            # runtime deps
poetry install --no-root --with lint  # + ruff & mypy

# Tests (hit the live API; swagger-coverage off by default → runs on Windows)
poetry run pytest tests                 # full suite
poetry run pytest tests --env stg       # explicit environment
poetry run pytest path::Test::case      # single test

# Quality gates
poetry run ruff format .                # format
poetry run ruff format --check .        # format check (CI)
poetry run ruff check .                 # lint
poetry run mypy .                       # type check

# Git hooks
poetry run pre-commit install
poetry run pre-commit run --all-files

# Swagger coverage report (Linux/Docker only — needs Java + ':' in paths)
docker build -f Dockerfile-sw-coverage -t dm-api-tests-coverage .
docker run --rm -v "$(pwd)":/app -v /app/.venv dm-api-tests-coverage
```

---

## 11. Verification Results (this snapshot)

Executed on 2026-07-17 on `version_before_restcodegen`:

| Check | Command | Result |
|-------|---------|--------|
| Lint | `ruff check .` | ✅ All checks passed |
| Types | `mypy .` | ✅ Success — no issues in **44** source files |
| Collection | `pytest --collect-only` | ✅ **14 tests collected** |
| Tests | `pytest tests` | ✅ **14 passed in ~17s** (against the live API) |

> The first live run flaked (3 failed / 2 errored) on the register→activate flows
> that depend on **MailHog email polling**; a clean rerun passed 14/14. This is the
> documented live-dependency flakiness (see §14), not a code issue — no code was
> changed to produce this snapshot.

---

## 12. Swagger vs. Reality (carried into `api-notes.md`)

The code documents where the **live API deviates from the contract**:

- **401** on `GET /v1/account` (unauthenticated) returns a **`ProblemDetails`**
  body, though swagger only declares `200 → UserDetailsEnvelope`.
- **403** on `POST /v1/account/login` (inactive user) returns **`ProblemDetails`**,
  though swagger declares `GeneralError`.
- `UserDetails.info` is serialized as an **empty string** when absent instead of
  `null`/object; a pydantic `field_validator` normalizes it.

These are recorded and expanded in `api-notes.md`.

---

## 13. Security Notes

- ✅ `.env` and `tg_bot_creds.txt` are **gitignored** and were **never committed**.
  Real Telegram secrets stay out of the repo.
- ✅ CI consumes Telegram secrets from **GitHub Actions secrets**, not the repo.
- ⚠️ **Committed test credentials:** `config/stg.yaml` and `config/prod.yaml`
  contain a plaintext login/password for a shared training account on the live
  server. Low severity (throwaway training account), but the README itself advises
  *not* to put credentials in tracked `config/*.yaml`. The same hardcoded login
  also appears in `tests/functional/.../test_get_v1_account.py`.
- ℹ️ `tg_bot_creds.txt` exists locally (untracked) and may hold real bot
  credentials; keep it gitignored. Value not inspected/recorded here.

---

## 14. Known Gotchas & Cleanup Candidates

- **Live-dependency:** all tests hit the live API + MailHog; they fail offline and
  can be **flaky** on email polling (mitigated by the `retrier` decorator, 5
  attempts, 1s apart) — see §11.
- **Shared MailHog inbox:** token lookup filters messages by `Login` and skips
  non-JSON bodies; a very busy inbox could still slow token retrieval.
- **Windows:** swagger-coverage recording writes to `…/<host:port>/` — the `:` is
  illegal on Windows, so it is disabled by default; use Docker for the report.
- **`prod.yaml` == `stg.yaml`** — no real prod environment yet.
- **Stale root dirs** `api_mailhog/`, `dm_api_account/` contain only old `.pyc`
  files — deletable.
- **Unused dependencies** (§2.1) — 10 declared libs are never imported.
- **Python version drift** — `pyproject` requires `>=3.13` but the venv/CI use 3.14
  (mypy is pinned to `python_version = 3.13`).
- **External transport dependency:** the `restclient` package is a git dependency
  (`SDET-org/rest_client@main`) with no `py.typed`; mypy reads its annotations via
  `follow_untyped_imports` (§2.2). Pinning it to a tag/commit would make builds
  reproducible.
- Open `TODO`s in code: remove test users after runs (`conftest.py`); exact-status
  assertion in `check_status_code_http` (`http_checkers.py`).
