# Shipgate

Shipgate is a GitHub App that reviews a pull request and posts one comment: **ship**, **revise**, or **block**, with a file and a reason for each risk.

The decision comes from [Decision Bench](https://github.com/joypciu/decision-bench). The change-risk lead spawns the security, migration, and research checkers. Shipgate posts the lead's schema-valid result. It does not post a second comment for the same commit.

This folder is a local git repository. It does not have a GitHub remote yet.

## Run a review without GitHub

Install Decision Bench from the sibling checkout, then Shipgate:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e E:\decision-bench
pip install -e ".[dev]"
$env:DECISION_BENCH_ROOT = "E:\decision-bench"
pytest
```

`pytest` runs the auth-bypass diff through the demo provider and expects **block** on `auth.py`.

## Webhook

`POST /github/webhook` accepts `pull_request` events whose action is `opened`, `synchronize`, or `reopened`. When `GITHUB_APP_ID` and a private key are set, Shipgate exchanges a short-lived installation token for that delivery. Otherwise it uses `GITHUB_TOKEN`.

- `GITHUB_WEBHOOK_SECRET` verifies `X-Hub-Signature-256`
- `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY` (PEM text, or `GITHUB_APP_PRIVATE_KEY_PATH`) identify the GitHub App
- `GITHUB_TOKEN` is the fallback when the app key is not set
- `DECISION_BENCH_ROOT` is the Decision Bench checkout that contains `packs/`
- `SHIPGATE_PROVIDER` (`demo` by default)

```powershell
$env:DECISION_BENCH_ROOT = "E:\decision-bench"
py -m shipgate
```

The server listens on `127.0.0.1:8010`.
