"""Discord dark-mode PNG renderer for GFM Markdown comparison tables."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Sequence

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - graceful fallback when Pillow absent
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]

# Discord Dark Theme Palette
BG_OUTER = (30, 31, 34)       # #1E1F22
BG_CARD = (43, 45, 49)        # #2B2D31
BG_HEADER = (35, 36, 40)      # #232428
BG_ROW_EVEN = (43, 45, 49)    # #2B2D31
BG_ROW_ODD = (49, 51, 56)     # #313338
BORDER_COLOR = (63, 65, 71)   # #3F4147
DIVIDER_COLOR = (56, 58, 64)  # #383A40
ACCENT_BAR = (88, 101, 242)   # #5865F2 (Discord Blurple)
TEXT_HEADER = (242, 243, 245) # #F2F3F5
TEXT_COL0 = (255, 255, 255)   # #FFFFFF
TEXT_BODY = (224, 227, 230)   # #E0E3E6
TEXT_MUTED = (200, 205, 212)  # #C8CDD4

_REGULAR_FONT_CANDIDATES = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

_BOLD_FONT_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def is_pillow_available() -> bool:
    """Return True when Pillow is importable."""
    return Image is not None and ImageDraw is not None and ImageFont is not None


def _load_font(size: int, *, bold: bool = False):
    candidates = _BOLD_FONT_CANDIDATES if bold else _REGULAR_FONT_CANDIDATES
    for candidate in candidates:
        if Path(candidate).is_file():
            try:
                # For Hiragino Sans GB.ttc, index 3 is W6 (bold) and index 0 is W3 (regular)
                if candidate.endswith("Hiragino Sans GB.ttc") and bold:
                    try:
                        return ImageFont.truetype(candidate, size=size, index=3)
                    except Exception:
                        pass
                return ImageFont.truetype(candidate, size=size, index=0)
            except Exception:
                continue
    return ImageFont.load_default()


def _strip_md_emphasis(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    return cleaned.strip()


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    """Wrap CJK + Latin text cleanly by measured pixel width."""
    clean = _strip_md_emphasis(text)
    if not clean:
        return [""]

    lines: list[str] = []
    # Tokenize into Latin words/numbers or individual CJK chars, keeping closing punctuation bound to prior token
    raw_tokens = re.findall(r"[A-Za-z0-9_./:+%-]+|\s+|.", clean)
    tokens: list[str] = []
    no_line_start = set("）)】」』》〉，。、：；！？!?,.:;%)")
    for tok in raw_tokens:
        if tokens and len(tok) == 1 and tok in no_line_start and not tokens[-1].isspace():
            tokens[-1] += tok
        else:
            tokens.append(tok)
    current = ""
    for tok in tokens:
        if not current and tok.isspace():
            continue
        candidate = current + tok
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current.rstrip())
            current = "" if tok.isspace() else tok
            if draw.textlength(current, font=font) <= max_width:
                continue
        # Hard-wrap an overly long single Latin token
        buf = ""
        for ch in tok:
            if buf and draw.textlength(buf + ch, font=font) > max_width:
                lines.append(buf)
                buf = ch
            else:
                buf += ch
        current = buf
    if current.strip():
        lines.append(current.rstrip())
    return lines or [""]


def _compute_col_widths(
    draw,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    font_header,
    font_body,
    total_inner_width: int,
) -> list[int]:
    num_cols = len(headers)
    if num_cols == 0:
        return []

    raw_weights: list[float] = []
    for c in range(num_cols):
        hdr_w = draw.textlength(_strip_md_emphasis(headers[c]), font=font_header)
        cell_ws = [
            draw.textlength(_strip_md_emphasis(r[c]) if c < len(r) else "", font=font_body)
            for r in rows
        ]
        avg_w = (sum(cell_ws) / len(cell_ws)) if cell_ws else hdr_w
        max_w = max([hdr_w] + cell_ws)
        # Blend average and max so one long cell doesn't starve other columns
        weight = max(140.0, 0.65 * avg_w + 0.35 * min(max_w, 520.0))
        if c == 0:
            weight = max(weight, 220.0)
        raw_weights.append(weight)

    total_w = sum(raw_weights)
    min_col = max(150, int(total_inner_width * 0.14))
    widths = [max(min_col, int(total_inner_width * (w / total_w))) for w in raw_weights]

    # Normalize sum to exact total_inner_width
    diff = total_inner_width - sum(widths)
    if widths:
        widest = max(range(num_cols), key=lambda idx: widths[idx])
        widths[widest] = max(min_col, widths[widest] + diff)
    return widths


def render_table_png(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    title: str | None = None,
    width: int = 1240,
) -> bytes:
    """Render a GFM table as a crisp Retina Discord dark-mode PNG image in memory."""
    if not is_pillow_available():
        raise RuntimeError("Pillow is not installed")
    if not headers or not rows:
        raise ValueError("Table must have headers and at least one row")

    num_cols = len(headers)
    norm_rows = [
        [r[c] if c < len(r) else "" for c in range(num_cols)]
        for r in rows
    ]

    outer_pad = 10
    cell_pad_x = 18
    cell_pad_y = 16
    accent_h = 6
    title_h = 54 if title else 0

    font_title = _load_font(30, bold=True)
    font_header = _load_font(28, bold=True)
    font_col0 = _load_font(27, bold=True)
    font_body = _load_font(27, bold=False)

    line_height_header = 38
    line_height_body = 38

    # Measure pass on a tiny scratch canvas
    scratch = Image.new("RGB", (10, 10), BG_OUTER)
    sdraw = ImageDraw.Draw(scratch)

    card_width = width - outer_pad * 2
    col_widths = _compute_col_widths(
        sdraw, headers, norm_rows, font_header, font_body, card_width
    )

    wrapped_headers = [
        _wrap_text(sdraw, headers[c], font_header, max(40, col_widths[c] - cell_pad_x * 2))
        for c in range(num_cols)
    ]
    header_row_h = max(len(lines) for lines in wrapped_headers) * line_height_header + cell_pad_y * 2

    wrapped_rows: list[list[list[str]]] = []
    row_heights: list[int] = []
    for row in norm_rows:
        w_cells: list[list[str]] = []
        for c in range(num_cols):
            fnt = font_col0 if c == 0 else font_body
            w_cells.append(_wrap_text(sdraw, row[c], fnt, max(40, col_widths[c] - cell_pad_x * 2)))
        wrapped_rows.append(w_cells)
        row_heights.append(max(len(lines) for lines in w_cells) * line_height_body + cell_pad_y * 2)

    card_height = accent_h + title_h + header_row_h + sum(row_heights)
    total_height = card_height + outer_pad * 2

    img = Image.new("RGB", (width, total_height), BG_OUTER)
    draw = ImageDraw.Draw(img)

    x0, y0 = outer_pad, outer_pad
    x1, y1 = x0 + card_width, y0 + card_height

    # Card background & border
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
    # Top Discord Blurple accent bar
    draw.rounded_rectangle([x0, y0, x1, y0 + accent_h + 10], radius=16, fill=ACCENT_BAR)
    draw.rectangle([x0, y0 + accent_h, x1, y0 + accent_h + 12], fill=BG_HEADER)

    cursor_y = y0 + accent_h

    if title:
        draw.rectangle([x0 + 1, cursor_y, x1 - 1, cursor_y + title_h], fill=BG_HEADER)
        draw.text((x0 + cell_pad_x, cursor_y + 12), _strip_md_emphasis(title), font=font_title, fill=TEXT_HEADER)
        cursor_y += title_h

    # Header row
    draw.rectangle([x0 + 1, cursor_y, x1 - 1, cursor_y + header_row_h], fill=BG_HEADER)
    if title:
        draw.line([(x0 + 1, cursor_y), (x1 - 1, cursor_y)], fill=DIVIDER_COLOR, width=2)
    col_x = x0
    for c in range(num_cols):
        if c > 0:
            draw.line([(col_x, cursor_y), (col_x, cursor_y + header_row_h)], fill=DIVIDER_COLOR, width=1)
        ty = cursor_y + cell_pad_y
        for line in wrapped_headers[c]:
            draw.text((col_x + cell_pad_x, ty), line, font=font_header, fill=TEXT_HEADER)
            ty += line_height_header
        col_x += col_widths[c]
    cursor_y += header_row_h
    draw.line([(x0 + 1, cursor_y), (x1 - 1, cursor_y)], fill=BORDER_COLOR, width=2)

    # Body rows
    for r_idx, (w_cells, rh) in enumerate(zip(wrapped_rows, row_heights)):
        row_bg = BG_ROW_EVEN if r_idx % 2 == 0 else BG_ROW_ODD
        is_last = r_idx == len(wrapped_rows) - 1
        if is_last:
            draw.rounded_rectangle([x0 + 1, cursor_y, x1 - 1, cursor_y + rh - 1], radius=14, fill=row_bg)
            draw.rectangle([x0 + 1, cursor_y, x1 - 1, cursor_y + 16], fill=row_bg)
        else:
            draw.rectangle([x0 + 1, cursor_y, x1 - 1, cursor_y + rh], fill=row_bg)

        col_x = x0
        for c in range(num_cols):
            if c > 0:
                draw.line([(col_x, cursor_y), (col_x, cursor_y + rh)], fill=DIVIDER_COLOR, width=1)
            fnt = font_col0 if c == 0 else font_body
            color = TEXT_COL0 if c == 0 else (TEXT_MUTED if c == num_cols - 1 and num_cols >= 4 else TEXT_BODY)
            ty = cursor_y + cell_pad_y
            for line in w_cells[c]:
                draw.text((col_x + cell_pad_x, ty), line, font=fnt, fill=color)
                ty += line_height_body
            col_x += col_widths[c]

        cursor_y += rh
        if not is_last:
            draw.line([(x0 + 1, cursor_y), (x1 - 1, cursor_y)], fill=DIVIDER_COLOR, width=1)

    # Re-stroke clean rounded outer border on top
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=BORDER_COLOR, width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# --- Mermaid Flowchart / Sequence PNG Renderer ---

ACCENT_ARROW = (129, 140, 248)     # #818CF8 (Soft Indigo arrow)
BG_NODE = (53, 55, 62)             # #35373E
BG_NODE_DECISION = (61, 56, 78)    # #3D384E (Subtle violet tint for decisions)
BORDER_NODE = (94, 102, 120)       # #5E6678
BORDER_DECISION = (129, 140, 248)  # #818CF8
BG_SUBGRAPH = (35, 36, 40)         # #232428
BG_BADGE = (88, 101, 242)          # #5865F2

_M_NODE_DEF_RE = re.compile(
    r'([A-Za-z0-9_]+)\s*(?:\[\s*"([^"]+)"\s*\]|\{\s*"([^"]+)"\s*\}|\(\s*"([^"]+)"\s*\)|\[([^\]]+)\]|\{([^}]+)\})'
)
_M_EDGE_SPLIT_RE = re.compile(
    r'\s*(?:--\s*"?([^"\n]+?)"?\s*-->|-\.\s*"?([^"\n]+?)"?\s*\.->|-->|-.->|==>)\s*'
)
_M_SUBGRAPH_RE = re.compile(r'^\s*subgraph\s+\S+(?:\s+\["?([^"\]]+)"?\])?\s*$')
_M_SEQ_EDGE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*->>?\+?\s*([A-Za-z0-9_]+)\s*:\s*(.+)$')


def _clean_m_label(raw: str) -> str:
    cleaned = re.sub(r"<br\s*/?>", " / ", raw, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip().strip('"')


def _draw_arrowhead(draw, x: int, y: int, direction: str, color=ACCENT_ARROW, size: int = 10) -> None:
    if direction == "right":
        pts = [(x, y), (x - size, y - size // 2 - 2), (x - size, y + size // 2 + 2)]
    elif direction == "down":
        pts = [(x, y), (x - size // 2 - 2, y - size), (x + size // 2 + 2, y - size)]
    else:
        pts = [(x, y), (x + size, y - size // 2 - 2), (x + size, y + size // 2 + 2)]
    draw.polygon(pts, fill=color)


def _render_linear_flow_png(labels: Sequence[str], *, width: int = 1240) -> bytes:
    """Render a linear flow as crisp rounded dark-mode step cards (up to 3 per row, left-to-right)."""
    outer_pad = 16
    inner_pad = 26
    accent_h = 6
    cols = min(len(labels), 3)
    gap_x = 48
    gap_y = 54
    pad_x = 18
    pad_y = 18

    font_badge = _load_font(20, bold=True)
    font_node = _load_font(26, bold=True)
    line_h = 36

    card_w = width - outer_pad * 2
    usable_w = card_w - inner_pad * 2
    node_w = (usable_w - gap_x * (cols - 1)) // cols

    scratch = Image.new("RGB", (10, 10), BG_OUTER)
    sdraw = ImageDraw.Draw(scratch)

    # Group into rows of `cols`
    rows_labels = [list(labels[i : i + cols]) for i in range(0, len(labels), cols)]
    wrapped_rows: list[list[list[str]]] = []
    row_heights: list[int] = []
    for r_labels in rows_labels:
        w_row = [_wrap_text(sdraw, lbl, font_node, max(60, node_w - pad_x * 2)) for lbl in r_labels]
        wrapped_rows.append(w_row)
        max_lines = max(len(w) for w in w_row)
        row_heights.append(max(108, 34 + max_lines * line_h + pad_y * 2))

    card_h = accent_h + inner_pad * 2 + sum(row_heights) + gap_y * max(0, len(row_heights) - 1)
    total_h = card_h + outer_pad * 2

    img = Image.new("RGB", (width, total_h), BG_OUTER)
    draw = ImageDraw.Draw(img)

    x0, y0 = outer_pad, outer_pad
    x1, y1 = x0 + card_w, y0 + card_h
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
    draw.rounded_rectangle([x0, y0, x1, y0 + accent_h + 10], radius=16, fill=ACCENT_BAR)
    draw.rectangle([x0, y0 + accent_h, x1, y0 + accent_h + 12], fill=BG_CARD)

    cursor_y = y0 + accent_h + inner_pad
    step_num = 1
    row_boxes: list[list[tuple[int, int, int, int]]] = []

    for r_idx, (w_row, rh) in enumerate(zip(wrapped_rows, row_heights)):
        boxes: list[tuple[int, int, int, int]] = []
        n_in_row = len(w_row)
        row_total_w = n_in_row * node_w + (n_in_row - 1) * gap_x
        start_x = x0 + inner_pad + (usable_w - row_total_w) // 2

        for c_idx, lines in enumerate(w_row):
            bx0 = start_x + c_idx * (node_w + gap_x)
            by0 = cursor_y
            bx1 = bx0 + node_w
            by1 = by0 + rh
            boxes.append((bx0, by0, bx1, by1))

            # Node box
            draw.rounded_rectangle(
                [bx0, by0, bx1, by1],
                radius=14,
                fill=BG_NODE,
                outline=BORDER_NODE,
                width=2,
            )
            # Step badge pill (01, 02, ...)
            badge_txt = f"{step_num:02d}"
            step_num += 1
            badge_w = 46
            badge_h = 28
            draw.rounded_rectangle(
                [bx0 + pad_x, by0 + 12, bx0 + pad_x + badge_w, by0 + 12 + badge_h],
                radius=8,
                fill=BG_BADGE,
            )
            bw = draw.textlength(badge_txt, font=font_badge)
            draw.text(
                (bx0 + pad_x + (badge_w - bw) / 2, by0 + 15),
                badge_txt,
                font=font_badge,
                fill=TEXT_COL0,
            )

            # Centered text below badge
            text_block_h = len(lines) * line_h
            ty = by0 + 44 + max(0, (rh - 44 - pad_y - text_block_h) // 2)
            for line in lines:
                lw = draw.textlength(line, font=font_node)
                tx = bx0 + max(pad_x, int((node_w - lw) / 2))
                draw.text((tx, ty), line, font=font_node, fill=TEXT_COL0)
                ty += line_h

            # Horizontal arrow to next node in same row
            if c_idx > 0:
                prev_x1 = boxes[c_idx - 1][2]
                mid_y = (by0 + by1) // 2
                draw.line([(prev_x1 + 4, mid_y), (bx0 - 12, mid_y)], fill=ACCENT_ARROW, width=4)
                _draw_arrowhead(draw, bx0 - 4, mid_y, "right", size=12)

        row_boxes.append(boxes)

        # Connector from end of previous row to start of current row
        if r_idx > 0:
            prev_last = row_boxes[r_idx - 1][-1]
            curr_first = boxes[0]
            px = (prev_last[0] + prev_last[2]) // 2
            py = prev_last[3]
            cx = (curr_first[0] + curr_first[2]) // 2
            cy = curr_first[1]
            mid_gap_y = (py + cy) // 2
            draw.line([(px, py + 2), (px, mid_gap_y)], fill=ACCENT_ARROW, width=4)
            draw.line([(px, mid_gap_y), (cx, mid_gap_y)], fill=ACCENT_ARROW, width=4)
            draw.line([(cx, mid_gap_y), (cx, cy - 10)], fill=ACCENT_ARROW, width=4)
            _draw_arrowhead(draw, cx, cy - 3, "down", size=12)

        cursor_y += rh + gap_y

    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=BORDER_COLOR, width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _render_edge_flow_png(
    sections: Sequence[tuple[str | None, list[tuple[str, str, str]]]],
    *,
    width: int = 1240,
) -> bytes:
    """Render branched / subgraph / sequence Mermaid edges as a crisp Discord dark-mode flow card."""
    outer_pad = 16
    inner_pad = 22
    accent_h = 6
    box_pad_x = 16
    box_pad_y = 12

    font_sec = _load_font(25, bold=True)
    font_node = _load_font(23, bold=True)
    font_edge = _load_font(20, bold=False)
    line_h = 32

    card_w = width - outer_pad * 2
    usable_w = card_w - inner_pad * 2
    arrow_zone_w = 220
    node_w = (usable_w - arrow_zone_w) // 2

    scratch = Image.new("RGB", (10, 10), BG_OUTER)
    sdraw = ImageDraw.Draw(scratch)

    measured: list[tuple[str | None, list[tuple[list[str], list[str], list[str], int]]]] = []
    total_inner_h = 0
    for sec_title, edges in sections:
        if not edges:
            continue
        if sec_title:
            total_inner_h += 46
        m_edges = []
        for src, lbl, dst in edges:
            w_src = _wrap_text(sdraw, src, font_node, max(60, node_w - box_pad_x * 2))
            w_dst = _wrap_text(sdraw, dst, font_node, max(60, node_w - box_pad_x * 2))
            w_lbl = _wrap_text(sdraw, lbl, font_edge, max(60, arrow_zone_w - 28)) if lbl else []
            rh = max(len(w_src), len(w_dst)) * line_h + box_pad_y * 2
            if w_lbl:
                rh = max(rh, len(w_lbl) * 26 + 34)
            rh = max(rh, 60)
            m_edges.append((w_src, w_lbl, w_dst, rh))
            total_inner_h += rh + 14
        total_inner_h += 10
        measured.append((sec_title, m_edges))

    card_h = accent_h + inner_pad * 2 + max(total_inner_h, 60)
    total_h = card_h + outer_pad * 2

    img = Image.new("RGB", (width, total_h), BG_OUTER)
    draw = ImageDraw.Draw(img)

    x0, y0 = outer_pad, outer_pad
    x1, y1 = x0 + card_w, y0 + card_h
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
    draw.rounded_rectangle([x0, y0, x1, y0 + accent_h + 10], radius=16, fill=ACCENT_BAR)
    draw.rectangle([x0, y0 + accent_h, x1, y0 + accent_h + 12], fill=BG_CARD)

    cursor_y = y0 + accent_h + inner_pad
    left_x = x0 + inner_pad
    right_x = left_x + node_w + arrow_zone_w

    for sec_title, m_edges in measured:
        if sec_title:
            draw.rounded_rectangle(
                [left_x, cursor_y, x1 - inner_pad, cursor_y + 38],
                radius=8,
                fill=BG_SUBGRAPH,
            )
            draw.text((left_x + 14, cursor_y + 6), sec_title, font=font_sec, fill=ACCENT_ARROW)
            cursor_y += 46

        for w_src, w_lbl, w_dst, rh in m_edges:
            # Source node
            draw.rounded_rectangle(
                [left_x, cursor_y, left_x + node_w, cursor_y + rh],
                radius=10,
                fill=BG_NODE,
                outline=BORDER_NODE,
                width=2,
            )
            ty = cursor_y + (rh - len(w_src) * line_h) // 2
            for line in w_src:
                draw.text((left_x + box_pad_x, ty), line, font=font_node, fill=TEXT_COL0)
                ty += line_h

            # Arrow + optional edge label
            mid_y = cursor_y + rh // 2
            ax0 = left_x + node_w + 6
            ax1 = right_x - 10
            if w_lbl:
                lbl_block_h = len(w_lbl) * 26
                ly = cursor_y + max(2, (rh - lbl_block_h) // 2 - 10)
                for line in w_lbl:
                    lw = draw.textlength(line, font=font_edge)
                    draw.text((ax0 + (arrow_zone_w - 16 - lw) / 2, ly), line, font=font_edge, fill=TEXT_MUTED)
                    ly += 26
                arrow_y = min(cursor_y + rh - 12, ly + 4)
            else:
                arrow_y = mid_y
            draw.line([(ax0, arrow_y), (ax1 - 6, arrow_y)], fill=ACCENT_ARROW, width=3)
            _draw_arrowhead(draw, ax1 + 2, arrow_y, "right", size=10)

            # Target node
            draw.rounded_rectangle(
                [right_x, cursor_y, right_x + node_w, cursor_y + rh],
                radius=10,
                fill=BG_NODE_DECISION,
                outline=BORDER_DECISION,
                width=2,
            )
            ty = cursor_y + (rh - len(w_dst) * line_h) // 2
            for line in w_dst:
                draw.text((right_x + box_pad_x, ty), line, font=font_node, fill=TEXT_COL0)
                ty += line_h

            cursor_y += rh + 14
        cursor_y += 10

    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=BORDER_COLOR, width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_mermaid_png(block_text: str, *, width: int = 1240) -> bytes:
    """Render a fenced ```mermaid``` block as a crisp Discord dark-mode PNG in memory."""
    if not is_pillow_available():
        raise RuntimeError("Pillow is not installed")

    inner = re.sub(r"^```mermaid\b[^\n]*\n?", "", block_text.strip(), flags=re.IGNORECASE)
    inner = re.sub(r"\n?```$", "", inner).strip()
    lines = [ln.rstrip() for ln in inner.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise ValueError("Mermaid diagram has no renderable edges")

    header = lines[0].strip().lower()
    if header.startswith("sequencediagram"):
        participants: dict[str, str] = {}
        edges: list[tuple[str, str, str]] = []
        for ln in lines[1:]:
            p_m = re.match(r"^\s*participant\s+(\S+)\s+as\s+(.+)$", ln)
            if p_m:
                participants[p_m.group(1)] = p_m.group(2).strip()
                continue
            s_m = _M_SEQ_EDGE_RE.match(ln)
            if s_m:
                src = participants.get(s_m.group(1), s_m.group(1))
                dst = participants.get(s_m.group(2), s_m.group(2))
                edges.append((src, _clean_m_label(s_m.group(3)), dst))
        if not edges:
            raise ValueError("Sequence diagram has no edges")
        return _render_edge_flow_png([(None, edges)], width=width)

    node_labels: dict[str, str] = {}
    for ln in lines[1:]:
        if _M_SUBGRAPH_RE.match(ln) or ln.strip() == "end":
            continue
        for m in _M_NODE_DEF_RE.finditer(ln):
            nid = m.group(1)
            label = next((g for g in m.groups()[1:] if g is not None), nid)
            node_labels[nid] = _clean_m_label(label)

    def _resolve(token: str) -> str:
        t = token.strip()
        m = _M_NODE_DEF_RE.search(t)
        if m:
            nid = m.group(1)
            label = next((g for g in m.groups()[1:] if g is not None), nid)
            return _clean_m_label(label)
        if "&" in t:
            return " + ".join(node_labels.get(p.strip(), p.strip()) for p in t.split("&"))
        return node_labels.get(t, _clean_m_label(t))

    has_subgraph = any(_M_SUBGRAPH_RE.match(ln) for ln in lines[1:])
    edge_lines = [ln for ln in lines[1:] if any(op in ln for op in ("-->", "-.->", "==>", ".->"))]

    # Single linear chain -> sleek step-card diagram
    if not has_subgraph and len(edge_lines) == 1:
        parts = _M_EDGE_SPLIT_RE.split(edge_lines[0])
        has_edge_labels = any((parts[i + 1] or parts[i + 2]) for i in range(0, len(parts) - 3, 3))
        if not has_edge_labels:
            raw_nodes = [n for n in parts[0::3] if n and n.strip()]
            labels_inline = [_resolve(n) for n in raw_nodes]
            if len(labels_inline) >= 2:
                return _render_linear_flow_png(labels_inline, width=width)

    sections: list[tuple[str | None, list[tuple[str, str, str]]]] = []
    current_title: str | None = None
    current_edges: list[tuple[str, str, str]] = []

    for ln in lines[1:]:
        stripped = ln.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        if stripped == "end":
            if current_edges:
                sections.append((current_title, current_edges))
                current_edges = []
            current_title = None
            continue
        sg = _M_SUBGRAPH_RE.match(ln)
        if sg:
            if current_edges:
                sections.append((current_title, current_edges))
                current_edges = []
            current_title = _clean_m_label(sg.group(1) or stripped)
            continue
        if any(op in ln for op in ("-->", "-.->", "==>", ".->")):
            parts = _M_EDGE_SPLIT_RE.split(stripped)
            idx = 0
            while idx + 3 < len(parts):
                src = _resolve(parts[idx])
                elbl = _clean_m_label(parts[idx + 1] or parts[idx + 2] or "")
                dst = _resolve(parts[idx + 3])
                current_edges.append((src, elbl, dst))
                idx += 3

    if current_edges:
        sections.append((current_title, current_edges))
    if not sections:
        raise ValueError("No Mermaid edges found")
    return _render_edge_flow_png(sections, width=width)

