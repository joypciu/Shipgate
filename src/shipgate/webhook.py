from __future__ import annotations

import hashlib
import hmac
import json
from typing import Callable

from shipgate.comment import format_comment
from shipgate.github import GitHub
from shipgate.review import Review
from shipgate.store import DeliveryStore


REVIEW_ACTIONS = {"opened", "synchronize", "reopened"}


class WebhookError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def verify_signature(body: bytes, secret: str, header: str | None) -> bool:
    if not secret or not header:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", header)


def handle_webhook(
    body: bytes,
    *,
    event: str,
    signature: str | None,
    secret: str,
    github: GitHub,
    store: DeliveryStore,
    review_diff: Callable[[str], Review],
) -> dict:
    if not verify_signature(body, secret, signature):
        raise WebhookError(401, "Invalid webhook signature.")
    if event != "pull_request":
        return {"status": "ignored", "event": event}
    payload = json.loads(body)
    action = str(payload.get("action") or "")
    if action not in REVIEW_ACTIONS:
        return {"status": "ignored", "action": action}
    pull = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    sha = pull["head"]["sha"]
    number = int(pull["number"])
    if store.seen(repo, sha):
        return {"status": "duplicate", "sha": sha}
    diff = github.fetch_diff(repo, number)
    review = review_diff(diff)
    comment_id = github.post_comment(repo, number, format_comment(review))
    store.record(repo, sha, review.run_id, comment_id)
    return {"status": "reviewed", "verdict": review.verdict, "sha": sha, "comment_id": comment_id}
