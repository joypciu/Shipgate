from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
import httpx

from shipgate.app_auth import AppCredentials
from shipgate.github import GitHub
from shipgate.review import Reviewer
from shipgate.store import DeliveryStore
from shipgate.webhook import WebhookError, handle_webhook


def load_private_key() -> str:
    raw = os.environ.get("GITHUB_APP_PRIVATE_KEY", "")
    if not raw:
        path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH", "")
        if path:
            raw = Path(path).read_text(encoding="utf-8")
    return raw.replace("\\n", "\n")


def create_app() -> FastAPI:
    bench_root = Path(os.environ.get("DECISION_BENCH_ROOT", Path(__file__).resolve().parents[3] / "decision-bench"))
    data = Path(os.environ.get("SHIPGATE_DATA", "data"))
    reviewer = Reviewer.open(
        bench_root=bench_root,
        database=data / "decision_bench.sqlite",
        provider=os.environ.get("SHIPGATE_PROVIDER", "demo"),
    )
    store = DeliveryStore(data / "shipgate.sqlite")
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    private_key = load_private_key()
    app_id = os.environ.get("GITHUB_APP_ID", "")
    app = FastAPI(title="Shipgate", version="0.1.0")
    app.state.reviewer = reviewer
    app.state.store = store
    app.state.secret = secret
    app.state.token = token
    app.state.credentials = AppCredentials(app_id, private_key) if app_id and private_key else None

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/github/webhook")
    async def webhook(request: Request) -> dict:
        body = await request.body()
        try:
            credentials = app.state.credentials

            def open_github(installation_id: int) -> GitHub:
                with httpx.Client(timeout=30) as client:
                    token = credentials.token_for(installation_id, client)
                return GitHub(token)

            return handle_webhook(
                body,
                event=request.headers.get("X-GitHub-Event", ""),
                signature=request.headers.get("X-Hub-Signature-256"),
                secret=app.state.secret,
                github=None if credentials is not None else GitHub(app.state.token),
                open_github=open_github if credentials is not None else None,
                store=app.state.store,
                review_diff=app.state.reviewer.review,
            )
        except WebhookError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail) from exc

    return app
