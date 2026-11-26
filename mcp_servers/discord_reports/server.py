"""FastMCP stdio server exposing Discord report delivery tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

import httpx

if __package__ in (None, ""):
    # Allow running directly via `python server.py` inside mcp_servers/discord_reports
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from mcp_servers.discord_reports.formatter import (
        build_daily_delivery_plan,
        build_single_report_plan,
        discover_daily_reports,
        normalize_date,
    )
    from mcp_servers.discord_reports.publisher import (
        DeliveryLedger,
        DiscordWebhookPublisher,
        compute_content_sha256,
        redact_webhook_url,
    )
else:
    from .formatter import (
        build_daily_delivery_plan,
        build_single_report_plan,
        discover_daily_reports,
        normalize_date,
    )
    from .publisher import (
        DeliveryLedger,
        DiscordWebhookPublisher,
        compute_content_sha256,
        redact_webhook_url,
    )


class _FallbackFastMCP:
    """Offline-safe shim when `mcp` SDK is absent (e.g. unit testing under system Python)."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._registered_tools: list[str] = []

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self._registered_tools.append(fn.__name__)
            return fn

        return _decorator

    def run(self, transport: str = "stdio") -> None:
        raise RuntimeError(
            "The 'mcp' package is required to run the MCP server. "
            "Run 'uv sync --directory mcp_servers/discord_reports' first."
        )


try:
    from mcp.server import MCPServer as FastMCP  # type: ignore[import-not-found]
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]
    except ImportError:
        FastMCP = _FallbackFastMCP  # type: ignore[assignment,misc]


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_effective_data_root(repo_root: Path | None = None) -> Path:
    """Resolve Data Repo root: explicit arg -> KNOWLEDGE_LOOP_DATA_REPO -> workspace.local.env -> Home Root."""
    if repo_root is not None:
        return repo_root.resolve()
    try:
        from scripts.lib.workspace_paths import resolve_data_repo

        return resolve_data_repo(home_root=DEFAULT_REPO_ROOT, require_exists=False)
    except Exception:
        env_dir = os.environ.get("KNOWLEDGE_LOOP_DATA_REPO", "").strip()
        if env_dir:
            cand = Path(os.path.expanduser(env_dir))
            if not cand.is_absolute():
                cand = DEFAULT_REPO_ROOT / cand
            return cand.resolve()
        return DEFAULT_REPO_ROOT.resolve()

TOOL_NAMES = [
    "discord_publish_daily_reports",
    "discord_send_report_file",
    "discord_delivery_status",
]

mcp = FastMCP("discord-reports")


def resolve_report_path(report_path: str, repo_root: Path) -> Path:
    """Resolve and validate that report_path stays strictly inside <repo_root>/reports/."""
    if not report_path or not report_path.strip():
        raise ValueError("Invalid report_path: must reside within reports/")
    reports_dir = (repo_root / "reports").resolve()
    raw = Path(report_path.strip())
    candidate = raw.resolve() if raw.is_absolute() else (repo_root / raw).resolve()

    if not candidate.is_relative_to(reports_dir) or candidate == reports_dir:
        raise ValueError("Invalid report_path: must reside within reports/")
    if not candidate.is_file():
        raise ValueError(f"Report file not found: {candidate.relative_to(reports_dir.parent).as_posix()}")
    if candidate.suffix.lower() != ".md":
        raise ValueError("Invalid report_path: only .md report files are supported")
    return candidate


def _plan_preview(plans: list[Any]) -> list[dict]:
    return [
        {
            "thread_name": p.thread_name,
            "content": p.content,
            "embeds": p.embeds,
            "files": [f.name for f in p.files] + [f.filename for f in getattr(p, "inline_files", [])],
        }
        for p in plans
    ]


def _publish_daily_reports_impl(
    date: str | None = None,
    mode: str | None = None,
    include_source_files: bool = False,
    force: bool = False,
    dry_run: bool = False,
    *,
    repo_root: Path | None = None,
    transport: httpx.BaseTransport | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> dict:
    root = resolve_effective_data_root(repo_root)
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    channel_type = os.environ.get("DISCORD_CHANNEL_TYPE", "forum").strip().lower() or "forum"
    eff_mode = (mode or os.environ.get("DISCORD_DEFAULT_MODE", "per_report")).strip().lower() or "per_report"
    username = os.environ.get("DISCORD_USERNAME", "Daily AI Digest").strip() or "Daily AI Digest"

    try:
        norm_date = normalize_date(date)
        bundle = discover_daily_reports(root, norm_date)
        if bundle.distillation is None and not bundle.sources:
            return {
                "status": "no_reports",
                "date": norm_date,
                "messages_sent": 0,
                "files_attached": 0,
            }

        plans = build_daily_delivery_plan(
            bundle,
            mode=eff_mode,
            include_source_files=include_source_files,
            channel_type=channel_type,
        )

        included_files: list[Path] = []
        if bundle.distillation is not None:
            included_files.append(bundle.distillation.path)
        if eff_mode != "distillation_only":
            included_files.extend(src.path for src in bundle.sources)
        content_sha = compute_content_sha256(root, included_files)

        if dry_run:
            posts_planned = sum(1 for p in plans if p.thread_name is not None)
            return {
                "status": "dry_run",
                "date": norm_date,
                "mode": eff_mode,
                "channel_type": channel_type,
                "content_sha256": content_sha,
                "posts_planned": posts_planned,
                "messages_planned": len(plans),
                "files_planned": sum(len(p.files) + len(p.inline_files) for p in plans),
                "payload_preview": _plan_preview(plans),
            }

        if not webhook_url:
            return {
                "status": "error",
                "date": norm_date,
                "error": "DISCORD_WEBHOOK_URL is not configured",
            }

        ledger = DeliveryLedger(root / "data" / "discord_delivery_log.json")
        should_skip, existing = ledger.should_skip(
            norm_date,
            mode=eff_mode,
            include_source_files=include_source_files,
            content_sha256=content_sha,
            force=force,
        )
        if should_skip and existing is not None:
            return {
                "status": "skipped",
                "reason": "already_delivered",
                "date": norm_date,
                "mode": eff_mode,
                "thread_id": existing.get("thread_id"),
                "messages_sent": 0,
                "files_attached": 0,
            }

        pub_kwargs: dict[str, Any] = {
            "channel_type": channel_type,
            "username": username,
            "transport": transport,
        }
        if sleep_fn is not None:
            pub_kwargs["sleep_fn"] = sleep_fn
        publisher = DiscordWebhookPublisher(webhook_url, **pub_kwargs)
        result = publisher.publish_plans(plans)

        ledger.record(
            date=norm_date,
            mode=eff_mode,
            include_source_files=include_source_files,
            content_sha256=content_sha,
            thread_id=result.get("thread_id"),
            thread_ids=result.get("thread_ids"),
            posts_created=result.get("posts_created"),
            messages_sent=result["messages_sent"],
            files_attached=result["files_attached"],
        )

        return {
            "status": "sent",
            "date": norm_date,
            "mode": eff_mode,
            "channel_type": channel_type,
            "thread_id": result.get("thread_id"),
            "thread_ids": result.get("thread_ids", []),
            "posts_created": result.get("posts_created", 0),
            "messages_sent": result["messages_sent"],
            "files_attached": result["files_attached"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": redact_webhook_url(str(exc), webhook_url or None),
        }


def _send_report_file_impl(
    report_path: str,
    thread_id: str | None = None,
    attach_markdown: bool = False,
    dry_run: bool = False,
    *,
    repo_root: Path | None = None,
    transport: httpx.BaseTransport | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> dict:
    root = resolve_effective_data_root(repo_root)
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    channel_type = os.environ.get("DISCORD_CHANNEL_TYPE", "forum").strip().lower() or "forum"
    username = os.environ.get("DISCORD_USERNAME", "Daily AI Digest").strip() or "Daily AI Digest"

    try:
        resolved = resolve_report_path(report_path, root)
        plans = build_single_report_plan(
            resolved,
            root,
            attach_markdown=attach_markdown,
            channel_type=channel_type,
            thread_id=thread_id,
        )

        if dry_run:
            return {
                "status": "dry_run",
                "report_path": resolved.relative_to(root).as_posix(),
                "channel_type": channel_type,
                "messages_planned": len(plans),
                "files_planned": sum(len(p.files) + len(p.inline_files) for p in plans),
                "payload_preview": _plan_preview(plans),
            }

        if not webhook_url:
            return {
                "status": "error",
                "error": "DISCORD_WEBHOOK_URL is not configured",
            }

        pub_kwargs: dict[str, Any] = {
            "channel_type": channel_type,
            "username": username,
            "transport": transport,
        }
        if sleep_fn is not None:
            pub_kwargs["sleep_fn"] = sleep_fn
        publisher = DiscordWebhookPublisher(webhook_url, **pub_kwargs)
        result = publisher.publish_plans(plans, existing_thread_id=thread_id)
        return {
            "status": "sent",
            "report_path": resolved.relative_to(root).as_posix(),
            "channel_type": channel_type,
            "thread_id": result.get("thread_id"),
            "messages_sent": result["messages_sent"],
            "files_attached": result["files_attached"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": redact_webhook_url(str(exc), webhook_url or None),
        }


def _delivery_status_impl(
    date: str | None = None,
    *,
    repo_root: Path | None = None,
) -> dict:
    root = resolve_effective_data_root(repo_root)
    try:
        ledger = DeliveryLedger(root / "data" / "discord_delivery_log.json")
        if date is not None and str(date).strip():
            norm_date = normalize_date(date)
            entry = ledger.get(norm_date)
            return {
                "status": "ok",
                "date": norm_date,
                "delivered": entry is not None,
                "entry": entry,
            }
        entries = ledger.get_all()
        return {
            "status": "ok",
            "count": len(entries),
            "entries": entries,
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": redact_webhook_url(str(exc)),
        }


@mcp.tool()
def discord_publish_daily_reports(
    date: str | None = None,
    mode: str | None = None,
    include_source_files: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    """Publish daily-workflow reports formatted as native Discord Markdown."""
    return _publish_daily_reports_impl(
        date=date,
        mode=mode,
        include_source_files=include_source_files,
        force=force,
        dry_run=dry_run,
    )


@mcp.tool()
def discord_send_report_file(
    report_path: str,
    thread_id: str | None = None,
    attach_markdown: bool = False,
    dry_run: bool = False,
) -> dict:
    """Send a single Markdown report under reports/ formatted as native Discord Markdown."""
    return _send_report_file_impl(
        report_path=report_path,
        thread_id=thread_id,
        attach_markdown=attach_markdown,
        dry_run=dry_run,
    )


@mcp.tool()
def discord_delivery_status(date: str | None = None) -> dict:
    """Inspect Discord report delivery status from data/discord_delivery_log.json."""
    return _delivery_status_impl(date=date)


if __name__ == "__main__":
    mcp.run(transport="stdio")
