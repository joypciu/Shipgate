from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from shipgate.github import GitHub
from shipgate.review import Reviewer
from shipgate.store import DeliveryStore
from shipgate.webhook import WebhookError, handle_webhook


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
    app = FastAPI(title="Shipgate", version="0.1.0")
    app.state.reviewer = reviewer
    app.state.store = store
    app.state.secret = secret
    app.state.token = token

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/github/webhook")
    async def webhook(request: Request) -> dict:
        body = await request.body()
        try:
            return handle_webhook(
                body,
                event=request.headers.get("X-GitHub-Event", ""),
                signature=request.headers.get("X-Hub-Signature-256"),
                secret=app.state.secret,
                github=GitHub(app.state.token),
                store=app.state.store,
                review_diff=app.state.reviewer.review,
            )
        except WebhookError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail) from exc

    return app
