"""Deterministic Markdown discovery, v5.0 parsing, sanitization, and Discord payload planning."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .table_renderer import is_pillow_available, render_mermaid_png, render_table_png

MAX_CONTENT_CHARS = 2000
CHUNK_TARGET_CHARS = 1900

MAX_EMBED_TITLE = 256
MAX_EMBED_DESC = 4096
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_FOOTER_TEXT = 2048
MAX_AUTHOR_NAME = 256
MAX_EMBED_FIELDS = 25
MAX_EMBEDS_PER_MSG = 10
MAX_TOTAL_EMBED_CHARS = 6000
SAFE_TOTAL_EMBED_CHARS = 5800

MAX_THREAD_NAME = 100
MAX_FILES_PER_BATCH = 10
MAX_BATCH_BYTES = 8 * 1024 * 1024  # 8 MB safe margin under Discord's 10 MB free-tier cap
MAX_DISCORD_FILE_BYTES = 10 * 1024 * 1024
MAX_INDEX_URL_LEN = 120

VALID_MODES = frozenset({"per_report", "digest", "distillation_only", "full"})
VALID_CHANNEL_TYPES = frozenset({"forum", "text"})

CATEGORY_EMOJI: dict[str, str] = {
    "Newsletter": "📧",
    "Threads": "🧵",
    "Website": "🌐",
    "YouTube": "📺",
}

SOURCE_CATEGORY_DIRS: list[tuple[str, str]] = [
    ("Newsletter", "Newsletter_{date_us}"),
    ("Threads", "Threads_{date_us}"),
    ("Website", "Website_{date_us}"),
    ("YouTube", "YouTube_{date_us}"),
]

_MERMAID_BLOCK_RE = re.compile(r"```mermaid\b[\s\S]*?```", re.IGNORECASE)
_DETAILS_BLOCK_RE = re.compile(
    r"<details\b[^>]*>\s*<summary\b[^>]*>(?P<summary>[\s\S]*?)</summary>(?P<body>[\s\S]*?)</details>",
    re.IGNORECASE,
)
_HTML_TAG_RE = re.compile(r"</?(?:details|summary|b|strong|br)\b[^>]*>", re.IGNORECASE)
_MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
_URL_RE = re.compile(r"https?://[^\s)>]+")
_TABLE_SEP_RE = re.compile(r"^\s*\|(?:\s*:?-{2,}:?\s*\|)+\s*$")


@dataclass(frozen=True)
class InMemoryAttachment:
    """Binary attachment generated in memory (e.g., rendered PNG table image)."""

    filename: str
    content: bytes
    content_type: str = "image/png"


@dataclass(frozen=True)
class SourceReport:
    """Parsed metadata and rendered summary fields for an individual daily report."""

    category: str
    path: Path
    rel_path: str
    title: str
    one_liner: str
    rating: str
    next_step: str
    source_url: str | None
    key_points: list[str] = field(default_factory=list)
    overview_bullets: list[str] = field(default_factory=list)
    overview_subtext_lines: list[str] = field(default_factory=list)
    overview_table: tuple[list[str], list[list[str]]] | None = None
    mermaid_flows: list[str] = field(default_factory=list)
    mermaid_blocks: list[str] = field(default_factory=list)
    deep_dives: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class DistillationReport:
    """Parsed Knowledge Distillation report (v5.0 Answer-First or legacy)."""

    path: Path
    rel_path: str
    title: str
    one_liner: str
    weekly_action: str
    key_points: list[str]
    overview_bullets: list[str]
    pillars: list[tuple[str, str]]
    is_legacy: bool
    overview_subtext_lines: list[str] = field(default_factory=list)
    overview_table: tuple[list[str], list[list[str]]] | None = None
    mermaid_flows: list[str] = field(default_factory=list)
    mermaid_blocks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DailyReportBundle:
    """All discovered reports for a given YYYY-MM-DD date."""

    date: str
    distillation: DistillationReport | None
    sources: list[SourceReport]


@dataclass(frozen=True)
class DiscordMessagePlan:
    """Single validated Discord webhook request payload and attachments."""

    content: str | None
    embeds: list[dict]
    files: list[Path]
    thread_name: str | None = None
    is_primary_thread: bool = False
    inline_files: list[InMemoryAttachment] = field(default_factory=list)


def normalize_date(date: str | None = None) -> str:
    """Validate YYYY-MM-DD date string or return today's local date."""
    if date is None or not str(date).strip():
        return datetime.now().strftime("%Y-%m-%d")
    cleaned = str(date).strip()
    try:
        parsed = datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date '{cleaned}': expected YYYY-MM-DD") from exc
    return parsed.strftime("%Y-%m-%d")


def truncate(text: str, max_len: int) -> str:
    """Truncate text cleanly to max_len characters using a trailing ellipsis."""
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len == 1:
        return "…"
    return text[: max_len - 1].rstrip() + "…"


def _strip_html_inline(text: str) -> str:
    cleaned = _HTML_TAG_RE.sub("", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def _replace_relative_links(text: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        return label

    return _MD_LINK_RE.sub(_repl, text)


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def extract_first_gfm_table(lines: list[str]) -> tuple[list[str], list[list[str]]] | None:
    """Extract the first GFM table (headers, rows) from a list of Markdown lines."""
    i = 0
    while i + 1 < len(lines):
        if "|" in lines[i] and _TABLE_SEP_RE.match(lines[i + 1]):
            headers = _split_table_row(lines[i])
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|") and "|" in lines[i].strip()[1:]:
                cells = _split_table_row(lines[i])
                if cells and any(c for c in cells):
                    rows.append(cells)
                i += 1
            if headers and rows:
                return headers, rows
            return None
        i += 1
    return None


def _convert_gfm_tables(text: str, *, style: str = "inline") -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        if (
            i + 1 < len(lines)
            and "|" in lines[i]
            and _TABLE_SEP_RE.match(lines[i + 1])
        ):
            headers = _split_table_row(lines[i])
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|") and "|" in lines[i].strip()[1:]:
                cells = _split_table_row(lines[i])
                if cells and any(c for c in cells):
                    out.append(_format_table_row(headers, cells, style=style))
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _clean_column_header(raw_header: str) -> str:
    """Clean GFM table column header for inline code badges (strip trailing parenthetical hints)."""
    cleaned = raw_header.strip().replace("`", "").replace("**", "")
    # Strip trailing parenthetical helper text like "（痛點）" or "(details)" when a base label exists
    stripped = re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", cleaned).strip()
    return stripped or cleaned


def _format_table_row(headers: list[str], cells: list[str], *, style: str = "inline") -> str:
    clean_cells = [c.strip() for c in cells]
    col1 = clean_cells[0] if clean_cells else ""
    if col1 and not (col1.startswith("**") and col1.endswith("**")):
        col1_fmt = f"**{col1}**"
    else:
        col1_fmt = col1
    rest = [c for c in clean_cells[1:] if c]

    if style == "subtext":
        # Option 1: Indented sub-bullets with inline `Column` badges preserving table headers
        lines = [f"- {col1_fmt}".strip()]
        for col_idx, val in enumerate(clean_cells[1:], start=1):
            if not val:
                continue
            raw_hdr = headers[col_idx] if col_idx < len(headers) else ""
            hdr = _clean_column_header(raw_hdr)
            if hdr:
                lines.append(f"  - `{hdr}` {val}")
            else:
                lines.append(f"  - {val}")
        return "\n".join(lines)

    if not rest:
        return f"• {col1_fmt}".strip()
    if len(rest) == 1:
        return f"• {col1_fmt} — {rest[0]}"
    if len(rest) == 2:
        return f"• {col1_fmt} — {rest[0]} → {rest[1]}"
    return f"• {col1_fmt} — {' → '.join(rest[:-1])} ({rest[-1]})"


_NODE_DEF_RE = re.compile(
    r'([A-Za-z0-9_]+)\s*(?:\[\s*"([^"]+)"\s*\]|\{\s*"([^"]+)"\s*\}|\(\s*"([^"]+)"\s*\)|\[([^\]]+)\]|\{([^}]+)\})'
)
_EDGE_SPLIT_RE = re.compile(
    r'\s*(?:--\s*"?([^"\n]+?)"?\s*-->|-\.\s*"?([^"\n]+?)"?\s*\.->|-->|-.->|==>)\s*'
)
_SUBGRAPH_RE = re.compile(r'^\s*subgraph\s+\S+(?:\s+\["?([^"\]]+)"?\])?\s*$')
_SEQ_EDGE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*->>?\+?\s*([A-Za-z0-9_]+)\s*:\s*(.+)$')


def _clean_mermaid_label(raw: str) -> str:
    cleaned = re.sub(r"<br\s*/?>", " / ", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip('"')
    return cleaned


def convert_mermaid_to_discord(block_text: str) -> str:
    """Convert a fenced ```mermaid``` block into clean, mobile-safe Discord Markdown."""
    inner = re.sub(r"^```mermaid\b[^\n]*\n?", "", block_text.strip(), flags=re.IGNORECASE)
    inner = re.sub(r"\n?```$", "", inner).strip()
    if not inner:
        return ""

    lines = [ln.rstrip() for ln in inner.splitlines() if ln.strip()]
    if not lines:
        return ""

    header = lines[0].strip().lower()
    if header.startswith("sequencediagram"):
        steps: list[str] = []
        participants: dict[str, str] = {}
        for ln in lines[1:]:
            p_match = re.match(r"^\s*participant\s+(\S+)\s+as\s+(.+)$", ln)
            if p_match:
                participants[p_match.group(1)] = p_match.group(2).strip()
                continue
            s_match = _SEQ_EDGE_RE.match(ln)
            if s_match:
                src = participants.get(s_match.group(1), s_match.group(1))
                dst = participants.get(s_match.group(2), s_match.group(2))
                msg = _clean_mermaid_label(s_match.group(3))
                steps.append(f"- **{src}** ➔ **{dst}**：{msg}")
        return "\n".join(steps)

    # First pass: collect node_id -> human label across the diagram
    node_labels: dict[str, str] = {}
    for ln in lines[1:]:
        if _SUBGRAPH_RE.match(ln) or ln.strip() == "end":
            continue
        for m in _NODE_DEF_RE.finditer(ln):
            nid = m.group(1)
            label = next((g for g in m.groups()[1:] if g is not None), nid)
            node_labels[nid] = _clean_mermaid_label(label)

    def _resolve_node(token: str) -> str:
        t = token.strip()
        m = _NODE_DEF_RE.search(t)
        if m:
            nid = m.group(1)
            label = next((g for g in m.groups()[1:] if g is not None), nid)
            return _clean_mermaid_label(label)
        if "&" in t:
            return " + ".join(node_labels.get(p.strip(), p.strip()) for p in t.split("&"))
        return node_labels.get(t, _clean_mermaid_label(t))

    has_subgraph = any(_SUBGRAPH_RE.match(ln) for ln in lines[1:])
    # Detect single linear chain (no subgraphs, single chained edge line like A --> B --> C)
    edge_lines = [
        ln for ln in lines[1:]
        if any(op in ln for op in ("-->", "-.->", "==>", ".->"))
    ]
    if not has_subgraph and len(edge_lines) == 1:
        parts = _EDGE_SPLIT_RE.split(edge_lines[0])
        # _EDGE_SPLIT_RE has 2 capture groups, so nodes are at indices 0, 3, 6, ...
        raw_nodes = [n for n in parts[0::3] if n and n.strip()]
        labels_inline = [_resolve_node(n) for n in raw_nodes]
        if labels_inline:
            return " ➔ ".join(f"`{lbl}`" for lbl in labels_inline)

    out_lines: list[str] = []
    for ln in lines[1:]:
        stripped = ln.strip()
        if not stripped or stripped == "end" or stripped.startswith("%%"):
            continue
        sg = _SUBGRAPH_RE.match(ln)
        if sg:
            sg_title = _clean_mermaid_label(sg.group(1) or stripped)
            out_lines.append(f"**{sg_title}**")
            continue
        if any(op in ln for op in ("-->", "-.->", "==>", ".->")):
            parts = _EDGE_SPLIT_RE.split(stripped)
            # parts structure: [node0, g1, g2, node1, g1, g2, node2, ...]
            idx = 0
            while idx + 3 < len(parts):
                src = _resolve_node(parts[idx])
                edge_lbl = _clean_mermaid_label(parts[idx + 1] or parts[idx + 2] or "")
                dst = _resolve_node(parts[idx + 3])
                if edge_lbl:
                    out_lines.append(f"- **{src}** —(*{edge_lbl}*)➔ **{dst}**")
                else:
                    out_lines.append(f"- **{src}** ➔ **{dst}**")
                idx += 3

    return "\n".join(out_lines)


def _suppress_link_previews(text: str) -> str:
    """Wrap external Markdown link URLs in <...> so Discord suppresses link preview cards."""
    def _repl(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2).strip()
        if target.startswith(("http://", "https://")) and not (
            target.startswith("<") and target.endswith(">")
        ):
            return f"[{label}](<{target}>)"
        return match.group(0)

    return _MD_LINK_RE.sub(_repl, text)


def sanitize_for_discord(
    text: str,
    *,
    strip_mermaid: bool = False,
    table_style: str = "inline",
    convert_mermaid: bool = False,
    suppress_link_previews: bool = False,
) -> str:
    """Convert GFM tables, <details> tags, relative links, and mermaid blocks for Discord."""
    cleaned = text
    if strip_mermaid:
        cleaned = _MERMAID_BLOCK_RE.sub("", cleaned)
    elif convert_mermaid:
        def _mermaid_repl(match: re.Match[str]) -> str:
            converted = convert_mermaid_to_discord(match.group(0))
            return f"### 🔄 系統流程\n{converted}" if converted else ""

        cleaned = _MERMAID_BLOCK_RE.sub(_mermaid_repl, cleaned)

    def _details_repl(match: re.Match[str]) -> str:
        title = _strip_html_inline(match.group("summary"))
        body = match.group("body").strip()
        heading = f"### {title}" if title else ""
        if heading and body:
            return f"{heading}\n{body}"
        return heading or body

    cleaned = _DETAILS_BLOCK_RE.sub(_details_repl, cleaned)
    cleaned = _HTML_TAG_RE.sub("", cleaned)
    cleaned = _convert_gfm_tables(cleaned, style=table_style)
    cleaned = _replace_relative_links(cleaned)
    if suppress_link_previews:
        cleaned = _suppress_link_previews(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_markdown_attachment(raw_text: str) -> str:
    """Sanitize a .md file in memory for Discord's plain-text attachment preview.

    Removes HTML <details>/<summary>/<b> tags, converts Mermaid blocks and GFM tables,
    and strips broken relative workspace links while leaving local files untouched.
    """
    return sanitize_for_discord(raw_text, convert_mermaid=True, table_style="inline") + "\n"


def _extract_heading_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def _extract_tagged_line(md_text: str, markers: tuple[str, ...]) -> str:
    for line in md_text.splitlines():
        stripped = line.strip()
        for marker in markers:
            if marker in stripped:
                after_marker = stripped.split(marker, 1)[1]
                after_marker = re.sub(r"^[*_\s]*[：:]\s*", "", after_marker)
                after_marker = re.sub(r"^[*_\s]+", "", after_marker)
                return _replace_relative_links(after_marker.strip())
    return ""


def _extract_section_lines(md_text: str, heading_prefixes: tuple[str, ...]) -> list[str]:
    lines = md_text.splitlines()
    capturing = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if capturing:
                break
            heading_body = stripped[3:].strip()
            if any(heading_body.startswith(prefix) for prefix in heading_prefixes):
                capturing = True
            continue
        if capturing:
            if stripped == "---" or stripped.lower().startswith("<details"):
                break
            collected.append(line)
    return collected


def _is_excluded_distillation_accordion(summary_title: str) -> bool:
    lowered = summary_title.lower()
    return (
        "今日合成來源清單" in summary_title
        or "sources" in lowered
        or "對我的意義與來源資訊" in summary_title
        or "展開原始內容" in summary_title
    )


def _is_excluded_source_accordion(summary_title: str) -> bool:
    lowered = summary_title.lower()
    return (
        "展開原始內容" in summary_title
        or "raw content" in lowered
        or "今日合成來源清單" in summary_title
    )


def parse_distillation(path: Path, repo_root: Path) -> DistillationReport:
    """Parse a v5.0 or legacy Knowledge Distillation Markdown file."""
    raw = path.read_text(encoding="utf-8")
    rel_path = path.relative_to(repo_root).as_posix()
    title = _extract_heading_title(raw, path.stem)
    if title.lower().startswith("knowledge distillation:"):
        title = title.split(":", 1)[1].strip()

    one_liner = _extract_tagged_line(raw, ("🎯 今日一句話結論", "🎯 一句話結論"))
    weekly_action = _extract_tagged_line(raw, ("⚡ 本週唯一行動", "⚡ 下一步"))

    key_point_lines = _extract_section_lines(raw, ("💡 今日核心重點", "💡 核心重點"))
    key_points: list[str] = []
    for line in key_point_lines:
        stripped = line.strip()
        if re.match(r"^(?:\d+\.|[-*])\s+", stripped):
            key_points.append(_replace_relative_links(stripped))

    overview_lines = _extract_section_lines(raw, ("📊 跨來源主題速覽", "📊 一張表看懂"))
    overview_table = extract_first_gfm_table(overview_lines)
    overview_sanitized = sanitize_for_discord("\n".join(overview_lines), strip_mermaid=True)
    overview_bullets = [
        line.strip() for line in overview_sanitized.splitlines() if line.strip().startswith("•")
    ]
    overview_subtext_sanitized = sanitize_for_discord(
        "\n".join(overview_lines), strip_mermaid=True, table_style="subtext"
    )
    overview_subtext_lines = [
        line.rstrip()
        for line in overview_subtext_sanitized.splitlines()
        if line.lstrip().startswith(("- ", "-# "))
    ]
    mermaid_blocks = [m.group(0) for m in _MERMAID_BLOCK_RE.finditer(raw)]
    mermaid_flows = [
        flow for blk in mermaid_blocks if (flow := convert_mermaid_to_discord(blk))
    ]

    pillars: list[tuple[str, str]] = []
    for match in _DETAILS_BLOCK_RE.finditer(raw):
        summary_title = _strip_html_inline(match.group("summary"))
        if _is_excluded_distillation_accordion(summary_title):
            continue
        body = sanitize_for_discord(
            match.group("body"), convert_mermaid=True, table_style="subtext", suppress_link_previews=True
        )
        if summary_title or body:
            pillars.append((summary_title, body))

    is_legacy = not one_liner and not key_points and not pillars
    if is_legacy:
        exec_lines = _extract_section_lines(raw, ("📝 Executive Summary", "Executive Summary"))
        exec_text = sanitize_for_discord("\n".join(exec_lines), strip_mermaid=True)
        if exec_text:
            first_para = exec_text.split("\n\n", 1)[0].strip()
            one_liner = truncate(first_para.replace("\n", " "), 300)

        sections = re.split(r"^##\s+", raw, flags=re.MULTILINE)
        for sec in sections[1:]:
            sec_lines = sec.splitlines()
            sec_title = sec_lines[0].strip()
            if (
                sec_title.startswith("📝")
                or sec_title.lower().startswith("executive summary")
                or sec_title.startswith("🚀")
            ):
                if sec_title.startswith("🚀") and not weekly_action:
                    weekly_action = truncate(
                        sanitize_for_discord("\n".join(sec_lines[1:]), strip_mermaid=True),
                        300,
                    )
                continue
            sec_body = sanitize_for_discord(
                "\n".join(sec_lines[1:]), convert_mermaid=True, table_style="subtext", suppress_link_previews=True
            )
            if sec_body:
                pillars.append((sec_title, sec_body))

    return DistillationReport(
        path=path,
        rel_path=rel_path,
        title=title,
        one_liner=one_liner,
        weekly_action=weekly_action,
        key_points=key_points,
        overview_bullets=overview_bullets,
        pillars=pillars,
        is_legacy=is_legacy,
        overview_subtext_lines=overview_subtext_lines,
        overview_table=overview_table,
        mermaid_flows=mermaid_flows,
        mermaid_blocks=mermaid_blocks,
    )


def parse_source_report(path: Path, category: str, repo_root: Path) -> SourceReport:
    """Parse a v5.0 or legacy individual source report including key points, table, and deep dives."""
    raw = path.read_text(encoding="utf-8")
    rel_path = path.relative_to(repo_root).as_posix()
    title = _extract_heading_title(raw, path.stem)
    one_liner = _extract_tagged_line(raw, ("🎯 一句話結論", "🎯 今日一句話結論"))
    if not one_liner:
        for line in raw.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("---") and not s.startswith("<"):
                one_liner = truncate(_replace_relative_links(s.lstrip("> -*")), 220)
                break

    rating_raw = _extract_tagged_line(raw, ("⭐ 推薦度",))
    rating_match = re.search(r"[★☆]+", rating_raw)
    rating = rating_match.group(0) if rating_match else truncate(rating_raw, 24)

    next_step = _extract_tagged_line(raw, ("⚡ 下一步", "⚡ 本週唯一行動"))

    source_url: str | None = None
    source_line = _extract_tagged_line(raw, ("🔗 來源", "來源連結", "URL"))
    if source_line:
        url_match = _URL_RE.search(source_line)
        if url_match:
            source_url = url_match.group(0)
    if not source_url:
        top_chunk = "\n".join(raw.splitlines()[:25])
        url_match = _URL_RE.search(top_chunk)
        if url_match:
            source_url = url_match.group(0)

    key_point_lines = _extract_section_lines(raw, ("💡 核心重點", "💡 今日核心重點"))
    key_points: list[str] = []
    for line in key_point_lines:
        stripped = line.strip()
        if re.match(r"^(?:\d+\.|[-*])\s+", stripped):
            key_points.append(_replace_relative_links(stripped))

    overview_lines = _extract_section_lines(raw, ("📊 一張表看懂", "📊 跨來源主題速覽"))
    overview_table = extract_first_gfm_table(overview_lines)
    overview_sanitized = sanitize_for_discord("\n".join(overview_lines), strip_mermaid=True)
    overview_bullets = [
        line.strip() for line in overview_sanitized.splitlines() if line.strip().startswith("•")
    ]
    overview_subtext_sanitized = sanitize_for_discord(
        "\n".join(overview_lines), strip_mermaid=True, table_style="subtext"
    )
    overview_subtext_lines = [
        line.rstrip()
        for line in overview_subtext_sanitized.splitlines()
        if line.lstrip().startswith(("- ", "-# "))
    ]
    mermaid_blocks = [m.group(0) for m in _MERMAID_BLOCK_RE.finditer(raw)]
    mermaid_flows = [
        flow for blk in mermaid_blocks if (flow := convert_mermaid_to_discord(blk))
    ]

    deep_dives: list[tuple[str, str]] = []
    for match in _DETAILS_BLOCK_RE.finditer(raw):
        summary_title = _strip_html_inline(match.group("summary"))
        if _is_excluded_source_accordion(summary_title):
            continue
        body = sanitize_for_discord(
            match.group("body"), convert_mermaid=True, table_style="subtext", suppress_link_previews=True
        )
        if summary_title or body:
            deep_dives.append((summary_title, body))

    # Fallback for legacy source reports without <details> blocks
    if not deep_dives:
        sections = re.split(r"^##\s+", raw, flags=re.MULTILINE)
        for sec in sections[1:]:
            sec_lines = sec.splitlines()
            sec_title = sec_lines[0].strip()
            if (
                sec_title.startswith(("💡", "📊", "🔍"))
                or "原始內容" in sec_title
                or "raw content" in sec_title.lower()
            ):
                continue
            sec_body = sanitize_for_discord(
                "\n".join(sec_lines[1:]), convert_mermaid=True, table_style="subtext", suppress_link_previews=True
            )
            if sec_body:
                deep_dives.append((sec_title, sec_body))

    return SourceReport(
        category=category,
        path=path,
        rel_path=rel_path,
        title=title,
        one_liner=one_liner,
        rating=rating,
        next_step=next_step,
        source_url=source_url,
        key_points=key_points,
        overview_bullets=overview_bullets,
        overview_subtext_lines=overview_subtext_lines,
        overview_table=overview_table,
        mermaid_flows=mermaid_flows,
        mermaid_blocks=mermaid_blocks,
        deep_dives=deep_dives,
    )


def discover_daily_reports(repo_root: Path, date: str) -> DailyReportBundle:
    """Discover distillation and all date-stamped source reports deterministically."""
    norm_date = normalize_date(date)
    date_us = norm_date.replace("-", "_")
    reports_root = repo_root / "reports"

    distillation_path = reports_root / "distillations" / f"Knowledge_Distillation_{date_us}.md"
    distillation = (
        parse_distillation(distillation_path, repo_root)
        if distillation_path.is_file()
        else None
    )

    sources: list[SourceReport] = []
    for category, dir_template in SOURCE_CATEGORY_DIRS:
        cat_dir = reports_root / dir_template.format(date_us=date_us)
        if not cat_dir.is_dir():
            continue
        for md_path in sorted(cat_dir.glob("*.md"), key=lambda p: p.name):
            if md_path.is_file():
                sources.append(parse_source_report(md_path, category, repo_root))

    return DailyReportBundle(date=norm_date, distillation=distillation, sources=sources)


def chunk_text(text: str, limit: int = CHUNK_TARGET_CHARS) -> list[str]:
    """Split text into chunks of at most `limit` characters (<= 2000 hard cap)."""
    effective_limit = min(limit, MAX_CONTENT_CHARS)
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= effective_limit:
        return [cleaned]

    chunks: list[str] = []
    current = ""

    def _flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for paragraph in cleaned.split("\n\n"):
        para = paragraph.strip()
        if not para:
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= effective_limit:
            current = candidate
            continue

        _flush()
        if len(para) <= effective_limit:
            current = para
            continue

        for line in para.splitlines():
            if not line.strip():
                continue
            line_s = line.rstrip()
            cand_line = f"{current}\n{line_s}" if current else line_s
            if len(cand_line) <= effective_limit:
                current = cand_line
                continue
            _flush()
            if len(line_s) <= effective_limit:
                current = line_s
                continue
            words = line_s.split(" ")
            for word in words:
                cand_word = f"{current} {word}" if current else word
                if len(cand_word) <= effective_limit:
                    current = cand_word
                    continue
                _flush()
                if len(word) <= effective_limit:
                    current = word
                else:
                    for idx in range(0, len(word), effective_limit):
                        part = word[idx : idx + effective_limit]
                        if len(part) == effective_limit:
                            chunks.append(part)
                        else:
                            current = part

    _flush()
    return chunks


def embed_char_count(embed: dict) -> int:
    """Calculate total character count of an embed per Discord API rules."""
    total = len(embed.get("title", "") or "")
    total += len(embed.get("description", "") or "")
    footer = embed.get("footer") or {}
    total += len(footer.get("text", "") or "")
    author = embed.get("author") or {}
    total += len(author.get("name", "") or "")
    for field_item in embed.get("fields", []) or []:
        total += len(field_item.get("name", "") or "")
        total += len(field_item.get("value", "") or "")
    return total


def validate_message_plan(plan: DiscordMessagePlan) -> None:
    """Assert every Discord API size, count, and length constraint on a message plan."""
    if plan.content is not None and len(plan.content) > MAX_CONTENT_CHARS:
        raise ValueError(f"Message content exceeds {MAX_CONTENT_CHARS} chars: {len(plan.content)}")
    if plan.thread_name is not None and len(plan.thread_name) > MAX_THREAD_NAME:
        raise ValueError(f"thread_name exceeds {MAX_THREAD_NAME} chars: {len(plan.thread_name)}")
    if len(plan.embeds) > MAX_EMBEDS_PER_MSG:
        raise ValueError(f"Message exceeds {MAX_EMBEDS_PER_MSG} embeds: {len(plan.embeds)}")

    total_embed_chars = 0
    for embed in plan.embeds:
        title = embed.get("title", "") or ""
        desc = embed.get("description", "") or ""
        footer_text = (embed.get("footer") or {}).get("text", "") or ""
        author_name = (embed.get("author") or {}).get("name", "") or ""
        fields = embed.get("fields", []) or []

        if len(title) > MAX_EMBED_TITLE:
            raise ValueError(f"Embed title exceeds {MAX_EMBED_TITLE} chars: {len(title)}")
        if len(desc) > MAX_EMBED_DESC:
            raise ValueError(f"Embed description exceeds {MAX_EMBED_DESC} chars: {len(desc)}")
        if len(footer_text) > MAX_FOOTER_TEXT:
            raise ValueError(f"Embed footer exceeds {MAX_FOOTER_TEXT} chars: {len(footer_text)}")
        if len(author_name) > MAX_AUTHOR_NAME:
            raise ValueError(f"Embed author exceeds {MAX_AUTHOR_NAME} chars: {len(author_name)}")
        if len(fields) > MAX_EMBED_FIELDS:
            raise ValueError(f"Embed fields exceed {MAX_EMBED_FIELDS}: {len(fields)}")
        for field_item in fields:
            fname = field_item.get("name", "") or ""
            fval = field_item.get("value", "") or ""
            if len(fname) > MAX_FIELD_NAME:
                raise ValueError(f"Embed field name exceeds {MAX_FIELD_NAME}: {len(fname)}")
            if len(fval) > MAX_FIELD_VALUE:
                raise ValueError(f"Embed field value exceeds {MAX_FIELD_VALUE}: {len(fval)}")
        total_embed_chars += embed_char_count(embed)

    if total_embed_chars > MAX_TOTAL_EMBED_CHARS:
        raise ValueError(
            f"Combined embed characters exceed {MAX_TOTAL_EMBED_CHARS}: {total_embed_chars}"
        )

    total_files = len(plan.files) + len(plan.inline_files)
    if total_files > MAX_FILES_PER_BATCH:
        raise ValueError(f"Attachments exceed {MAX_FILES_PER_BATCH} files: {total_files}")
    total_bytes = sum(f.stat().st_size for f in plan.files if f.exists()) + sum(
        len(f.content) for f in plan.inline_files
    )
    if total_bytes > MAX_DISCORD_FILE_BYTES:
        raise ValueError(f"Attachment batch exceeds 10 MB: {total_bytes} bytes")


def batch_attachment_files(
    files: list[Path],
    *,
    max_files: int = MAX_FILES_PER_BATCH,
    max_bytes: int = MAX_BATCH_BYTES,
) -> list[list[Path]]:
    """Group files into batches obeying file-count and total-byte caps."""
    batches: list[list[Path]] = []
    current: list[Path] = []
    current_bytes = 0

    for path in files:
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_DISCORD_FILE_BYTES:
            continue
        would_exceed_count = len(current) >= max_files
        would_exceed_bytes = bool(current) and (current_bytes + size > max_bytes)
        if would_exceed_count or would_exceed_bytes:
            batches.append(current)
            current = []
            current_bytes = 0
        current.append(path)
        current_bytes += size

    if current:
        batches.append(current)
    return batches


def _format_discord_rating(rating: str) -> str:
    """Format star ratings using bright gold ⭐ emoji + explicit (N/5) score for Discord dark/light mode."""
    if not rating:
        return ""
    filled = rating.count("★") + rating.count("⭐")
    empty = rating.count("☆")
    if filled > 0 or empty > 0:
        total = max(filled + empty, 5) if empty > 0 else max(filled, 5)
        if filled == 0:
            return f"0/{total}"
        return f"{'⭐' * filled} ({filled}/{total})"
    return f"⭐ {rating}"


def _format_index_line(src: SourceReport) -> str:
    stars = f" {_format_discord_rating(src.rating)}" if src.rating else ""
    short_title = truncate(src.title, 70)
    if src.source_url and len(src.source_url) <= MAX_INDEX_URL_LEN:
        label = f"[{short_title}]({src.source_url})"
    else:
        label = f"**{short_title}**"
    line = f"• **[{src.category}]** {label}{stars}"
    if src.one_liner:
        remaining = 180 - len(line)
        if remaining > 30:
            line += f" — {truncate(src.one_liner, remaining)}"
    return truncate(line, MAX_FIELD_VALUE - 4)


def _pack_lines_into_fields(
    lines: list[str],
    base_name: str,
    *,
    max_total_chars: int,
) -> tuple[list[dict], list[str]]:
    """Pack lines into Embed fields <= 1024 chars without exceeding max_total_chars."""
    fields: list[dict] = []
    overflow_idx = len(lines)
    used_chars = 0
    current_lines: list[str] = []

    for idx, line in enumerate(lines):
        candidate = "\n".join(current_lines + [line])
        field_name = base_name if not fields else f"{base_name} (cont.)"
        if len(candidate) <= MAX_FIELD_VALUE:
            projected = used_chars + len(field_name) + len(candidate)
            if projected <= max_total_chars and len(fields) < MAX_EMBED_FIELDS:
                current_lines.append(line)
                continue
        if current_lines:
            fname = base_name if not fields else f"{base_name} (cont.)"
            fval = "\n".join(current_lines)
            if used_chars + len(fname) + len(fval) <= max_total_chars and len(fields) < MAX_EMBED_FIELDS:
                fields.append({"name": fname, "value": fval, "inline": False})
                used_chars += len(fname) + len(fval)
                current_lines = []
                fname_next = f"{base_name} (cont.)"
                if (
                    len(line) <= MAX_FIELD_VALUE
                    and used_chars + len(fname_next) + len(line) <= max_total_chars
                    and len(fields) < MAX_EMBED_FIELDS
                ):
                    current_lines = [line]
                    continue
        overflow_idx = idx
        break

    if current_lines:
        fname = base_name if not fields else f"{base_name} (cont.)"
        fval = "\n".join(current_lines)
        if used_chars + len(fname) + len(fval) <= max_total_chars and len(fields) < MAX_EMBED_FIELDS:
            fields.append({"name": fname, "value": fval, "inline": False})
        else:
            overflow_idx = min(overflow_idx, len(lines) - len(current_lines))

    return fields, lines[overflow_idx:]


def _build_distillation_embed(
    distillation: DistillationReport | None,
    bundle: DailyReportBundle,
    *,
    compact: bool = False,
) -> dict:
    if distillation is None:
        return {
            "title": truncate(f"📰 Daily Reports Index ({bundle.date})", MAX_EMBED_TITLE),
            "description": (
                f"No `Knowledge_Distillation_{bundle.date.replace('-', '_')}.md` file found; "
                f"delivering **{len(bundle.sources)}** processed source report(s)."
            ),
            "color": 0x3B82F6,
            "footer": {
                "text": truncate(
                    f"Daily AI Workflow • {bundle.date} • {len(bundle.sources)} source report(s)",
                    MAX_FOOTER_TEXT,
                )
            },
        }

    parts: list[str] = []
    if distillation.one_liner:
        parts.append(f"🎯 **今日一句話結論**\n{distillation.one_liner}")
    if distillation.weekly_action:
        parts.append(f"⚡ **本週唯一行動**\n{distillation.weekly_action}")
    if not compact:
        if distillation.key_points:
            kp_block = "\n".join(distillation.key_points[:5])
            parts.append(f"💡 **今日核心重點**\n{kp_block}")
        if distillation.overview_bullets:
            ov_block = "\n".join(distillation.overview_bullets[:5])
            parts.append(f"📊 **跨來源主題速覽**\n{ov_block}")

    raw_desc = "\n\n".join(parts) if parts else "Daily Knowledge Distillation ready."
    desc = truncate(sanitize_for_discord(raw_desc, strip_mermaid=True), MAX_EMBED_DESC)
    if len(desc) > 3400:
        desc = truncate(desc, 3400)

    return {
        "title": truncate(f"🧠 {distillation.title}", MAX_EMBED_TITLE),
        "description": desc,
        "color": 0x5865F2,
        "footer": {
            "text": truncate(
                f"Daily AI Workflow • {bundle.date} • {len(bundle.sources)} source report(s)",
                MAX_FOOTER_TEXT,
            )
        },
    }


def _build_source_embed(src: SourceReport, *, include_body_preview: bool = False) -> dict:
    desc_parts: list[str] = []
    if src.one_liner:
        desc_parts.append(f"🎯 **一句話結論**\n{src.one_liner}")
    meta_lines: list[str] = []
    if src.rating:
        meta_lines.append(f"⭐ **推薦度**：{_format_discord_rating(src.rating)}")
    if src.next_step:
        meta_lines.append(f"⚡ **下一步**：{src.next_step}")
    if src.source_url:
        if len(src.source_url) <= 500:
            meta_lines.append(f"🔗 [原文連結]({src.source_url})")
        else:
            meta_lines.append(f"🔗 **來源**：{src.category}")
    if meta_lines:
        desc_parts.append("\n".join(meta_lines))

    if include_body_preview:
        if src.key_points:
            desc_parts.append("💡 **核心重點**\n" + "\n".join(src.key_points[:5]))
        if src.overview_bullets:
            desc_parts.append("📊 **一張表看懂**\n" + "\n".join(src.overview_bullets[:6]))

    raw_desc = "\n\n".join(desc_parts) if desc_parts else src.title
    desc = truncate(sanitize_for_discord(raw_desc, strip_mermaid=True), MAX_EMBED_DESC)
    if len(desc) > 3800:
        desc = truncate(desc, 3800)

    emoji = CATEGORY_EMOJI.get(src.category, "📄")
    return {
        "title": truncate(f"{emoji} [{src.category}] {src.title}", MAX_EMBED_TITLE),
        "description": desc,
        "color": 0x10B981,
        "footer": {"text": truncate(src.rel_path, MAX_FOOTER_TEXT)},
    }


def _build_source_post_plans(
    src: SourceReport,
    *,
    date: str,
    attach_markdown: bool,
    channel_type: str,
    existing_thread_id: str | None = None,
    compact: bool = True,
) -> list[DiscordMessagePlan]:
    """Build opener Embed (+ .md attachment) and optional deep-dive reply plans for one source report."""
    plans: list[DiscordMessagePlan] = []
    embed = _build_source_embed(src, include_body_preview=not compact)
    emoji = CATEGORY_EMOJI.get(src.category, "📄")
    tname = (
        truncate(f"{emoji} [{date}] {src.title}", MAX_THREAD_NAME)
        if channel_type == "forum" and not existing_thread_id
        else None
    )
    plans.append(
        DiscordMessagePlan(
            content=None,
            embeds=[embed],
            files=[src.path] if attach_markdown else [],
            thread_name=tname,
            is_primary_thread=False,
        )
    )

    if not compact and src.deep_dives:
        sections = []
        for heading_title, body in src.deep_dives:
            heading = f"### {heading_title}" if heading_title else ""
            sections.append(f"{heading}\n{body}".strip() if heading else body)
        deep_text = "## 🔍 深入解構\n\n" + "\n\n".join(sections)
        for chunk in chunk_text(deep_text, limit=CHUNK_TARGET_CHARS):
            plans.append(DiscordMessagePlan(content=chunk, embeds=[], files=[]))

    return plans


def _build_distillation_post_plans(
    bundle: DailyReportBundle,
    *,
    channel_type: str,
    include_index: bool,
    include_pillars: bool,
    compact: bool = False,
) -> list[DiscordMessagePlan]:
    """Build opener Embed (+ distillation .md) and optional deep-dive replies for the daily distillation."""
    plans: list[DiscordMessagePlan] = []
    opener_embed = _build_distillation_embed(bundle.distillation, bundle, compact=compact)
    overflow_index_lines: list[str] = []

    if include_index and bundle.sources:
        index_lines = [_format_index_line(src) for src in bundle.sources]
        used_base = embed_char_count(opener_embed)
        budget = max(0, SAFE_TOTAL_EMBED_CHARS - used_base)
        fields, overflow_index_lines = _pack_lines_into_fields(
            index_lines,
            f"📚 Processed Reports ({len(bundle.sources)})",
            max_total_chars=budget,
        )
        if fields:
            opener_embed["fields"] = fields

    thread_name = (
        truncate(f"📰 Daily Digest — {bundle.date}", MAX_THREAD_NAME)
        if channel_type == "forum"
        else None
    )
    opener_files = [bundle.distillation.path] if bundle.distillation else []
    plans.append(
        DiscordMessagePlan(
            content=None,
            embeds=[opener_embed],
            files=opener_files,
            thread_name=thread_name,
            is_primary_thread=True,
        )
    )

    if overflow_index_lines:
        overflow_text = "**📚 Processed Reports (Continued)**\n" + "\n".join(overflow_index_lines)
        for chunk in chunk_text(overflow_text, limit=CHUNK_TARGET_CHARS):
            plans.append(DiscordMessagePlan(content=chunk, embeds=[], files=[]))

    if include_pillars and bundle.distillation and bundle.distillation.pillars:
        pillar_sections = []
        for title, body in bundle.distillation.pillars:
            heading = f"### {title}" if title else ""
            pillar_sections.append(f"{heading}\n{body}".strip() if heading else body)
        deep_dive_text = "## 🔍 主題深入解構\n\n" + "\n\n".join(pillar_sections)
        for chunk in chunk_text(deep_dive_text, limit=CHUNK_TARGET_CHARS):
            plans.append(DiscordMessagePlan(content=chunk, embeds=[], files=[]))

    return plans


def _render_overview_table_attachment(
    table: tuple[list[str], list[list[str]]] | None,
    *,
    title: str | None = None,
) -> InMemoryAttachment | None:
    if table is None or not is_pillow_available():
        return None
    headers, rows = table
    try:
        png_bytes = render_table_png(headers, rows, title=title)
    except Exception:
        return None
    return InMemoryAttachment(
        filename="overview_table.png",
        content=png_bytes,
        content_type="image/png",
    )


def _render_mermaid_attachments(mermaid_blocks: list[str]) -> list[InMemoryAttachment]:
    if not mermaid_blocks or not is_pillow_available():
        return []
    out: list[InMemoryAttachment] = []
    for idx, blk in enumerate(mermaid_blocks, start=1):
        try:
            png_bytes = render_mermaid_png(blk)
        except Exception:
            continue
        out.append(
            InMemoryAttachment(
                filename=f"diagram_{idx}.png",
                content=png_bytes,
                content_type="image/png",
            )
        )
    return out


def _build_markdown_source_post_plans(
    src: SourceReport,
    *,
    date: str,
    attach_markdown: bool,
    channel_type: str,
    existing_thread_id: str | None = None,
) -> list[DiscordMessagePlan]:
    """Option C: Pure native Discord Markdown + full-width dark-mode PNGs for Table and Mermaid."""
    opener_parts: list[str] = [f"# {src.title}"]
    if src.one_liner:
        opener_parts.append(f"> **🎯 一句話結論**：{src.one_liner}")

    meta_bits: list[str] = []
    if src.rating:
        meta_bits.append(_format_discord_rating(src.rating))
    if src.source_url and len(src.source_url) <= 500:
        meta_bits.append(f"🔗 [{src.category} 原文](<{src.source_url}>)")
    else:
        meta_bits.append(f"📁 {src.category}")
    opener_parts.append(" · ".join(meta_bits))

    if src.next_step:
        opener_parts.append(f"- **⚡ 下一步**：{src.next_step}")

    if src.key_points:
        opener_parts.append("\n## 💡 核心重點\n" + "\n".join(src.key_points))

    table_img = _render_overview_table_attachment(src.overview_table)
    mermaid_imgs = _render_mermaid_attachments(src.mermaid_blocks)

    if not mermaid_imgs:
        for flow in src.mermaid_flows:
            opener_parts.append(f"\n### 🔄 系統流程\n{flow}")

    if table_img is not None:
        opener_parts.append("\n## 📊 一張表看懂")
    elif src.overview_subtext_lines:
        opener_parts.append("\n## 📊 一張表看懂\n" + "\n".join(src.overview_subtext_lines))

    opener_text = _suppress_link_previews("\n".join(opener_parts).strip())
    opener_chunks = chunk_text(opener_text, limit=CHUNK_TARGET_CHARS)
    if not opener_chunks:
        opener_chunks = [f"# {src.title}"]

    emoji = CATEGORY_EMOJI.get(src.category, "📄")
    tname = (
        truncate(f"{emoji} [{date}] {src.title}", MAX_THREAD_NAME)
        if channel_type == "forum" and not existing_thread_id
        else None
    )

    last_idx = len(opener_chunks) - 1
    plans: list[DiscordMessagePlan] = []
    for idx, chunk in enumerate(opener_chunks):
        plans.append(
            DiscordMessagePlan(
                content=chunk,
                embeds=[],
                files=[src.path] if (idx == 0 and attach_markdown) else [],
                thread_name=tname if idx == 0 else None,
                is_primary_thread=False,
                inline_files=[table_img] if (idx == last_idx and table_img is not None) else [],
            )
        )

    # Give each Mermaid PNG its own dedicated full-width message so Discord doesn't shrink it into a 2-up grid
    for idx, m_img in enumerate(mermaid_imgs, start=1):
        heading = "### 🔄 系統流程" if len(mermaid_imgs) == 1 else f"### 🔄 系統流程 ({idx}/{len(mermaid_imgs)})"
        plans.append(
            DiscordMessagePlan(
                content=heading,
                embeds=[],
                files=[],
                inline_files=[m_img],
            )
        )

    if src.deep_dives:
        sections = []
        for heading_title, body in src.deep_dives:
            heading = f"### {heading_title}" if heading_title else ""
            sections.append(f"{heading}\n{body}".strip() if heading else body)
        deep_text = "## 🔍 深入解構\n\n" + "\n\n".join(sections)
        for chunk in chunk_text(deep_text, limit=CHUNK_TARGET_CHARS):
            plans.append(DiscordMessagePlan(content=chunk, embeds=[], files=[]))

    return plans


def _build_markdown_distillation_post_plans(
    bundle: DailyReportBundle,
    *,
    attach_markdown: bool,
    channel_type: str,
    existing_thread_id: str | None = None,
) -> list[DiscordMessagePlan]:
    """Option C: Pure native Discord Markdown + full-width dark-mode PNGs for Daily Distillation."""
    dist = bundle.distillation
    assert dist is not None

    opener_parts: list[str] = [f"# {dist.title}"]
    if dist.one_liner:
        opener_parts.append(f"> **🎯 今日一句話結論**：{dist.one_liner}")
    opener_parts.append(f"-# 📅 {bundle.date} · 📚 {len(bundle.sources)} 篇來源報告")
    if dist.weekly_action:
        opener_parts.append(f"- **⚡ 本週唯一行動**：{dist.weekly_action}")

    if dist.key_points:
        opener_parts.append("\n## 💡 今日核心重點\n" + "\n".join(dist.key_points))

    table_img = _render_overview_table_attachment(dist.overview_table)
    mermaid_imgs = _render_mermaid_attachments(dist.mermaid_blocks)

    if not mermaid_imgs:
        for flow in dist.mermaid_flows:
            opener_parts.append(f"\n### 🔄 系統流程\n{flow}")

    if table_img is not None:
        opener_parts.append("\n## 📊 跨來源主題速覽")
    elif dist.overview_subtext_lines:
        opener_parts.append("\n## 📊 跨來源主題速覽\n" + "\n".join(dist.overview_subtext_lines))

    opener_text = _suppress_link_previews("\n".join(opener_parts).strip())
    opener_chunks = chunk_text(opener_text, limit=CHUNK_TARGET_CHARS)
    if not opener_chunks:
        opener_chunks = [f"# {dist.title}"]

    tname = (
        truncate(f"📰 Daily Digest — {bundle.date}", MAX_THREAD_NAME)
        if channel_type == "forum" and not existing_thread_id
        else None
    )

    last_idx = len(opener_chunks) - 1
    plans: list[DiscordMessagePlan] = []
    for idx, chunk in enumerate(opener_chunks):
        plans.append(
            DiscordMessagePlan(
                content=chunk,
                embeds=[],
                files=[dist.path] if (idx == 0 and attach_markdown) else [],
                thread_name=tname if idx == 0 else None,
                is_primary_thread=(idx == 0),
                inline_files=[table_img] if (idx == last_idx and table_img is not None) else [],
            )
        )

    for idx, m_img in enumerate(mermaid_imgs, start=1):
        heading = "### 🔄 系統流程" if len(mermaid_imgs) == 1 else f"### 🔄 系統流程 ({idx}/{len(mermaid_imgs)})"
        plans.append(
            DiscordMessagePlan(
                content=heading,
                embeds=[],
                files=[],
                inline_files=[m_img],
            )
        )

    if dist.pillars:
        sections = []
        for heading_title, body in dist.pillars:
            heading = f"### {heading_title}" if heading_title else ""
            sections.append(f"{heading}\n{body}".strip() if heading else body)
        deep_text = "## 🔍 主題深入解構\n\n" + "\n\n".join(sections)
        for chunk in chunk_text(deep_text, limit=CHUNK_TARGET_CHARS):
            plans.append(DiscordMessagePlan(content=chunk, embeds=[], files=[]))

    return plans


def build_daily_delivery_plan(
    bundle: DailyReportBundle,
    *,
    mode: str = "per_report",
    include_source_files: bool = False,
    channel_type: str = "forum",
) -> list[DiscordMessagePlan]:
    """Build ordered, validated Discord message plans for a DailyReportBundle."""
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode '{mode}': expected one of {sorted(VALID_MODES)}")
    if channel_type not in VALID_CHANNEL_TYPES:
        raise ValueError(
            f"Unsupported channel_type '{channel_type}': expected one of {sorted(VALID_CHANNEL_TYPES)}"
        )
    if bundle.distillation is None and not bundle.sources:
        return []

    plans: list[DiscordMessagePlan] = []

    if mode == "per_report":
        # Option C: Pure native Discord Markdown (zero Embed boxes, zero .md attachments by default).
        # Post individual source reports first, then Daily Digest last so it sits at top of Forum.
        for src in bundle.sources:
            plans.extend(
                _build_markdown_source_post_plans(
                    src,
                    date=bundle.date,
                    attach_markdown=include_source_files,
                    channel_type=channel_type,
                )
            )
        if bundle.distillation is not None:
            plans.extend(
                _build_markdown_distillation_post_plans(
                    bundle,
                    attach_markdown=include_source_files,
                    channel_type=channel_type,
                )
            )
        elif not plans:
            return []
        for plan in plans:
            validate_message_plan(plan)
        return plans

    if mode == "distillation_only":
        plans = _build_distillation_post_plans(
            bundle,
            channel_type=channel_type,
            include_index=False,
            include_pillars=False,
        )
        for plan in plans:
            validate_message_plan(plan)
        return plans

    # digest or full: single daily thread with distillation opener
    plans = _build_distillation_post_plans(
        bundle,
        channel_type=channel_type,
        include_index=True,
        include_pillars=True,
    )

    if mode == "full" and bundle.sources:
        current_embeds: list[dict] = []
        current_chars = 0
        for src in bundle.sources:
            emb = _build_source_embed(src, include_body_preview=False)
            ecount = embed_char_count(emb)
            if current_embeds and (
                len(current_embeds) >= 5 or current_chars + ecount > SAFE_TOTAL_EMBED_CHARS
            ):
                plans.append(DiscordMessagePlan(content=None, embeds=current_embeds, files=[]))
                current_embeds = []
                current_chars = 0
            current_embeds.append(emb)
            current_chars += ecount
        if current_embeds:
            plans.append(DiscordMessagePlan(content=None, embeds=current_embeds, files=[]))

    if include_source_files and bundle.sources:
        batches = batch_attachment_files([src.path for src in bundle.sources])
        total_batches = len(batches)
        for idx, batch in enumerate(batches, start=1):
            label = (
                f"📎 Source Reports (Batch {idx}/{total_batches} — {len(batch)} file(s))"
                if total_batches > 1
                else f"📎 Source Reports ({len(batch)} file(s))"
            )
            plans.append(DiscordMessagePlan(content=label, embeds=[], files=batch))

    for plan in plans:
        validate_message_plan(plan)
    return plans


def build_single_report_plan(
    report_path: Path,
    repo_root: Path,
    *,
    attach_markdown: bool = False,
    channel_type: str = "forum",
    thread_id: str | None = None,
) -> list[DiscordMessagePlan]:
    """Build validated Discord message plan(s) for a single Markdown report file (Option C native Markdown)."""
    if channel_type not in VALID_CHANNEL_TYPES:
        raise ValueError(
            f"Unsupported channel_type '{channel_type}': expected one of {sorted(VALID_CHANNEL_TYPES)}"
        )

    rel_parts = report_path.relative_to(repo_root / "reports").parts
    category_dir = rel_parts[0] if rel_parts else "Report"
    is_distillation = category_dir == "distillations" or report_path.name.startswith(
        "Knowledge_Distillation_"
    )

    date_match = re.search(r"(\d{4})_(\d{2})_(\d{2})", report_path.as_posix())
    report_date = (
        f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        if date_match
        else datetime.now().strftime("%Y-%m-%d")
    )

    if is_distillation:
        dist = parse_distillation(report_path, repo_root)
        dummy_bundle = DailyReportBundle(date=report_date, distillation=dist, sources=[])
        plans = _build_markdown_distillation_post_plans(
            dummy_bundle,
            attach_markdown=attach_markdown,
            channel_type=channel_type,
            existing_thread_id=thread_id,
        )
    else:
        cat_label = category_dir.split("_", 1)[0] if "_" in category_dir else category_dir
        src = parse_source_report(report_path, cat_label, repo_root)
        plans = _build_markdown_source_post_plans(
            src,
            date=report_date,
            attach_markdown=attach_markdown,
            channel_type=channel_type,
            existing_thread_id=thread_id,
        )

    for plan in plans:
        validate_message_plan(plan)
    return plans
