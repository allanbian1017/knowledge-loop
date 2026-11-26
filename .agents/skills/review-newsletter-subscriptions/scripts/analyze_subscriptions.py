#!/usr/bin/env python3
"""
Newsletter Subscription Telemetry Analyzer

Aggregates statistics from $DATA_REPO/reports/Newsletter_YYYY_MM_DD/ and suggestion files
(suggestions_reviewed.md, suggestions_filtered.md, suggestions_pending.md) over
a specified time window (default: 30 days) to evaluate newsletter ROI and triage.
"""

import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import glob
import json
import os
from pathlib import Path
import re
import sys

# Allow importing shared workspace_paths from knowledge-loop
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from scripts.lib.workspace_paths import resolve_data_repo
except ImportError:
    resolve_data_repo = None  # type: ignore[assignment]

DEFAULT_ALIASES: list[dict] = []  # Configure optional custom aliases in $DATA_REPO/data/newsletter_aliases.json

def load_newsletter_aliases(workspace_dir: str | Path | None = None) -> list[dict]:
    """Load optional user-configured newsletter aliases from $DATA_REPO/data/newsletter_aliases.json."""
    aliases = list(DEFAULT_ALIASES)
    if workspace_dir:
        alias_file = Path(workspace_dir) / "data" / "newsletter_aliases.json"
        if alias_file.is_file():
            try:
                loaded = json.loads(alias_file.read_text(encoding="utf-8"))
                custom = loaded.get("aliases", []) if isinstance(loaded, dict) else []
                if isinstance(custom, list):
                    # Prepend user aliases so user overrides take precedence
                    aliases = custom + aliases
            except Exception:
                pass
    return aliases


def normalize_source(
    filename: str = "",
    title_url: str = "",
    aliases: list[dict] | None = None,
) -> str:
    """Normalize filename, subject, and URL patterns to canonical newsletter names."""
    combined = f"{filename} {title_url}".lower()
    active_aliases = aliases if aliases is not None else DEFAULT_ALIASES

    for rule in active_aliases:
        patterns = rule.get("patterns", [])
        canonical = rule.get("canonical", "")
        if canonical and any(str(pat).lower() in combined for pat in patterns):
            return canonical

    if filename:
        clean_fn = os.path.splitext(filename)[0]
        parts = clean_fn.split("_")
        return " ".join(parts[:2])
    return "Other / Unknown"


def parse_suggestion_file(filepath: str):
    """Parse suggestion entries from a markdown file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = text.split("\n---\n")
    entries = []
    for chunk in chunks:
        lines = chunk.strip().split("\n")
        if not lines or not lines[0].startswith("### "):
            continue
        header = lines[0]
        parts = header[4:].split(" | ")
        date_str = parts[0].strip() if len(parts) > 0 else ""
        entry_type = parts[1].strip() if len(parts) > 1 else ""
        title_url = parts[2].strip() if len(parts) > 2 else ""

        report_path, feedback, comment, category, score_status, suggestion_text = "", "", "", "", "", ""
        for line in lines[1:]:
            l_strip = line.strip()
            if "🏷️" in l_strip:
                cat_m = re.search(r"🏷️\s*([^\|]+)", l_strip)
                if cat_m:
                    category = cat_m.group(1).strip()
                sc_m = re.search(r"📊\s*(.+)", l_strip)
                if sc_m:
                    score_status = sc_m.group(1).strip()
            elif "**Feedback**:" in l_strip or "- Feedback:" in l_strip:
                feedback = l_strip
            elif "**Comment**:" in l_strip or "- Comment:" in l_strip:
                comment = l_strip
            elif "[報告]" in l_strip or "[完整報告]" in l_strip:
                report_path = l_strip
            elif "建議" in l_strip:
                suggestion_text = l_strip

        entries.append({
            "date": date_str,
            "type": entry_type,
            "title_url": title_url,
            "category": category,
            "score_status": score_status,
            "feedback": feedback,
            "comment": comment,
            "report_path": report_path,
            "suggestion": suggestion_text,
            "raw": chunk,
        })
    return entries


def extract_veto_category(score_status: str) -> str:
    """Extract the specific veto or low-score reason from score_status."""
    m = re.search(r"Hard-veto:\s*([^\)]+)", score_status)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"Ambiguity blocklist:\s*([^\)]+)", score_status)
    if m2:
        return f"Ambiguity: {m2.group(1).strip()}"
    if "Below threshold" in score_status:
        return "Below threshold"
    if "VETO" in score_status:
        return "Hard Veto (Other)"
    return "Other Filtered"


def analyze_subscriptions(workspace_dir: str, days: int = 30, start_date: str = None, end_date: str = None):
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = datetime.now()

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = end_dt - timedelta(days=days)

    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    aliases = load_newsletter_aliases(workspace_dir)

    stats = defaultdict(lambda: {
        "reports_count": 0,
        "report_dates": set(),
        "reviewed_count": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "filtered_count": 0,
        "pending_count": 0,
        "veto_reasons": defaultdict(int),
        "accepted_examples": [],
        "rejected_examples": [],
        "filtered_examples": [],
    })

    reports_glob = os.path.join(workspace_dir, "reports", "Newsletter_*")
    for folder in glob.glob(reports_glob):
        if not os.path.isdir(folder):
            continue
        folder_name = os.path.basename(folder)
        m = re.match(r"Newsletter_(\d{4})_(\d{2})_(\d{2})", folder_name)
        if not m:
            continue
        d_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if not (start_str <= d_str <= end_str):
            continue

        for md_file in glob.glob(os.path.join(folder, "*.md")):
            fn = os.path.basename(md_file)
            src = normalize_source(filename=fn, aliases=aliases)
            stats[src]["reports_count"] += 1
            stats[src]["report_dates"].add(d_str)

    reviewed_path = os.path.join(workspace_dir, "data", "suggestions_reviewed.md")
    for entry in parse_suggestion_file(reviewed_path):
        if "Newsletter" not in entry["type"] and "Newsletter_" not in entry["report_path"]:
            continue
        d_str = entry["date"]
        if not (start_str <= d_str <= end_str):
            continue
        rp_fn = os.path.basename(entry["report_path"].split("(")[-1].rstrip(")")) if "(" in entry["report_path"] else ""
        src = normalize_source(filename=rp_fn, title_url=entry["title_url"], aliases=aliases)
        stats[src]["reviewed_count"] += 1
        if "✅" in entry["feedback"] or "Accept" in entry["feedback"]:
            stats[src]["accepted_count"] += 1
            stats[src]["accepted_examples"].append(f"[{d_str}] {entry['title_url']} — {entry['comment']}")
        elif "❌" in entry["feedback"] or "Reject" in entry["feedback"]:
            stats[src]["rejected_count"] += 1
            stats[src]["rejected_examples"].append(f"[{d_str}] {entry['title_url']} — {entry['comment']}")

    filtered_path = os.path.join(workspace_dir, "data", "suggestions_filtered.md")
    for entry in parse_suggestion_file(filtered_path):
        if "Newsletter" not in entry["type"] and "Newsletter_" not in entry["report_path"]:
            continue
        d_str = entry["date"]
        if not (start_str <= d_str <= end_str):
            continue
        rp_fn = os.path.basename(entry["report_path"].split("(")[-1].rstrip(")")) if "(" in entry["report_path"] else ""
        src = normalize_source(filename=rp_fn, title_url=entry["title_url"], aliases=aliases)
        stats[src]["filtered_count"] += 1
        reason = extract_veto_category(entry["score_status"])
        stats[src]["veto_reasons"][reason] += 1
        stats[src]["filtered_examples"].append(f"[{d_str}] {entry['title_url']} ({reason})")

    pending_path = os.path.join(workspace_dir, "data", "suggestions_pending.md")
    for entry in parse_suggestion_file(pending_path):
        if "Newsletter" not in entry["type"] and "Newsletter_" not in entry["report_path"]:
            continue
        d_str = entry["date"]
        if not (start_str <= d_str <= end_str):
            continue
        rp_fn = os.path.basename(entry["report_path"].split("(")[-1].rstrip(")")) if "(" in entry["report_path"] else ""
        src = normalize_source(filename=rp_fn, title_url=entry["title_url"], aliases=aliases)
        stats[src]["pending_count"] += 1

    results = []
    for src, s in stats.items():
        total_sugg = s["reviewed_count"] + s["filtered_count"] + s["pending_count"]
        acc_rate = (s["accepted_count"] / s["reviewed_count"] * 100) if s["reviewed_count"] > 0 else 0.0
        yield_rate = (s["accepted_count"] / total_sugg * 100) if total_sugg > 0 else 0.0
        veto_rate = (s["filtered_count"] / total_sugg * 100) if total_sugg > 0 else 0.0

        triage = "Watch"
        triage_reason = "Insufficient volume (< 3 reports) or no completed reviews."

        if s["reports_count"] >= 3 or total_sugg >= 3:
            if s["accepted_count"] >= 1 and (acc_rate >= 40.0 or yield_rate >= 25.0):
                triage = "Keep"
                triage_reason = f"Strong signal: {s['accepted_count']} accepted ({acc_rate:.0f}% acceptance, {yield_rate:.0f}% yield)."
            elif s["accepted_count"] >= 1 and (acc_rate < 40.0 or veto_rate >= 50.0):
                triage = "Adjust"
                triage_reason = f"Mixed signal: {s['accepted_count']} accepted but {s['rejected_count']} rejected & {s['filtered_count']} filtered."
            elif s["accepted_count"] == 0 and (s["rejected_count"] + s["filtered_count"] >= 3 or s["reports_count"] >= 4):
                triage = "Unsubscribe"
                triage_reason = f"Zero yield across {s['reports_count']} reports ({s['rejected_count']} rejected, {s['filtered_count']} filtered)."
            else:
                triage = "Watch"
                triage_reason = f"Evaluating: {s['reports_count']} reports, {s['pending_count']} pending."

        results.append({
            "source": src,
            "triage": triage,
            "triage_reason": triage_reason,
            "reports_count": s["reports_count"],
            "active_days": len(s["report_dates"]),
            "total_suggestions": total_sugg,
            "reviewed_count": s["reviewed_count"],
            "accepted_count": s["accepted_count"],
            "rejected_count": s["rejected_count"],
            "filtered_count": s["filtered_count"],
            "pending_count": s["pending_count"],
            "acceptance_rate": round(acc_rate, 1),
            "yield_rate": round(yield_rate, 1),
            "veto_rate": round(veto_rate, 1),
            "veto_reasons": dict(s["veto_reasons"]),
            "accepted_examples": s["accepted_examples"][:3],
            "rejected_examples": s["rejected_examples"][:3],
            "filtered_examples": s["filtered_examples"][:3],
        })

    triage_order = {"Unsubscribe": 0, "Adjust": 1, "Keep": 2, "Watch": 3}
    results.sort(key=lambda x: (triage_order.get(x["triage"], 9), -x["reports_count"], -x["total_suggestions"]))

    return {
        "window": {"start": start_str, "end": end_str, "days": (end_dt - start_dt).days},
        "total_newsletters_evaluated": len(results),
        "total_reports": sum(r["reports_count"] for r in results),
        "total_accepted": sum(r["accepted_count"] for r in results),
        "total_rejected": sum(r["rejected_count"] for r in results),
        "total_filtered": sum(r["filtered_count"] for r in results),
        "subscriptions": results,
    }


def format_markdown_table(data: dict) -> str:
    lines = []
    w = data["window"]
    lines.append(f"### Telemetry Window: {w['start']} to {w['end']} ({w['days']} days)")
    lines.append(
        f"**Total Newsletters**: {data['total_newsletters_evaluated']} | "
        f"**Total Reports**: {data['total_reports']} | "
        f"**Accepted**: {data['total_accepted']} | "
        f"**Rejected**: {data['total_rejected']} | "
        f"**Filtered/Vetoed**: {data['total_filtered']}\n"
    )
    lines.append("| Source | Triage | Reports | Accepted | Rejected | Filtered | Pending | Acc. Rate | Yield | Top Veto Reason |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

    for r in data["subscriptions"]:
        top_veto = "-"
        if r["veto_reasons"]:
            top_v = sorted(r["veto_reasons"].items(), key=lambda x: -x[1])[0]
            top_veto = f"{top_v[0]} ({top_v[1]})"
        lines.append(
            f"| **{r['source']}** | `{r['triage']}` | {r['reports_count']} | {r['accepted_count']} | "
            f"{r['rejected_count']} | {r['filtered_count']} | {r['pending_count']} | "
            f"{r['acceptance_rate']}% | {r['yield_rate']}% | {top_veto} |"
        )
    return "\n".join(lines)


def _default_data_repo() -> str:
    if resolve_data_repo is not None:
        try:
            return str(resolve_data_repo(require_exists=False))
        except FileNotFoundError:
            pass
    return os.getcwd()


def main():
    parser = argparse.ArgumentParser(description="Analyze newsletter subscription ROI over a time window.")
    parser.add_argument("--data-repo", "--workspace", dest="workspace", default=None, help="Data Repo root directory")
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days (default: 30)")
    parser.add_argument("--start-date", type=str, default=None, help="Explicit start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="Explicit end date YYYY-MM-DD")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    args = parser.parse_args()

    workspace = args.workspace or _default_data_repo()
    data = analyze_subscriptions(
        workspace_dir=workspace,
        days=args.days,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    if args.format == "markdown":
        print(format_markdown_table(data))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
