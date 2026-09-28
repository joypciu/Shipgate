from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

from shipgate.app_auth import AppCredentials
from shipgate.comment import format_comment
from shipgate.diffmap import inline_comments
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
    root = Path(__file__).resolve().parents[2]
    templates = Jinja2Templates(directory=str(root / "web" / "templates"))
    app.mount("/static", StaticFiles(directory=str(root / "web" / "static")), name="static")

    def page_context(request: Request, **extra):
        return {
            "request": request,
            "provider": os.environ.get("SHIPGATE_PROVIDER", "demo"),
            "github_app": app.state.credentials is not None,
            "sample": SAMPLE_DIFF,
            **extra,
        }

    @app.get("/")
    def home(request: Request):
        return templates.TemplateResponse(request, "home.html", page_context(request, review=None, diff="", error=None))

    @app.post("/reviews")
    async def review_page(request: Request):
        form = await request.form()
        diff = str(form.get("diff") or "")
        if not diff.strip():
            return templates.TemplateResponse(
                request,
                "home.html",
                page_context(request, review=None, diff="", error="Paste a diff first."),
                status_code=400,
            )
        review = app.state.reviewer.review(diff)
        return templates.TemplateResponse(
            request,
            "home.html",
            page_context(
                request,
                review=review,
                diff=diff,
                error=None,
                comment=format_comment(review),
                lines=inline_comments(review, diff),
            ),
        )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/github/webhook")
    async def webhook(request: Request) -> dict:
        body = await request.body()
        try:
            credentials = app.state.credentials
            override = getattr(app.state, "github_override", None)

            def open_github(installation_id: int) -> GitHub:
                with httpx.Client(timeout=30) as client:
                    token = credentials.token_for(installation_id, client)
                return GitHub(token)

            if override is not None:
                github = override
                opener = None
            elif credentials is not None:
                github = None
                opener = open_github
            else:
                github = GitHub(app.state.token)
                opener = None
            return handle_webhook(
                body,
                event=request.headers.get("X-GitHub-Event", ""),
                signature=request.headers.get("X-Hub-Signature-256"),
                secret=app.state.secret,
                github=github,
                open_github=opener,
                store=app.state.store,
                review_diff=app.state.reviewer.review,
            )
        except WebhookError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail) from exc

    return app


SAMPLE_DIFF = """diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -4,7 +4,7 @@ def allow(user):
-    if user.is_authenticated:
+    if True:  # bypass auth
         return True
     return False
"""
