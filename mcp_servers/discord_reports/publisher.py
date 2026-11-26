"""Discord Webhook publisher, token redaction, 429 backoff, and SHA-256 idempotency ledger."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

from .formatter import (
    DiscordMessagePlan,
    InMemoryAttachment,
    VALID_CHANNEL_TYPES,
    sanitize_markdown_attachment,
)

_WEBHOOK_TOKEN_RE = re.compile(r"(/webhooks/\d+/)[^\s\"'?&/]+")


class DiscordPublishError(RuntimeError):
    """Raised when Discord webhook delivery fails; message is guaranteed token-redacted."""


def redact_webhook_url(text: str, raw_webhook_url: str | None = None) -> str:
    """Scrub Discord webhook tokens from URLs, error messages, and logs."""
    redacted = _WEBHOOK_TOKEN_RE.sub(r"\1***", text)
    if raw_webhook_url:
        token = raw_webhook_url.rstrip("/").rsplit("/", 1)[-1]
        if token and len(token) > 6:
            redacted = redacted.replace(token, "***")
    return redacted


def compute_content_sha256(repo_root: Path, files: list[Path]) -> str:
    """Compute a deterministic SHA-256 digest over sorted (relative_path, content) pairs."""
    hasher = hashlib.sha256()
    unique_files = sorted(
        {p.resolve() for p in files if p.is_file()},
        key=lambda p: p.relative_to(repo_root.resolve()).as_posix(),
    )
    resolved_root = repo_root.resolve()
    for file_path in unique_files:
        rel = file_path.relative_to(resolved_root).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(file_path.read_bytes())
        hasher.update(b"\x00")
    return hasher.hexdigest()


class DeliveryLedger:
    """JSON idempotency ledger keyed by date (data/discord_delivery_log.json)."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = ledger_path

    def load(self) -> dict[str, dict]:
        """Load ledger entries from disk, returning empty dict if absent or unreadable."""
        if not self.ledger_path.is_file():
            return {}
        try:
            data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def get(self, date: str) -> dict | None:
        """Return ledger entry for a given YYYY-MM-DD date, if present."""
        entry = self.load().get(date)
        return entry if isinstance(entry, dict) else None

    def get_all(self) -> dict[str, dict]:
        """Return all stored ledger entries."""
        return self.load()

    def should_skip(
        self,
        date: str,
        *,
        mode: str,
        include_source_files: bool,
        content_sha256: str,
        force: bool = False,
    ) -> tuple[bool, dict | None]:
        """Return (True, existing_entry) when identical content/config was already delivered."""
        if force:
            return False, None
        existing = self.get(date)
        if not existing:
            return False, None
        if (
            existing.get("mode") == mode
            and existing.get("include_source_files") == include_source_files
            and existing.get("content_sha256") == content_sha256
        ):
            return True, existing
        return False, existing

    def record(
        self,
        *,
        date: str,
        mode: str,
        include_source_files: bool,
        content_sha256: str,
        thread_id: str | None,
        messages_sent: int,
        files_attached: int,
        thread_ids: list[str] | None = None,
        posts_created: int | None = None,
    ) -> dict:
        """Persist a delivery receipt entry to disk."""
        data = self.load()
        entry: dict = {
            "date": date,
            "mode": mode,
            "include_source_files": include_source_files,
            "content_sha256": content_sha256,
            "thread_id": thread_id,
            "messages_sent": messages_sent,
            "files_attached": files_attached,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }
        if thread_ids is not None:
            entry["thread_ids"] = thread_ids
        if posts_created is not None:
            entry["posts_created"] = posts_created
        data[date] = entry
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return entry


class DiscordWebhookPublisher:
    """HTTPX-based Discord Webhook client supporting multi-thread Forum posts, attachments, and 429 retries."""

    def __init__(
        self,
        webhook_url: str,
        *,
        channel_type: str = "forum",
        username: str = "Daily AI Digest",
        transport: httpx.BaseTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        max_retries: int = 5,
        min_request_interval: float = 0.25,
        timeout: float = 30.0,
    ) -> None:
        if not webhook_url or not webhook_url.strip():
            raise ValueError("DISCORD_WEBHOOK_URL must not be empty")
        if channel_type not in VALID_CHANNEL_TYPES:
            raise ValueError(
                f"Unsupported channel_type '{channel_type}': expected 'forum' or 'text'"
            )
        self.webhook_url = webhook_url.strip().split("?", 1)[0].rstrip("/")
        self.channel_type = channel_type
        self.username = username
        self._transport = transport
        self._sleep_fn = sleep_fn
        self._max_retries = max_retries
        self._min_request_interval = max(0.0, min_request_interval)
        self._timeout = timeout

    def _build_url(self, thread_id: str | None = None) -> str:
        url = f"{self.webhook_url}?wait=true"
        if thread_id:
            url += f"&thread_id={thread_id}"
        return url

    def _extract_retry_after(self, response: httpx.Response) -> float:
        header_val = response.headers.get("Retry-After")
        if header_val:
            try:
                return max(0.0, float(header_val))
            except ValueError:
                pass
        try:
            body = response.json()
            if isinstance(body, dict) and "retry_after" in body:
                return max(0.0, float(body["retry_after"]))
        except Exception:
            pass
        return 1.0

    def _prepare_attachment_bytes(self, path: Path) -> bytes:
        if path.suffix.lower() == ".md":
            raw_text = path.read_text(encoding="utf-8")
            return sanitize_markdown_attachment(raw_text).encode("utf-8")
        return path.read_bytes()

    def _post_with_retry(
        self,
        client: httpx.Client,
        url: str,
        payload: dict,
        files: list[Path],
        inline_files: list[InMemoryAttachment] | None = None,
    ) -> dict:
        attempt = 0
        mem_files = inline_files or []
        while True:
            try:
                if files or mem_files:
                    multipart_files = []
                    slot = 0
                    for f in files:
                        multipart_files.append(
                            (
                                f"files[{slot}]",
                                (f.name, self._prepare_attachment_bytes(f), "text/markdown; charset=utf-8"),
                            )
                        )
                        slot += 1
                    for mem in mem_files:
                        multipart_files.append(
                            (
                                f"files[{slot}]",
                                (mem.filename, mem.content, mem.content_type),
                            )
                        )
                        slot += 1
                    response = client.post(
                        url,
                        data={"payload_json": json.dumps(payload, ensure_ascii=False)},
                        files=multipart_files,
                    )
                else:
                    response = client.post(url, json=payload)
            except httpx.HTTPError as exc:
                msg = redact_webhook_url(f"HTTP transport error: {exc}", self.webhook_url)
                raise DiscordPublishError(msg) from exc

            if response.status_code == 429:
                if attempt >= self._max_retries:
                    raise DiscordPublishError(
                        redact_webhook_url(
                            f"Discord rate limit (429) persisted after {self._max_retries} retries",
                            self.webhook_url,
                        )
                    )
                delay = self._extract_retry_after(response)
                self._sleep_fn(delay)
                attempt += 1
                continue

            if response.status_code >= 400:
                body_text = redact_webhook_url(response.text[:400], self.webhook_url)
                lowered = body_text.lower()
                if response.status_code == 400 and any(
                    hint in lowered
                    for hint in ("thread_name", "forum", "220001", "220003", "thread")
                ):
                    raise DiscordPublishError(
                        f"Discord returned HTTP 400 ({body_text}). "
                        f"Check DISCORD_CHANNEL_TYPE (currently '{self.channel_type}'): "
                        "use 'forum' for Forum/Media channels or 'text' for standard Text channels."
                    )
                raise DiscordPublishError(
                    f"Discord webhook failed with HTTP {response.status_code}: {body_text}"
                )

            if response.status_code == 204 or not response.content:
                return {}
            try:
                parsed = response.json()
                return parsed if isinstance(parsed, dict) else {}
            except ValueError:
                return {}

    def publish_plans(
        self,
        plans: list[DiscordMessagePlan],
        *,
        existing_thread_id: str | None = None,
    ) -> dict:
        """Publish ordered DiscordMessagePlans; each plan with thread_name opens a new Forum post."""
        if not plans:
            return {
                "thread_id": existing_thread_id,
                "thread_ids": [existing_thread_id] if existing_thread_id else [],
                "posts_created": 0,
                "messages_sent": 0,
                "files_attached": 0,
            }

        current_thread_id = existing_thread_id
        primary_thread_id = existing_thread_id
        thread_ids: list[str] = []
        messages_sent = 0
        files_attached = 0

        client_kwargs: dict = {"timeout": self._timeout}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        with httpx.Client(**client_kwargs) as client:
            for idx, plan in enumerate(plans):
                if idx > 0 and self._min_request_interval > 0:
                    self._sleep_fn(self._min_request_interval)

                payload: dict = {}
                if self.username:
                    payload["username"] = self.username
                if plan.content:
                    payload["content"] = plan.content
                if plan.embeds:
                    payload["embeds"] = plan.embeds

                starts_new_forum_post = (
                    self.channel_type == "forum"
                    and existing_thread_id is None
                    and plan.thread_name is not None
                )

                if self.channel_type == "forum":
                    if starts_new_forum_post:
                        payload["thread_name"] = plan.thread_name
                        url = self._build_url(thread_id=None)
                    else:
                        url = self._build_url(thread_id=current_thread_id)
                else:
                    url = self._build_url(thread_id=None)

                resp_json = self._post_with_retry(client, url, payload, plan.files, plan.inline_files)
                messages_sent += 1
                files_attached += len(plan.files) + len(plan.inline_files)

                if starts_new_forum_post:
                    captured = resp_json.get("channel_id")
                    if captured:
                        captured_str = str(captured)
                        current_thread_id = captured_str
                        thread_ids.append(captured_str)
                        if plan.is_primary_thread or primary_thread_id is None:
                            primary_thread_id = captured_str

        return {
            "thread_id": primary_thread_id,
            "thread_ids": thread_ids if thread_ids else ([existing_thread_id] if existing_thread_id else []),
            "posts_created": len(thread_ids),
            "messages_sent": messages_sent,
            "files_attached": files_attached,
        }
