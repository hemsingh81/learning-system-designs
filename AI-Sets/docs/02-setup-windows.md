# 02 — Setup on Windows

This project lives at `C:\Users\hemsingh9\source\repos\AI-Sets`. Every
command below assumes that is your current directory in PowerShell.

## Prerequisites

- **Python 3.11 or newer.** This machine has Python 3.14.4, which is fine.
  Check yours with:
  ```powershell
  python --version
  ```
  If that fails, install Python from https://www.python.org/downloads/ and
  make sure "Add python.exe to PATH" is checked during install.
- **PowerShell** (built into Windows 11 — you already have it).
- **No API key required.** The whole tutorial runs offline by default.

## One-command setup

```powershell
cd C:\Users\hemsingh9\source\repos\AI-Sets
.\scripts\setup.ps1
```

If PowerShell refuses to run the script with a message like *"running
scripts is disabled on this system"*, that is Windows' execution policy
protecting you from unknown scripts. Allow it for THIS session only
(safe — it resets when you close the window):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run `.\scripts\setup.ps1` again.

### What `setup.ps1` does, step by step

1. Checks that `python` is on your PATH.
2. Creates a virtual environment at `.venv` (an isolated Python install just
   for this project — the same idea as a `node_modules` folder, but for
   Python packages, so they don't clash with anything else on your machine).
3. Activates that virtual environment for the rest of the script.
4. Installs the project's dependencies (`anthropic`, `pydantic`, `fastapi`,
   `pytest`, etc. — the full list is in `pyproject.toml`).
5. Copies `.env.example` to `.env` if you don't have one yet. The default
   `.env` has `LLM_BACKEND=fake`, so nothing here talks to the internet.
6. Generates the sample data (`data\tickets.json`, `data\orders.db`,
   `data\app.log`, `data\metrics.json`, `data\runbooks\*.md`) by running
   `data\seed_data.py`.

## Verify everything is ready

```powershell
.\scripts\verify-env.ps1
```

This prints a checklist — `[OK]` or `[FAIL]` for each item, with an exact
fix command if something failed. Run this any time something feels wrong;
it is the fastest way to tell "my setup is broken" from "my code has a bug".

## Running an example

```powershell
.\scripts\run-example.ps1 01_skill_hello
```

This activates the virtual environment, sets `PYTHONPATH` to `src`, and
runs `examples\01_skill_hello.py`. Every example in `examples\` can be run
the same way — just pass its filename (with or without `.py`).

## Running the tests

```powershell
.\scripts\test.ps1
```

Runs everything except the `live` suite (which needs a real API key), with
a coverage report. See [docs/05-testing-ai-code.md](05-testing-ai-code.md)
for the full testing story.

## Opting into the real Anthropic API (optional, not required)

1. Get an API key from https://console.anthropic.com/
2. Open `.env` (create it from `.env.example` if you haven't run setup yet)
   and set:
   ```
   LLM_BACKEND=claude
   ANTHROPIC_API_KEY=sk-ant-...your-key-here...
   ```
3. Re-run any example. The exact same code now makes a real API call.
   `docs/07-cost-and-latency.md` tells you roughly what that costs.
4. Set `LLM_BACKEND=fake` again any time to go back to free/offline mode.

## Common setup problems

See [docs/08-troubleshooting.md](08-troubleshooting.md) for the full list.
The two most common:

- **"running scripts is disabled"** → run the `Set-ExecutionPolicy` command
  above.
- **`ModuleNotFoundError: No module named 'aisets'`** → you ran `python`
  directly instead of through `scripts\run-example.ps1` or `scripts\test.ps1`,
  so `PYTHONPATH` was never set. Use the scripts, or set
  `$env:PYTHONPATH = "src"` yourself first.
