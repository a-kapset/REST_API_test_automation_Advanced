# Repository for REST API test automation course (advanced part)

## Dependency management (Poetry)

This project uses [Poetry](https://python-poetry.org/) for dependency
management and virtual environments. Dependencies are declared in
`pyproject.toml` and pinned in `poetry.lock`.

### Install Poetry

Install Poetry with the official installer (see the docs:
<https://python-poetry.org/docs/#installing-with-the-official-installer>):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

On Windows (PowerShell):

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Getting started

Configure Poetry to keep the virtual environment inside the project, then
install all dependencies (including sub-dependencies) from the lock file:

```bash
poetry config virtualenvs.in-project true
poetry install --no-root
```

`--no-root` tells Poetry to install only the dependencies, not the project
itself as a package. This creates a `.venv` in the project root.

### Migrating from pip to Poetry

If you were previously using `pip` with `requirements.txt`, the project has
already been migrated to Poetry (`requirements.txt` has been removed). These are
the exact steps that were used to set it up — you only need to re-run them if
you are recreating the environment from scratch:

```bash
# 1. Remove any old pip virtualenv (deactivate it first if it is active)
deactivate            # only if a virtualenv is currently active
rm -rf .venv

# 2. Keep the virtualenv inside the project
poetry config virtualenvs.in-project true

# 3. Create pyproject.toml
poetry init --no-interaction

# 4. Create the virtualenv and lock file
poetry install --no-root

# 5. Add the dependencies (Poetry resolves sub-dependencies automatically)
poetry add aiohttp allure-pytest assertpy curlify distconfig3 environs \
  Faker marshmallow pydantic PyHamcrest pyTelegramBotAPI pytest \
  pytest-telegram-notifier python-dotenv PyYAML requests retrying \
  rootpath setuptools six structlog swagger-coverage toml vyper-config watchdog
```

> If `pyproject.toml` is edited by hand, run `poetry lock` to refresh
> `poetry.lock`, followed by `poetry install --no-root`.

## Running the tests

```bash
poetry run pytest tests
```

Swagger coverage recording is **off by default**, so the suite runs anywhere,
including Windows.

## Linting and formatting (Ruff)

[Ruff](https://docs.astral.sh/ruff/) is used for linting and formatting. It is
installed in the `lint` dependency group inside Poetry's virtualenv, so it is
**not** on your global `PATH` — calling `ruff` directly fails with
`command not found` (or `The term 'ruff' is not recognized` on PowerShell).
Run it through Poetry instead:

```bash
poetry run ruff format .   # format all files (like Black)
poetry run ruff check .    # run the linter
```

> To drop the `poetry run` prefix, activate the environment first with
> `poetry env activate` (Poetry 2.x) and paste the printed command into your
> shell; `ruff` then works directly for that session.

## Type checking (mypy)

[mypy](https://mypy.readthedocs.io/) statically checks type annotations. Like
Ruff, it lives in the `lint` dependency group inside Poetry's virtualenv and is
**not** on your global `PATH`, so run it through Poetry:

```bash
poetry run mypy .   # static type check across the project
```

## Git hooks (pre-commit)

[pre-commit](https://pre-commit.com/) runs checks automatically on every
`git commit`, catching issues before they land in a commit. The hooks it runs
are declared in `.pre-commit-config.yaml`. The current setup runs:

- the standard [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
  (validate YAML, fix end-of-file newlines, strip trailing whitespace, block
  large files);
- **ruff format**, **ruff check**, and **mypy** (see the sections above) as
  `local` hooks that reuse the Poetry virtualenv.

A test run can also be added as a commit hook — the config includes a
commented-out example that runs the `POST /v1/account` base test. It is off by
default because that test hits the live account service, which makes commits
slow and fails when the environment is offline; uncomment it to enable.

### Configure hooks (`.pre-commit-config.yaml`)

Each `repo` entry pins a hook source by `rev` and lists the hook `id`s to run.
`local` hooks instead run a command from this environment via `entry` — here
`poetry run ...`, so they use the same virtualenv as everything else.
`pass_filenames: false` stops pre-commit from appending the staged file paths
to the command (needed for `mypy .` and pytest, which take their own targets).

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v3.2.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: poetry run ruff format
        language: system
        types: [python]
      - id: ruff-check
        name: ruff check
        entry: poetry run ruff check
        language: system
        types: [python]
      - id: mypy
        name: mypy
        entry: poetry run mypy .
        language: system
        types: [python]
        pass_filenames: false
      # Tests can also be run as a commit hook (off by default — hits the live
      # account service, so it slows commits and fails when offline):
      # - id: post-v1-account-base-test
      #   name: post_v1_account base test
      #   entry: poetry run pytest tests/functional/post_v1_account/test_post_v1_account_base.py
      #   language: system
      #   types: [python]
      #   pass_filenames: false
```

To add a hook, append its `id` under an existing `repo`, or add a new `repo`
block.

### Enable the hooks (one-time)

pre-commit is in the `lint` dependency group, so run it through Poetry. After
cloning, install the git hook once so it fires on every commit:

```bash
poetry run pre-commit install   # writes .git/hooks/pre-commit
```

### Run the hooks

Hooks run automatically on `git commit` against staged files. To run them
manually:

```bash
poetry run pre-commit run              # against staged files
poetry run pre-commit run --all-files  # against the whole repo
```

> `pre-commit autoupdate` bumps each `repo`'s `rev` to its latest release.

## Swagger coverage report

Generating the report has two requirements that Windows does not satisfy:

- A **Java runtime** — the swagger-coverage report generator is a Java CLI.
- A filesystem that allows `:` in paths — recorded requests are written to
  `swagger-coverage-output/<host:port>/`, and `:` is illegal in Windows paths.

For that reason the report is generated inside Docker (Linux) using the
dedicated `Dockerfile-sw-coverage` image. Recording is enabled by the
`--swagger-coverage` pytest flag (see `tests/conftest.py`), which that image
passes automatically.

### Generate the report

Build the coverage image:

```bash
docker build -f Dockerfile-sw-coverage -t dm-api-tests-coverage .
```

Run the suite with coverage enabled, mounting the project so the report is
written back to the host. The extra `-v /app/.venv` anonymous volume keeps the
image's Linux virtualenv from being shadowed by the mounted host `.venv`:

```bash
docker run --rm -v "$(pwd)":/app -v /app/.venv dm-api-tests-coverage
```

> **Git Bash on Windows:** prefix the run command with `MSYS_NO_PATHCONV=1` to
> stop Git Bash from rewriting the container path:
>
> ```bash
> MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -v /app/.venv dm-api-tests-coverage
> ```

After the run, open the generated report:

```
swagger-coverage-dm-api-account.html
```

(The report filename comes from `writers.html.filename` in
`swagger-coverage-config-dm-api-reporter.json`.)

### Enabling coverage manually

If you run pytest in a Linux environment yourself (not via the image), enable
recording and report generation with the flag:

```bash
poetry run pytest tests --swagger-coverage
```

## Telegram notifications

The run summary is sent to a Telegram **channel** via the
`pytest-telegram-notifier` plugin. The `--telegram-notifier` flags are already
in `pytest.ini` (`addopts`), so a plain `poetry run pytest tests` run triggers
the notification once credentials are configured.

Two values are required. They are secrets, so they live in a `.env` file
(gitignored) and are loaded in `tests/conftest.py` via `load_dotenv()` directly
into the env vars the plugin consumes:

- `TELEGRAM_BOT_ACCESS_TOKEN` — the bot token from BotFather.
- `TELEGRAM_BOT_CHAT_ID` — the **API** chat id of the channel (a large negative
  number starting with `-100...`), **not** the "Channel ID" shown in the
  Telegram UI.

Copy `.env.example` to `.env` and fill in the values:

```
TELEGRAM_BOT_CHAT_ID=-1004415010693
TELEGRAM_BOT_ACCESS_TOKEN=123456789:AAE...
```

> Keep the token secret — never commit it. `.env` is gitignored; do **not** put
> credentials in the tracked `config/*.yaml` files.

### 1. Create the bot

- In Telegram open **@BotFather** → `/newbot`.
- Set a name and a username ending in `bot`.
- BotFather returns a token like `123456789:AAE...` → this is
  `TELEGRAM_BOT_ACCESS_TOKEN`.
- To rotate a leaked/old token, use **@BotFather** → `/revoke` → select the bot;
  it issues a new token (the old one stops working). Update `.env` with it.

### 2. Create the channel

- Create a channel to receive notifications.
- The numeric "Channel ID" shown in the UI is **not** the API `chat_id` — see
  step 4.

### 3. Add the bot to the channel as administrator (required)

A bot can only post to (and even see) a channel if it is an admin of it.
Without this you get `400 Bad Request: chat not found`.

- Channel → **Manage Channel** → **Administrators** → **Add Admin**.
- Add your bot and enable at least the **Post Messages** permission.

### 4. Get the real channel `chat_id`

For channels the Bot API `chat_id` is a large negative number (`-100...`),
different from the UI "Channel ID". The reliable way to find it:

1. Make sure the bot is a channel admin (step 3).
2. Post any message in the channel.
3. Call `getUpdates` and read `chat.id`:

   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

   Look for an entry like:

   ```json
   "chat": { "id": -1004415010693, "type": "channel", "title": "..." }
   ```

   That `id` is `TELEGRAM_BOT_CHAT_ID`.

Sanity check that the bot can see the channel (should return `"ok": true`):

```
https://api.telegram.org/bot<TOKEN>/getChat?chat_id=<CHAT_ID>
```

### 5. Configure and run

Put the values in `.env` (copied from `.env.example`):

```
TELEGRAM_BOT_CHAT_ID=-1004415010693        # from step 4
TELEGRAM_BOT_ACCESS_TOKEN=123456789:AAE...  # from step 1
```

Then run:

```bash
poetry run pytest tests
```

`telegram-notifier-config.ini` controls **what/when** is sent (message
template, stickers on pass/fail, mentions on failure, etc.).

### Troubleshooting

- **`400 chat not found`** — bot is not an admin of the channel (step 3), or
  the `chat_id` is wrong (use step 4, not the UI number).
- **`getMe` ok but `getChat` fails** — token is valid but the bot can't access
  the chat (again: admin + correct `-100...` id).
- **No notification sent / empty credentials** — check that `.env` exists in the
  project root and both keys are filled in. `load_dotenv()` does not override
  vars already set in the real environment (handy for CI, where you can inject
  them as secrets instead of a file).
