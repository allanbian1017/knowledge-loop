"""Offline pytest verification suite for Discord report delivery (AC-1 through AC-13)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_servers.discord_reports.formatter import (
    MAX_CONTENT_CHARS,
    MAX_EMBED_DESC,
    MAX_EMBED_FIELDS,
    MAX_EMBED_TITLE,
    MAX_EMBEDS_PER_MSG,
    MAX_FIELD_NAME,
    MAX_FIELD_VALUE,
    MAX_FILES_PER_BATCH,
    MAX_FOOTER_TEXT,
    MAX_THREAD_NAME,
    MAX_TOTAL_EMBED_CHARS,
    batch_attachment_files,
    build_daily_delivery_plan,
    chunk_text,
    convert_mermaid_to_discord,
    discover_daily_reports,
    embed_char_count,
    parse_distillation,
    parse_source_report,
    sanitize_for_discord,
    validate_message_plan,
)
from mcp_servers.discord_reports.publisher import (
    DeliveryLedger,
    DiscordPublishError,
    DiscordWebhookPublisher,
    redact_webhook_url,
)
from mcp_servers.discord_reports.server import (
    TOOL_NAMES,
    _delivery_status_impl,
    _publish_daily_reports_impl,
    _send_report_file_impl,
    mcp,
    resolve_report_path,
)

SAMPLE_V5_DISTILLATION = """# Knowledge Distillation: 產碼變免費後，把關與系統設計才是真瓶頸 (2026-11-25)

> **🎯 今日一句話結論**：AI 寫碼幾乎零成本，成敗取決於「把驗收鎖在程式庫外」與「先審計畫再動手」的控制力。

- **⚡ 本週唯一行動**：花 15 分鐘在 `docs/adr/` 寫 1 份決策紀錄。

## 💡 今日核心重點
1. **驗收鎖在程式庫外才防作弊**：AI 會改測資湊綠燈，必須把驗收題移到庫外。
2. **長程協作靠分層與乾淨重啟**：平級搶鎖會拖垮速度，改用分層佇列才不走偏。

## 📊 跨來源主題速覽
| 主題支柱 | 卡在哪裡（白話痛點） | 核心解法直覺 | 對應來源 |
|---|---|---|---|
| **1. 庫外驗收與外殼** | AI改測資且盲跑易走偏 | 庫外場景＋外殼狀態機 | Osmani、StrongDM |
| **2. 分層與常駐架構** | 搶鎖卡死且記憶互相蓋 | 收件匣排隊與乾淨重啟 | Claude、Cursor |

---

## 🔍 主題深入解構（點擊展開細節）

<details>
<summary><b>1. 庫外驗收與外殼控制</b> — 自治權不能超過低成本且防作弊的驗證能力</summary>

- **痛點與脈絡**：AI 寫碼近乎免費，但把測試放在程式庫內易遭偷改測資作弊。
- **關鍵機制與數據**：StrongDM 將端對端場景移出程式庫；Pi 外殼調優讓分數從 39% 升至 55%。
- **系統怎麼串聯**：先鎖死品質再交給多代理長跑。

</details>

<details>
<summary>📚 <b>今日合成來源清單</b>（Sources — 2 篇報告）</summary>

- [Brief_AI.md](../Newsletter_2026_11_25/Brief_AI.md)
- [addyosmani.md](../Website_2026_11_25/addyosmani.md)

</details>
"""

SAMPLE_LEGACY_DISTILLATION = """# Knowledge Distillation: AI 系統信任邊界 (2026-11-23)

## 📝 Executive Summary
今日的技術訊號指向同一個核心工程命題：當產出規模超越人工逐行審查極限時，必須以確定性驗證建立信任。

---

## 🏗️ 1. 確定性驗證邊界
- **規格鎖定**：以多套獨立檢查器驗收。

---

## 🚀 Strategic Takeaway
不要為你讀不完的產出背書。

---
*Synthesized from:*
- [Report.md](../Newsletter_2026_11_23/Report.md)
"""

SAMPLE_V5_SOURCE = """# Sample Source Article

> **🎯 一句話結論**：先審 200 行計畫勝過事後啃 2,000 行程式。

- **⭐ 推薦度**：★★★★★（直擊核心）
- **⚡ 下一步**：花 15 分鐘寫 1 份 ADR
- **🔗 來源**：[Website：Example](https://example.com/article)

## 💡 核心重點
1. **重點一**：用確定性狀態機限制迴圈。

```mermaid
flowchart LR
    A[Start] --> B[End]
```
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _assert_all_discord_limits(plans) -> None:
    for plan in plans:
        validate_message_plan(plan)
        if plan.content is not None:
            assert len(plan.content) <= MAX_CONTENT_CHARS
        if plan.thread_name is not None:
            assert len(plan.thread_name) <= MAX_THREAD_NAME
        assert len(plan.embeds) <= MAX_EMBEDS_PER_MSG
        total_emb = 0
        for emb in plan.embeds:
            assert len(emb.get("title", "")) <= MAX_EMBED_TITLE
            assert len(emb.get("description", "")) <= MAX_EMBED_DESC
            assert len((emb.get("footer") or {}).get("text", "")) <= MAX_FOOTER_TEXT
            fields = emb.get("fields", [])
            assert len(fields) <= MAX_EMBED_FIELDS
            for f in fields:
                assert len(f.get("name", "")) <= MAX_FIELD_NAME
                assert len(f.get("value", "")) <= MAX_FIELD_VALUE
            total_emb += embed_char_count(emb)
        assert total_emb <= MAX_TOTAL_EMBED_CHARS
        assert len(plan.files) <= MAX_FILES_PER_BATCH


# --- AC-1: Daily Report Discovery ---


def test_discover_daily_reports_sorted_and_early_exit(tmp_path: Path) -> None:
    empty_bundle = discover_daily_reports(tmp_path, "2026-11-25")
    assert empty_bundle.distillation is None
    assert empty_bundle.sources == []

    res = _publish_daily_reports_impl(date="2026-11-25", repo_root=tmp_path)
    assert res == {
        "status": "no_reports",
        "date": "2026-11-25",
        "messages_sent": 0,
        "files_attached": 0,
    }

    _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    _write(tmp_path / "reports" / "Website_2026_11_25" / "b_site.md", SAMPLE_V5_SOURCE)
    _write(tmp_path / "reports" / "Website_2026_11_25" / "a_site.md", SAMPLE_V5_SOURCE)
    _write(tmp_path / "reports" / "Newsletter_2026_11_25" / "n1.md", SAMPLE_V5_SOURCE)
    _write(tmp_path / "reports" / "Threads_2026_11_25" / "t1.md", SAMPLE_V5_SOURCE)
    _write(tmp_path / "reports" / "YouTube_2026_11_25" / "y1.md", SAMPLE_V5_SOURCE)

    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    assert bundle.distillation is not None
    assert [(s.category, s.path.name) for s in bundle.sources] == [
        ("Newsletter", "n1.md"),
        ("Threads", "t1.md"),
        ("Website", "a_site.md"),
        ("Website", "b_site.md"),
        ("YouTube", "y1.md"),
    ]


def test_sources_without_distillation_fallback(tmp_path: Path) -> None:
    _write(tmp_path / "reports" / "Website_2026_11_25" / "only_site.md", SAMPLE_V5_SOURCE)
    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    assert bundle.distillation is None
    assert len(bundle.sources) == 1

    plans = build_daily_delivery_plan(bundle, mode="digest", include_source_files=True, channel_type="forum")
    _assert_all_discord_limits(plans)
    assert plans[0].thread_name == "📰 Daily Digest — 2026-11-25"
    assert plans[0].files == []
    assert any(p.files == [tmp_path / "reports" / "Website_2026_11_25" / "only_site.md"] for p in plans)


# --- AC-2: v5.0 & Legacy Parsing ---


def test_parse_v5_and_legacy_distillation_and_source(tmp_path: Path) -> None:
    v5_path = _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    v5 = parse_distillation(v5_path, tmp_path)
    assert not v5.is_legacy
    assert "把驗收鎖在程式庫外" in v5.one_liner
    assert "15 分鐘" in v5.weekly_action
    assert len(v5.key_points) == 2
    assert len(v5.overview_bullets) == 2
    # Must exclude "今日合成來源清單" footer accordion
    assert len(v5.pillars) == 1
    assert "1. 庫外驗收與外殼控制" in v5.pillars[0][0]

    legacy_path = _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_23.md",
        SAMPLE_LEGACY_DISTILLATION,
    )
    legacy = parse_distillation(legacy_path, tmp_path)
    assert legacy.is_legacy
    assert "確定性驗證建立信任" in legacy.one_liner
    assert "不要為你讀不完的產出背書" in legacy.weekly_action
    assert len(legacy.pillars) == 1

    long_url = "https://elink.example.com/ss/c/" + ("a" * 640)
    src_path = _write(
        tmp_path / "reports" / "Newsletter_2026_11_25" / "long_url.md",
        SAMPLE_V5_SOURCE.replace("https://example.com/article", long_url),
    )
    src = parse_source_report(src_path, "Newsletter", tmp_path)
    assert src.rating == "★★★★★"
    assert src.source_url == long_url


def test_parse_real_repo_distillations_when_present() -> None:
    for fname in ("Knowledge_Distillation_2026_11_25.md", "Knowledge_Distillation_2026_11_23.md"):
        fpath = REPO_ROOT / "reports" / "distillations" / fname
        if fpath.is_file():
            parsed = parse_distillation(fpath, REPO_ROOT)
            assert parsed.title
            assert parsed.one_liner


# --- AC-3: Discord-Safe Markdown Sanitization ---


def test_sanitize_gfm_table_details_relative_links_and_mermaid() -> None:
    raw = (
        "Intro [local doc](../Website_2026_11_25/a.md) and [ext](https://example.com).\n\n"
        "| 支柱 | 痛點 | 解法 | 來源 |\n"
        "|---|---|---|---|\n"
        "| **1. 閘門** | 亂跑 | 鎖邊界 | Osmani |\n\n"
        "<details>\n<summary><b>1. 標題</b> — 結論</summary>\n\n"
        "- 重點內容\n\n</details>\n\n"
        "```mermaid\nflowchart LR\nA-->B\n```"
    )
    cleaned = sanitize_for_discord(raw, strip_mermaid=True)
    assert "|---|" not in cleaned
    assert "<details>" not in cleaned
    assert "<summary>" not in cleaned
    assert "<b>" not in cleaned
    assert "../Website_2026_11_25/a.md" not in cleaned
    assert "local doc" in cleaned
    assert "[ext](https://example.com)" in cleaned
    assert "• **1. 閘門** — 亂跑 → 鎖邊界 (Osmani)" in cleaned
    assert "### 1. 標題 — 結論" in cleaned
    assert "```mermaid" not in cleaned

    # Also strip <details open> with attributes
    attr_cleaned = sanitize_for_discord(
        "<details open>\n<summary class='x'><b>Open Title</b></summary>\n\nBody\n</details>"
    )
    assert "<details" not in attr_cleaned
    assert "</details>" not in attr_cleaned
    assert "### Open Title" in attr_cleaned


def test_uploaded_md_attachment_is_sanitized_in_memory_without_modifying_disk(tmp_path: Path) -> None:
    dist_path = _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    plans = build_daily_delivery_plan(
        bundle, mode="distillation_only", include_source_files=True, channel_type="forum"
    )

    uploaded_bodies: list[str] = []

    def capture_handler(request: httpx.Request) -> httpx.Response:
        uploaded_bodies.append(request.content.decode("utf-8", errors="ignore"))
        return httpx.Response(200, json={"id": "m1", "channel_id": "t1"})

    pub = DiscordWebhookPublisher(
        "https://discord.com/api/webhooks/111/secret_tok_123",
        channel_type="forum",
        transport=httpx.MockTransport(capture_handler),
        sleep_fn=lambda _: None,
    )
    pub.publish_plans(plans)

    assert len(uploaded_bodies) == 1
    assert "<details" not in uploaded_bodies[0]
    assert "</details>" not in uploaded_bodies[0]
    assert "<summary" not in uploaded_bodies[0]
    assert "### 1. 庫外驗收與外殼控制" in uploaded_bodies[0]
    # Original on-disk file MUST keep <details> intact
    on_disk = dist_path.read_text(encoding="utf-8")
    assert "<details>" in on_disk
    assert "</details>" in on_disk


# --- AC-4: Hard Discord Character & Field Budgets ---


def test_hard_character_and_embed_limits(tmp_path: Path) -> None:
    huge_title = "T" * 350
    huge_one_liner = "結論" * 2000  # 4000 chars
    huge_pillar_body = ("這是一段非常長的段落。" * 150 + "\n\n") * 4
    dist_md = (
        f"# {huge_title}\n\n"
        f"> **🎯 今日一句話結論**：{huge_one_liner}\n\n"
        f"- **⚡ 本週唯一行動**：{'行動' * 100}\n\n"
        "## 💡 今日核心重點\n"
        "1. " + ("重點" * 400) + "\n\n"
        "## 🔍 主題深入解構\n"
        "<details>\n<summary><b>1. 超長支柱</b></summary>\n\n"
        f"{huge_pillar_body}\n</details>\n"
    )
    _write(tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md", dist_md)

    long_url = "https://tracking.example.com/" + ("x" * 650)
    for i in range(30):
        _write(
            tmp_path / "reports" / "Website_2026_11_25" / f"article_{i:02d}.md",
            f"# {'Article ' + str(i) + ' ' + ('X' * 120)}\n\n"
            f"> **🎯 一句話結論**：{'摘要' * 100}\n\n"
            f"- **⭐ 推薦度**：★★★★☆\n"
            f"- **🔗 來源**：[Link]({long_url})\n",
        )

    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    for mode in ("per_report", "digest", "distillation_only", "full"):
        plans = build_daily_delivery_plan(bundle, mode=mode, include_source_files=True, channel_type="forum")
        _assert_all_discord_limits(plans)

    # Also test chunk_text directly with unbroken token > 2000
    chunks = chunk_text("A" * 4500, limit=1900)
    assert len(chunks) == 3
    assert all(len(c) <= 1900 for c in chunks)


# --- AC-5: Multi-File Attachment Batching & Modes ---


def test_attachment_batching_over_10_files_and_modes(tmp_path: Path) -> None:
    _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    for i in range(25):
        _write(tmp_path / "reports" / "Newsletter_2026_11_25" / f"news_{i:02d}.md", SAMPLE_V5_SOURCE)

    bundle = discover_daily_reports(tmp_path, "2026-11-25")

    digest_plans = build_daily_delivery_plan(
        bundle, mode="digest", include_source_files=True, channel_type="forum"
    )
    _assert_all_discord_limits(digest_plans)
    assert digest_plans[0].files == [bundle.distillation.path]
    batch_counts = [len(p.files) for p in digest_plans[1:] if p.files]
    assert batch_counts == [10, 10, 5]

    dist_only_plans = build_daily_delivery_plan(
        bundle, mode="distillation_only", include_source_files=True, channel_type="forum"
    )
    assert len(dist_only_plans) == 1
    assert dist_only_plans[0].files == [bundle.distillation.path]

    no_src_plans = build_daily_delivery_plan(
        bundle, mode="digest", include_source_files=False, channel_type="forum"
    )
    assert sum(len(p.files) for p in no_src_plans) == 1

    full_plans = build_daily_delivery_plan(
        bundle, mode="full", include_source_files=True, channel_type="forum"
    )
    _assert_all_discord_limits(full_plans)
    assert sum(len(p.files) for p in full_plans) == 26


def test_attachment_batching_size_limit(tmp_path: Path) -> None:
    f1 = _write(tmp_path / "f1.md", "A" * (5 * 1024 * 1024))
    f2 = _write(tmp_path / "f2.md", "B" * (5 * 1024 * 1024))
    f3 = _write(tmp_path / "f3.md", "C" * (2 * 1024 * 1024))
    too_big = _write(tmp_path / "huge.md", "D" * (11 * 1024 * 1024))

    batches = batch_attachment_files([f1, f2, f3, too_big])
    assert batches == [[f1], [f2, f3]]


def test_convert_mermaid_to_discord_linear_subgraph_and_sequence() -> None:
    linear = '```mermaid\nflowchart LR\n    A["意圖"] --> B["任務佇列"] --> C["審查閘門"]\n```'
    assert convert_mermaid_to_discord(linear) == "`意圖` ➔ `任務佇列` ➔ `審查閘門`"

    branched = (
        '```mermaid\nflowchart TD\n'
        '    subgraph S1 ["第一層"]\n'
        '        Req["請求<br/>外部"] --> Gate{"分流"}\n'
        '        Gate -- "快速" --> Fast["小模型"]\n'
        '    end\n```'
    )
    conv_b = convert_mermaid_to_discord(branched)
    assert "**第一層**" in conv_b
    assert "- **請求 / 外部** ➔ **分流**" in conv_b
    assert "- **分流** —(*快速*)➔ **小模型**" in conv_b
    assert "<br/>" not in conv_b

    seq = "```mermaid\nsequenceDiagram\n    participant A as Agent\n    A->>Discord: Post\n```"
    assert convert_mermaid_to_discord(seq) == "- **Agent** ➔ **Discord**：Post"


def test_per_report_mode_opens_separate_forum_posts_with_digest_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rich_source = (
        SAMPLE_V5_SOURCE
        + "\n## 📊 一張表看懂\n| 層級 | 痛點 | 解法 | 代價 |\n|---|---|---|---|\n| **亮工廠** | 審查累 | 先審計畫 | 省時間 |\n\n"
        + "<details>\n<summary><b>1. 深入主題</b> — 結論</summary>\n\n- 關鍵證據與數據\n\n</details>\n\n"
        + "<details>\n<summary>📄 <b>展開原始內容</b></summary>\n\nRaw dump should be excluded\n\n</details>\n"
    )
    _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    _write(tmp_path / "reports" / "Newsletter_2026_11_25" / "n1.md", rich_source)
    _write(tmp_path / "reports" / "Website_2026_11_25" / "w1.md", rich_source)

    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    assert len(bundle.sources[0].key_points) == 1
    assert len(bundle.sources[0].overview_subtext_lines) == 4
    assert len(bundle.sources[0].mermaid_flows) == 1
    assert len(bundle.sources[0].deep_dives) == 1
    assert "Raw dump" not in bundle.sources[0].deep_dives[0][1]

    # Option C default: pure native Discord Markdown + dark-mode PNG overview table (zero embeds, zero .md attachments)
    plans = build_daily_delivery_plan(
        bundle, mode="per_report", include_source_files=False, channel_type="forum"
    )
    _assert_all_discord_limits(plans)
    assert all(p.embeds == [] for p in plans)
    assert all(p.files == [] for p in plans)

    thread_openers = [p for p in plans if p.thread_name is not None]
    assert len(thread_openers) == 3  # 2 source reports + 1 distillation
    assert thread_openers[0].thread_name.startswith("📧 [2026-11-25]")
    assert thread_openers[1].thread_name.startswith("🌐 [2026-11-25]")

    # Verify Option C formatting on source opener: headings, gold star emoji + (5/5), angle-bracket link, PNG table + PNG mermaid
    src_opener = thread_openers[0].content or ""
    assert "# Sample Source Article" in src_opener
    assert "⭐⭐⭐⭐⭐ (5/5)" in src_opener
    assert "-# ⭐" not in src_opener
    assert "<https://example.com/article>" in src_opener
    assert "## 📊 一張表看懂" in src_opener
    assert "```mermaid" not in src_opener
    assert "<details" not in src_opener
    assert len(thread_openers[0].inline_files) == 1
    assert thread_openers[0].inline_files[0].filename == "overview_table.png"
    assert thread_openers[0].inline_files[0].content.startswith(b"\x89PNG\r\n\x1a\n")

    # Mermaid PNG gets its own dedicated full-width message right under ### 🔄 系統流程
    mermaid_plans = [p for p in plans if any(f.filename == "diagram_1.png" for f in p.inline_files)]
    assert len(mermaid_plans) == 2
    assert mermaid_plans[0].content == "### 🔄 系統流程"
    assert mermaid_plans[0].inline_files[0].content.startswith(b"\x89PNG\r\n\x1a\n")

    # Daily Digest is posted LAST so it appears at the top of Discord Forum
    dist_plan = thread_openers[-1]
    assert dist_plan.thread_name == "📰 Daily Digest — 2026-11-25"
    assert dist_plan.is_primary_thread is True
    assert "> **🎯 今日一句話結論**" in (dist_plan.content or "")
    assert "## 💡 今日核心重點" in (dist_plan.content or "")
    assert "## 📊 跨來源主題速覽" in (dist_plan.content or "")
    assert len(dist_plan.inline_files) == 1
    assert dist_plan.inline_files[0].content.startswith(b"\x89PNG\r\n\x1a\n")

    # Verify graceful fallback to indented `Column` badges & text Mermaid flow when Pillow is unavailable
    import mcp_servers.discord_reports.formatter as fmt_mod

    monkeypatch.setattr(fmt_mod, "is_pillow_available", lambda: False)
    fallback_plans = build_daily_delivery_plan(
        bundle, mode="per_report", include_source_files=False, channel_type="forum"
    )
    fb_openers = [p for p in fallback_plans if p.thread_name is not None]
    assert all(p.inline_files == [] for p in fallback_plans)
    assert "### 🔄 系統流程\n`Start` ➔ `End`" in (fb_openers[0].content or "")
    assert (
        "- **亮工廠**\n"
        "  - `痛點` 審查累\n"
        "  - `解法` 先審計畫\n"
        "  - `代價` 省時間"
    ) in (fb_openers[0].content or "")
    assert "  - `卡在哪裡` AI改測資且盲跑易走偏" in (fb_openers[-1].content or "")
    monkeypatch.undo()

    # Verify multi-thread HTTP routing via DiscordWebhookPublisher (uploads 3 table PNGs + 2 mermaid PNGs = 5 files)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/111/secret_tok_multi")
    monkeypatch.setenv("DISCORD_CHANNEL_TYPE", "forum")
    monkeypatch.delenv("DISCORD_DEFAULT_MODE", raising=False)

    created_threads = {"n": 0}
    seen_urls: list[str] = []

    def multi_thread_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        seen_urls.append(url)
        if "thread_id=" not in url:
            created_threads["n"] += 1
            return httpx.Response(
                200,
                json={"id": f"op_{created_threads['n']}", "channel_id": f"thread_{created_threads['n']}"},
            )
        return httpx.Response(200, json={"id": "reply_ok", "channel_id": "reply_ch"})

    res = _publish_daily_reports_impl(
        date="2026-11-25",
        repo_root=tmp_path,
        transport=httpx.MockTransport(multi_thread_handler),
        sleep_fn=lambda _: None,
    )
    assert res["status"] == "sent"
    assert res["mode"] == "per_report"
    assert res["posts_created"] == 3
    assert res["thread_ids"] == ["thread_1", "thread_2", "thread_3"]
    assert res["thread_id"] == "thread_3"
    assert res["files_attached"] == 5
    assert any("thread_id=thread_1" in u for u in seen_urls)
    assert any("thread_id=thread_2" in u for u in seen_urls)
    assert any("thread_id=thread_3" in u for u in seen_urls)


# --- AC-6: Forum Threading & Text Fallback ---


def test_forum_thread_chaining_text_fallback_and_400_hint(tmp_path: Path) -> None:
    _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    _write(tmp_path / "reports" / "Website_2026_11_25" / "w1.md", SAMPLE_V5_SOURCE)
    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    plans = build_daily_delivery_plan(bundle, mode="digest", include_source_files=True, channel_type="forum")

    captured_requests: list[tuple[str, str]] = []

    def forum_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append((str(request.url), request.content.decode("utf-8", errors="ignore")))
        return httpx.Response(200, json={"id": f"msg_{len(captured_requests)}", "channel_id": "999888777"})

    pub = DiscordWebhookPublisher(
        "https://discord.com/api/webhooks/111/secret_tok_123",
        channel_type="forum",
        transport=httpx.MockTransport(forum_handler),
        sleep_fn=lambda _: None,
    )
    res = pub.publish_plans(plans)
    assert res["thread_id"] == "999888777"
    assert res["messages_sent"] == len(plans)
    assert res["files_attached"] == 2
    assert "wait=true" in captured_requests[0][0]
    assert "thread_id=" not in captured_requests[0][0]
    assert "thread_name" in captured_requests[0][1]
    assert all("thread_id=999888777" in url for url, _ in captured_requests[1:])

    # Text channel fallback omits thread_name and thread_id
    text_plans = build_daily_delivery_plan(bundle, mode="digest", include_source_files=True, channel_type="text")
    text_urls: list[str] = []

    def text_handler(request: httpx.Request) -> httpx.Response:
        text_urls.append(str(request.url))
        assert b"thread_name" not in request.content
        return httpx.Response(200, json={"id": "msg_t", "channel_id": "555"})

    pub_text = DiscordWebhookPublisher(
        "https://discord.com/api/webhooks/111/secret_tok_123",
        channel_type="text",
        transport=httpx.MockTransport(text_handler),
        sleep_fn=lambda _: None,
    )
    pub_text.publish_plans(text_plans)
    assert all("thread_id=" not in u for u in text_urls)

    # HTTP 400 forum/thread mismatch gives actionable hint
    def bad_400(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": 220001, "message": "Webhooks can only create threads in forum channels"})

    pub_bad = DiscordWebhookPublisher(
        "https://discord.com/api/webhooks/111/secret_tok_123",
        channel_type="forum",
        transport=httpx.MockTransport(bad_400),
        sleep_fn=lambda _: None,
    )
    with pytest.raises(DiscordPublishError) as exc_info:
        pub_bad.publish_plans(plans)
    assert "DISCORD_CHANNEL_TYPE" in str(exc_info.value)
    assert "secret_tok_123" not in str(exc_info.value)


# --- AC-7: 429 Rate Limit Backoff ---


def test_rate_limit_429_retry_and_exhaustion(tmp_path: Path) -> None:
    _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    bundle = discover_daily_reports(tmp_path, "2026-11-25")
    plans = build_daily_delivery_plan(bundle, mode="distillation_only", channel_type="forum")

    sleep_calls: list[float] = []
    attempts = {"count": 0}

    def retry_then_ok(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] <= 2:
            return httpx.Response(429, headers={"Retry-After": "0.5"}, json={"retry_after": 0.5})
        return httpx.Response(200, json={"id": "ok_1", "channel_id": "321"})

    pub = DiscordWebhookPublisher(
        "https://discord.com/api/webhooks/111/secret_tok_123",
        channel_type="forum",
        transport=httpx.MockTransport(retry_then_ok),
        sleep_fn=sleep_calls.append,
    )
    res = pub.publish_plans(plans)
    assert res["thread_id"] == "321"
    assert sleep_calls == [0.5, 0.5]

    # Exhaustion after 3 retries raises clean redacted DiscordPublishError
    def always_429(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"retry_after": 0.25})

    pub_fail = DiscordWebhookPublisher(
        "https://discord.com/api/webhooks/111/secret_tok_123",
        channel_type="forum",
        transport=httpx.MockTransport(always_429),
        sleep_fn=lambda _: None,
        max_retries=3,
    )
    with pytest.raises(DiscordPublishError) as exc_info:
        pub_fail.publish_plans(plans)
    assert "429" in str(exc_info.value)
    assert "secret_tok_123" not in str(exc_info.value)


# --- AC-8 & AC-9: Idempotency Ledger, Dry-Run, and MCP Server Contract ---


def test_idempotency_dry_run_and_missing_webhook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist_path = _write(
        tmp_path / "reports" / "distillations" / "Knowledge_Distillation_2026_11_25.md",
        SAMPLE_V5_DISTILLATION,
    )
    _write(tmp_path / "reports" / "Website_2026_11_25" / "w1.md", SAMPLE_V5_SOURCE)

    # dry_run works even without DISCORD_WEBHOOK_URL and makes zero HTTP calls or ledger writes
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    dry_res = _publish_daily_reports_impl(date="2026-11-25", dry_run=True, repo_root=tmp_path)
    assert dry_res["status"] == "dry_run"
    assert dry_res["messages_planned"] >= 2
    assert not (tmp_path / "data" / "discord_delivery_log.json").exists()

    # Live send without DISCORD_WEBHOOK_URL returns structured error
    err_res = _publish_daily_reports_impl(date="2026-11-25", dry_run=False, repo_root=tmp_path)
    assert err_res["status"] == "error"
    assert "DISCORD_WEBHOOK_URL" in err_res["error"]

    # Configure webhook + mock transport
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/111/secret_tok_xyz")
    monkeypatch.setenv("DISCORD_CHANNEL_TYPE", "forum")

    calls = {"n": 0}

    def ok_handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"id": f"m_{calls['n']}", "channel_id": "thread_abc"})

    transport = httpx.MockTransport(ok_handler)

    sent_1 = _publish_daily_reports_impl(
        date="2026-11-25", repo_root=tmp_path, transport=transport, sleep_fn=lambda _: None
    )
    assert sent_1["status"] == "sent"
    assert sent_1["thread_id"] == "thread_abc"
    first_calls = calls["n"]
    assert first_calls >= 2

    # Second run skips without HTTP calls
    skipped = _publish_daily_reports_impl(
        date="2026-11-25", repo_root=tmp_path, transport=transport, sleep_fn=lambda _: None
    )
    assert skipped["status"] == "skipped"
    assert skipped["reason"] == "already_delivered"
    assert skipped["thread_id"] == "thread_abc"
    assert calls["n"] == first_calls

    # force=True resends
    forced = _publish_daily_reports_impl(
        date="2026-11-25", force=True, repo_root=tmp_path, transport=transport, sleep_fn=lambda _: None
    )
    assert forced["status"] == "sent"
    assert calls["n"] > first_calls

    # Content modification triggers resend automatically
    prev_calls = calls["n"]
    dist_path.write_text(SAMPLE_V5_DISTILLATION + "\nUpdated line\n", encoding="utf-8")
    changed = _publish_daily_reports_impl(
        date="2026-11-25", repo_root=tmp_path, transport=transport, sleep_fn=lambda _: None
    )
    assert changed["status"] == "sent"
    assert calls["n"] > prev_calls

    # Status tool returns receipt without exposing webhook URL
    status = _delivery_status_impl(date="2026-11-25", repo_root=tmp_path)
    assert status["status"] == "ok"
    assert status["delivered"] is True
    assert "secret_tok_xyz" not in json.dumps(status)

    # Verify MCP tool exports
    if hasattr(mcp, "_registered_tools"):
        assert set(TOOL_NAMES).issubset(set(mcp._registered_tools))


# --- AC-10: Token Redaction & Path Containment ---


def test_webhook_token_redaction_and_path_containment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    secret_url = "https://discord.com/api/webhooks/987654321/MySuperSecretToken999"
    scrubbed = redact_webhook_url(f"Failed POST {secret_url}?wait=true", secret_url)
    assert "MySuperSecretToken999" not in scrubbed
    assert "/webhooks/987654321/***" in scrubbed

    _write(tmp_path / "reports" / "Website_2026_11_25" / "ok.md", SAMPLE_V5_SOURCE)
    _write(tmp_path / "data" / "secret.md", "# Secret")

    # Traversal and outside-reports rejections
    for bad in ("../data/secret.md", "data/secret.md", "reports/../../etc/passwd", "/etc/passwd", ""):
        with pytest.raises(ValueError):
            resolve_report_path(bad, tmp_path)

    # Symlink escape rejection
    outside = _write(tmp_path / "outside.md", "# Outside")
    sym = tmp_path / "reports" / "Website_2026_11_25" / "escape.md"
    sym.symlink_to(outside)
    with pytest.raises(ValueError):
        resolve_report_path("reports/Website_2026_11_25/escape.md", tmp_path)

    # Single report tool returns structured error on traversal and scrubs token on HTTP error
    res_bad = _send_report_file_impl("../data/secret.md", repo_root=tmp_path)
    assert res_bad["status"] == "error"
    assert "reports/" in res_bad["error"]

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", secret_url)

    def fail_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"Cannot reach {secret_url}")

    res_net = _send_report_file_impl(
        "reports/Website_2026_11_25/ok.md",
        repo_root=tmp_path,
        transport=httpx.MockTransport(fail_handler),
        sleep_fn=lambda _: None,
    )
    assert res_net["status"] == "error"
    assert "MySuperSecretToken999" not in res_net["error"]


# --- AC-11, AC-12, AC-13: Skills, Workflow Integration, Hygiene & User Guide ---


def test_skills_workflow_gitignore_and_user_guide() -> None:
    deliver_skill = (REPO_ROOT / ".agents" / "skills" / "deliver-discord-reports" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert len(deliver_skill.splitlines()) < 200
    assert "discord_publish_daily_reports" in deliver_skill

    deliver_readme = (REPO_ROOT / ".agents" / "skills" / "deliver-discord-reports" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "ADR-" in deliver_readme
    assert "Changelog" in deliver_readme

    dw_skill = (REPO_ROOT / ".agents" / "skills" / "daily-workflow" / "SKILL.md").read_text(encoding="utf-8")
    assert "Step 6 — Deliver to Discord" in dw_skill
    assert "Fail-Soft" in dw_skill or "fail-soft" in dw_skill
    assert "Step 7 — Review Suggestions" in dw_skill
    assert "Step 8 — Final Summary" in dw_skill

    dispatch_spec = (
        REPO_ROOT / ".agents" / "skills" / "daily-workflow" / "references" / "dispatch_spec.md"
    ).read_text(encoding="utf-8")
    assert "Discord delivery:" in dispatch_spec

    dw_readme = (REPO_ROOT / ".agents" / "skills" / "daily-workflow" / "README.md").read_text(encoding="utf-8")
    assert "ADR-" in dw_readme
    assert "v3.1.0" in dw_readme

    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/discord_delivery_log.json" in gitignore
    assert "mcp_servers/discord_reports/.venv/" in gitignore

    guide = (REPO_ROOT / "docs" / "guides" / "discord-mcp-setup-guide.md").read_text(encoding="utf-8")
    assert "DISCORD_WEBHOOK_URL" in guide
    assert "DISCORD_CHANNEL_TYPE" in guide
    assert "uv sync --directory mcp_servers/discord_reports" in guide
    assert ("/" + "Users/") not in guide

    pyproject = (REPO_ROOT / "mcp_servers" / "discord_reports" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "package = false" in pyproject
    assert "[build-system]" not in pyproject


def test_server_resolves_knowledge_loop_data_repo_env(tmp_path, monkeypatch):
    """MCP server discovers reports from KNOWLEDGE_LOOP_DATA_REPO without explicit repo_root."""
    data_repo = tmp_path / "external-data-repo"
    dist_dir = data_repo / "reports" / "distillations"
    dist_dir.mkdir(parents=True)
    (dist_dir / "Knowledge_Distillation_2026_11_26.md").write_text(
        "# Knowledge Distillation\n\n> 🎯 **今日一句話結論**：Test\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KNOWLEDGE_LOOP_DATA_REPO", str(data_repo))
    res = _publish_daily_reports_impl(date="2026-11-26", dry_run=True)
    assert res["status"] == "dry_run"
    assert res["posts_planned"] >= 1
