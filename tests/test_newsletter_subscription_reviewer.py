#!/usr/bin/env python3
import json
import os
import sys
import unittest
import tempfile
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.validate_skill import validate_skill_file

import importlib.util

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
        self.script_file = os.path.join(self.skill_dir, "scripts/analyze_subscriptions.py")

    def test_skill_frontmatter_validation(self):
        """Verify YAML frontmatter syntax and required fields."""
        is_valid = validate_skill_file(self.skill_md)
        self.assertTrue(is_valid, "SKILL.md must pass frontmatter validation")

    def test_skill_lean_spine_budget(self):
        """Verify SKILL.md adheres to the Lean Spine line count budget (<200 lines)."""
        with open(self.skill_md, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertLess(
            len(lines),
            200,
            f"SKILL.md should be under 200 lines for Lean Spine architecture, got {len(lines)}"
        )

    def test_reference_files_exist_and_non_empty(self):
        """Verify all reference files exist and contain required content."""
        required_refs = ["triage_criteria.md", "review_template.md"]
        for ref_name in required_refs:
            ref_path = os.path.join(self.refs_dir, ref_name)
            self.assertTrue(os.path.exists(ref_path), f"Reference file {ref_name} must exist")
            with open(ref_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertGreater(len(content.strip().splitlines()), 20, f"{ref_name} must have substantial content (>20 lines)")

    def test_triage_criteria_content(self):
        """Verify triage_criteria.md documents all 4 categories and metrics."""
        ref_path = os.path.join(self.refs_dir, "triage_criteria.md")
        with open(ref_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Keep", content)
        self.assertIn("Unsubscribe", content)
        self.assertIn("Adjust", content)
        self.assertIn("Watch", content)
        self.assertIn("Acceptance Rate", content)
        self.assertIn("Overall Yield", content)

    def test_evals_json_structure(self):
        """Verify evals.json is valid JSON and contains test cases."""
        self.assertTrue(os.path.exists(self.evals_file), "evals.json must exist")
        with open(self.evals_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("skill_name"), "review-newsletter-subscriptions")
        evals = data.get("evals", [])
        self.assertGreaterEqual(len(evals), 3, "Must have at least 3 evaluation test cases")
        for item in evals:
            self.assertIn("id", item)
            self.assertIn("prompt", item)
            self.assertIn("expected_output", item)

    def test_readme_and_adrs_exist(self):
        """Verify README.md exists and documents all 4 Architecture Decision Records (ADRs)."""
        self.assertTrue(os.path.exists(self.readme_file), "README.md must exist in skill directory")
        with open(self.readme_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ADR-0001", content)
        self.assertIn("ADR-0002", content)
        self.assertIn("ADR-0003", content)
        self.assertIn("ADR-0004", content)
        self.assertIn("Changelog", content)

    def test_source_normalizer(self):
        """Verify source normalizer accurately standardizes various names."""
        self.assertEqual(normalize_source("The_Rundown_AI_abc.md"), "The Rundown AI")
        self.assertEqual(normalize_source("ByteByteGo_EP224.md"), "ByteByteGo (Alex Xu)")
        self.assertEqual(normalize_source("朱騏_知識複利.md"), "朱騏 (Henry Chu)")
        self.assertEqual(normalize_source("Superhuman_AI_news.md"), "Superhuman")
        self.assertEqual(normalize_source("Hugging_Face_papers.md"), "Hugging Face Daily Papers")
        self.assertEqual(normalize_source("The_Code_issue.md"), "The Code")

    def test_veto_category_extractor(self):
        """Verify veto category extraction from score status."""
        self.assertEqual(
            extract_veto_category("VETO (Hard-veto: Paper reading tasks / 論文研讀)"),
            "Paper reading tasks / 論文研讀"
        )
        self.assertEqual(
            extract_veto_category("Below threshold (2 < 4) (A:1 P:0 G:1)"),
            "Below threshold"
        )

    def test_analyze_subscriptions_execution(self):
        """Verify analyze_subscriptions computes correct telemetry on workspace data."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / "reports" / "Newsletter_2026_09_01"
            reports.mkdir(parents=True)
            (reports / "The_Code_fixture.md").write_text("# Fixture\n\nSynthetic report.\n")
            (root / "data").mkdir()
            data = analyze_subscriptions(
                workspace_dir=directory,
                days=30,
                start_date="2026-08-09",
                end_date="2026-09-08"
            )

        self.assertIn("subscriptions", data)
        self.assertGreater(data["total_newsletters_evaluated"], 0)
        self.assertGreater(data["total_reports"], 0)

        # Check subscription schema
        for sub in data["subscriptions"]:
            self.assertIn("source", sub)
            self.assertIn("triage", sub)
            self.assertIn(sub["triage"], ["Keep", "Unsubscribe", "Adjust", "Watch"])
            self.assertIn("reports_count", sub)
            self.assertIn("reviewed_count", sub)
            self.assertIn("accepted_count", sub)
            self.assertIn("rejected_count", sub)
            self.assertIn("filtered_count", sub)
            self.assertIn("acceptance_rate", sub)
            self.assertIn("yield_rate", sub)

        # Check markdown table formatting
        table = format_markdown_table(data)
        self.assertIn("| Source | Triage |", table)
        self.assertIn("The Code", table)

if __name__ == "__main__":
    unittest.main()
