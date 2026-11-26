#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.validate_skill import validate_skill_file

SCRIPT_PATH = os.path.join(
    BASE_DIR, ".agents/skills/review-newsletter-subscriptions/scripts/analyze_subscriptions.py"
)
spec = importlib.util.spec_from_file_location("analyze_subscriptions_mod", SCRIPT_PATH)
analyze_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze_mod)

analyze_subscriptions = analyze_mod.analyze_subscriptions
normalize_source = analyze_mod.normalize_source
extract_veto_category = analyze_mod.extract_veto_category
format_markdown_table = analyze_mod.format_markdown_table


class TestReviewNewsletterSubscriptionsSkill(unittest.TestCase):
    def setUp(self):
        self.skill_dir = os.path.join(BASE_DIR, ".agents/skills/review-newsletter-subscriptions")
        self.skill_md = os.path.join(self.skill_dir, "SKILL.md")
        self.refs_dir = os.path.join(self.skill_dir, "references")
        self.evals_file = os.path.join(self.skill_dir, "evals/evals.json")
        self.readme_file = os.path.join(self.skill_dir, "README.md")

    def test_skill_frontmatter_validation(self):
        self.assertTrue(validate_skill_file(self.skill_md))

    def test_skill_lean_spine_budget(self):
        with open(self.skill_md, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertLess(len(lines), 200)

    def test_reference_files_exist_and_non_empty(self):
        for ref_name in ["triage_criteria.md", "review_template.md"]:
            ref_path = os.path.join(self.refs_dir, ref_name)
            self.assertTrue(os.path.exists(ref_path))
            with open(ref_path, "r", encoding="utf-8") as f:
                self.assertGreater(len(f.read().strip().splitlines()), 20)

    def test_triage_criteria_content(self):
        with open(os.path.join(self.refs_dir, "triage_criteria.md"), "r", encoding="utf-8") as f:
            content = f.read()
        for token in ["Keep", "Unsubscribe", "Adjust", "Watch", "Acceptance Rate", "Overall Yield"]:
            self.assertIn(token, content)

    def test_evals_json_structure(self):
        with open(self.evals_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("skill_name"), "review-newsletter-subscriptions")
        self.assertGreaterEqual(len(data.get("evals", [])), 3)

    def test_readme_and_adrs_exist(self):
        with open(self.readme_file, "r", encoding="utf-8") as f:
            content = f.read()
        for token in ["ADR-0001", "ADR-0002", "ADR-0003", "ADR-0004", "Changelog"]:
            self.assertIn(token, content)

    def test_source_normalizer_dynamic(self):
        self.assertEqual(normalize_source("Example_Weekly_issue_12.md"), "Example Weekly")
        self.assertEqual(normalize_source("Sample_Digest_2026_09_01.md"), "Sample Digest")
        self.assertEqual(
            normalize_source("", "[Issue](https://www.example.com/post/1)"),
            "example.com",
        )

    def test_veto_category_extractor(self):
        self.assertEqual(
            extract_veto_category("VETO (Hard-veto: Paper reading tasks)"),
            "Paper reading tasks",
        )
        self.assertEqual(
            extract_veto_category("Below threshold (2 < 4) (A:1 P:0 G:1)"),
            "Below threshold",
        )

    def test_analyze_subscriptions_on_isolated_data_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            for day in ("01", "02", "03"):
                d = root / "reports" / f"Newsletter_2026_09_{day}"
                d.mkdir(parents=True)
                (d / f"Example_Digest_issue_{day}.md").write_text("# Report", encoding="utf-8")
                (d / f"Sample_Weekly_issue_{day}.md").write_text("# Report", encoding="utf-8")

            (root / "data" / "suggestions_reviewed.md").write_text(
                "### 2026-09-02 | Newsletter | [Example Digest Issue](https://example.com/1)\n"
                "- 🏷️ 技術 | 📊 5/6 (A:2 P:2 G:1)\n"
                "- **Feedback**: ✅ Accept\n"
                "- **Comment**: Great actionable tip\n"
                "- [完整報告](reports/Newsletter_2026_09_02/Example_Digest_issue_02.md)\n",
                encoding="utf-8",
            )
            (root / "data" / "suggestions_filtered.md").write_text(
                "### 2026-09-03 | Newsletter | [Sample Weekly](https://example.com/2)\n"
                "- 🏷️ 技術 | 📊 VETO (Hard-veto: Paper reading tasks)\n"
                "- [完整報告](reports/Newsletter_2026_09_03/Sample_Weekly_issue_03.md)\n",
                encoding="utf-8",
            )
            (root / "data" / "suggestions_pending.md").write_text("# Pending\n", encoding="utf-8")

            data = analyze_subscriptions(
                workspace_dir=str(root),
                days=30,
                start_date="2026-08-15",
                end_date="2026-09-10",
            )
            self.assertEqual(data["total_newsletters_evaluated"], 2)
            self.assertEqual(data["total_reports"], 6)
            sources = {s["source"]: s for s in data["subscriptions"]}
            self.assertIn("Example Digest", sources)
            self.assertIn("Sample Weekly", sources)
            self.assertEqual(sources["Example Digest"]["triage"], "Keep")
            table = format_markdown_table(data)
            self.assertIn("| Source | Triage |", table)
            self.assertIn("Sample Weekly", table)


if __name__ == "__main__":
    unittest.main()
