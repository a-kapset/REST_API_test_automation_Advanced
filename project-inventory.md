# Project Inventory — Snapshot

> **Snapshot date:** 2026-07-17
> **Branch at capture:** `prof_ch4_datamodel0_code_generator`
> **Nature:** One-time, dated snapshot of the project's current state. **Not** a
> living document — regenerate on request rather than editing in place.

> ✅ **This snapshot describes the project _after_ the restcodegen code generator
> and the "Variant 2" rewiring were introduced.** The account API clients
> (`AccountApi`, `LoginApi`) and the pydantic models are **restcodegen-generated**;
> the models live in **one file** (`models/api_models.py`). The clients are
> generated from a **customized template** (`codegen_templates/`) so they call the
> external [`restclient`](https://github.com/SDET-org/rest_client) package's
> `RestClient` directly (`path=`/`json=`, `api_client: RestClient`) — there is **no
> `ApiClient` httpx wrapper**. The hand-written, pre-generator variant is pinned on
> the `version_before_restcodegen` branch.

A Python framework for **automated functional testing of a REST API**. The system
under test is the **DM.API Account** service (user registration, activation,
login/logout, email & password change), verified end-to-end against a live server
together with a **MailHog** inbox used to read activation and password-reset
emails.

---

## 1. System Under Test

| Item | Value |
|------|-------|
| API under test | **DM.API Account** (OpenAPI 3.0.1, title `DM.API Account`) |
| Account service host | `http://185.185.143.231:5051` |
| MailHog host | `http://185.185.143.231:5025` |
| Contract | `swagger/swagger_account.json` |
| Live swagger (for regen) | `http://185.185.143.231:5051/swagger/Account/swagger.json` |
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
| Language | Python — `requires-python = ">=3.13,<4.0"`; venv is **3.14**; CI runs 3.14 |
| Dependency manager | **Poetry**, `package-mode = false` (installed with `--no-root`) |
| HTTP client | **httpx** (async) — reached **only** through the external `restclient` package's `RestClient` |
| API clients | **restcodegen-generated** (`AccountApi`, `LoginApi`) from a **customized template** in `codegen_templates/`; the mailhog client is hand-written on `RestClient` |
| Client generation | **restcodegen 2.0.1** — a local dev step, **never run in CI** |
| Test runner | **pytest 9.1.0** + **pytest-asyncio** (`asyncio_mode = auto`, session-scoped loop) |
| Data models / validation | **pydantic v2** (`extra="forbid"`, camelCase aliases) — generated into one `api_models.py` |
| Assertions | **PyHamcrest** matchers + **assertpy** soft assertions |
| Reporting | **Allure** (`allure-pytest`) |
| API coverage | **swagger-coverage 3.5.2** (off by default; needs Java + `:` in paths) |
| Logging | **structlog** + **curlify2** — via the external `RestClient` |
| Config | **vyper-config** (YAML env files + CLI overrides) |
| Notifications | **pytest-telegram-notifier** + **pyTelegramBotAPI** |
| Shared REST client | **`rest-client`** — external git dependency (`git+https://github.com/SDET-org/rest_client.git@main`), imported as `restclient` |
| Linter / formatter | **Ruff** (line length 120; rules `E`,`F`,`I`,`UP`,`ANN`,`B`,`SIM`) |
| Type checker | **mypy** (strict-leaning; config in `pyproject.toml`) |
| Git hooks | **pre-commit** (ruff format, ruff check, mypy) |

### 2.1 Linter / type configuration highlights

Both tools live in **`pyproject.toml`** (`[tool.ruff]` / `[tool.mypy]`); there is
no standalone `mypy.ini`. Strict flags (`warn_return_any`, `disallow_any_generics`,
`warn_unused_ignores`, `no_implicit_optional`, `strict_equality`,
`warn_unreachable`, ruff `ANN401`) make annotations meaningful, so `-> Any` is an
error rather than an easy escape hatch.

**Import overrides:** `restclient.*` → `follow_untyped_imports` (the package ships
no `py.typed` but its source is fully annotated); `vyper`/`curlify2`/
`swagger_coverage_py`/`assertpy` → `ignore_missing_imports`; `checkers.*` →
`disable_error_code = ["arg-type"]` (pyhamcrest stub defect).

**Per-file ruff ignores:**
- `tests/**` → `ANN201` (test functions return `None`).
- `clients/http/dm_api_account/**` → `ANN401`, `UP009`, `I001` — restcodegen
  reproduces these on every regen (the `**kwargs: Any` httpx passthrough, the
  `# coding: utf-8` header, and its import order), so they are ignored rather than
  hand-fixed on generated files that would just be overwritten.
- `clients/http/__init__.py` → `UP009` (restcodegen also writes this init with the
  utf-8 header).

**Remaining deliberate `Any`:** the parsed MailHog message body in
`_get_token_by_login` is `dict[str, Any]` (arbitrary JSON). Elsewhere `Any` was
removed in favour of concrete types (see §4).

---

## 3. Repository Structure

```
.
├── clients/http/                     # Low-level API clients (transport + typed methods)
│   ├── dm_api_account/                # restcodegen-GENERATED account client
│   │   ├── apis/
│   │   │   ├── account_api.py         # AccountApi(RestClient): POST/GET account, PUT token/email/password, POST password
│   │   │   └── login_api.py           # LoginApi(RestClient): POST login, DELETE login, DELETE login/all
│   │   └── models/
│   │       └── api_models.py          # ALL pydantic DTOs in one file (+ manual UserDetails.info validator)
│   ├── api_mailhog/apis/mailhog_api.py# MailhogApi(RestClient): GET /api/v2/messages (hand-written)
│   └── schemas/dm_api_account.json    # OpenAPI schema snapshot restcodegen wrote during generation
├── codegen_templates/                 # Customized restcodegen templates (see §5)
│   ├── api_client.jinja2              # EDITED: RestClient dialect (path=/json=, api_client: RestClient)
│   ├── apis_init.jinja2              # copied default (unchanged)
│   └── header.jinja2                 # copied default (unchanged)
├── services/                          # Facades that group clients per service
│   ├── dm_api_account.py             # DmApiAccount → builds ONE RestClient, shares it with account_api + login_api
│   └── api_mailhog.py                # MailHogApi → {mailhog_api}
├── helpers/
│   └── account_helper.py             # AccountHelper: business flows + generic retrier; concrete return types (§4)
├── checkers/                          # Reusable response assertions
│   ├── http_checkers.py              # check_status_code_http (context manager)
│   ├── get_v1_account_checker.py     # GetV1AccountChecker (hamcrest + assertpy)
│   └── post_v1_account_checker.py    # PostV1AccountChecker (hamcrest)
├── tg_notifier/bot.py                 # Standalone Telegram sender for the swagger-coverage report
├── tests/
│   ├── conftest.py                   # Fixtures, CLI options, config loading, swagger-cov setup
│   ├── user.py                       # User model (test-user credentials)
│   └── functional/                   # Functional tests grouped by service/endpoint
├── config/                            # Per-environment config (stg.yaml default; prod.yaml == stg.yaml)
├── swagger/swagger_account.json       # OpenAPI 3.0.1 contract for the account service
├── .github/workflows/python-tests.yml # CI caller → reusable workflow in SDET-org/common-pipeline
├── pyproject.toml / poetry.lock       # Deps (+ restcodegen, rest-client) and [tool.ruff]/[tool.mypy] config
├── .pre-commit-config.yaml            # Git hook config
├── README.md                          # Setup & tooling guide (incl. the regeneration procedure)
├── project-inventory.md               # THIS dated snapshot (now tracked on this branch)
└── to_think_about.md                  # Backlog of deferred technical ideas (RU)
```

---

## 4. Architecture — Layered Design (Variant 2)

Requests flow through clearly separated layers. **Both** the account and MailHog
clients ride on the external `RestClient`; the account clients do so because the
customized restcodegen template makes them call `RestClient` directly, so **no
`ApiClient` wrapper exists** anymore.

```
Test → Checker (assert)          Test → AccountHelper (business flow)
                                          │
                                          ▼
                                 DmApiAccount            MailHogApi   ← service facades
                                          │                   │
                                          ▼                   ▼
                        AccountApi / LoginApi (generated)   MailhogApi
                                          │                   │  (subclass)
                                          └────────┬──────────┘
                                                   ▼
                                              RestClient          ← transport (external
                                             (external pkg)         `restclient`, wraps httpx)
```

- **Generated clients speak the `RestClient` dialect.** Each method calls
  `self.api_client.<verb>(path=..., json=model.model_dump(mode="json", by_alias=True,
  exclude_none=True), headers=...)` and types `api_client: RestClient`. Success
  responses are parsed with `model_validate_json`. Header params are filtered with
  a truthy test, so unset optionals **and** the empty-string auth token (the
  helper's "use the persisted session token" sentinel) are dropped.
- **`DmApiAccount`** builds one `RestClient(configuration)` and passes it to both
  `AccountApi` and `LoginApi`, so a single `set_headers(...)` (in
  `AccountHelper.authenticate_client`) authenticates every later request from
  either client.
- **`AccountHelper`** now has **concrete return types** (mentor comment #1):
  - `@overload` pairs keyed on `validate_response: Literal[True] | Literal[False]`
    return `UserEnvelope` / `UserDetailsEnvelope` on the parsing branch and
    `httpx.Response` on the raw branch (calling the generated `x(...)` vs
    `x_with_http_info(...)` method per branch).
  - `register_new_user` / `user_logout` / `user_logout_all` → `httpx.Response`.
  - A generic `retrier[**P, T]` narrows the emailed-token getters to `str`.
  - The reset token is converted with `UUID(token)` to match the generated
    `ChangePassword.token: UUID` field.
- **Manual post-generation patch:** the `UserDetails.info` `field_validator` (maps
  the API's empty-string `info` to `None`) is **not** emitted by restcodegen and
  must be re-applied after every regen (see §5 and `api-notes.md`).

---

## 5. Local Regeneration Procedure

The generated clients are committed; **regeneration is a local dev step and is
never run in CI** (CI installs deps and runs ruff/mypy/pytest on committed code
only). The customized template lives in `codegen_templates/` (committed).

1. Regenerate from the live swagger **with the custom template** (`-td` /
   `--templates-dir` replaces the whole template dir, so all three defaults are
   copied in and only `api_client.jinja2` is edited):

   ```bash
   poetry run restcodegen generate -u "http://185.185.143.231:5051/swagger/Account/swagger.json" -s dm_api_account -a -td codegen_templates
   ```

2. Re-apply the `UserDetails.info` `field_validator` in
   `clients/http/dm_api_account/models/api_models.py` (empty string → `None`).
3. Run `poetry run ruff format .`, then `ruff check` / `mypy` / `pytest`.

The four edits in `codegen_templates/api_client.jinja2` vs the restcodegen 2.0.1
default: import `RestClient`, type `__init__(api_client: RestClient)`, filter
header values by truthiness (drops `None` and the empty-string token), and call the
transport with `path=` + `json=model.model_dump(mode="json", ...)` instead of
`url=` + `content=`.

---

## 6. Notes & Gotchas

- `prod.yaml` == `stg.yaml` (no real prod env yet).
- `config/*.yaml` holds a plaintext training login/password — real secrets go in
  the gitignored `.env`.
- Several declared deps (`aiohttp`, `marshmallow`, `faker`, `retrying`, …) are
  unused; the client is httpx (via `restclient`), models are pydantic, retries use
  the custom `retrier`.
- `swagger/swagger_account.json` is the declared **contract, not a guarantee**;
  when it disagrees with the live API, the live response wins (see `api-notes.md`).
