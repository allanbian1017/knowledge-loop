import json
import os
import sys
import unittest

# Add root directory to path to import scripts.validate_skill
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.validate_skill import validate_skill_file

class TestAgentRulesReviewerSkill(unittest.TestCase):
    def setUp(self):
        self.skill_dir = os.path.join(BASE_DIR, ".agents/skills/agent-rules-reviewer")
        self.skill_md = os.path.join(self.skill_dir, "SKILL.md")
        self.refs_dir = os.path.join(self.skill_dir, "references")
        self.evals_file = os.path.join(self.skill_dir, "evals/evals.json")

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
        """Verify all three modular reference files exist and contain substantial content."""
        required_refs = [
            "three_tier_architecture.md",
            "audit_criteria.md",
            "review_template.md"
        ]
        for ref_name in required_refs:
            ref_path = os.path.join(self.refs_dir, ref_name)
            self.assertTrue(os.path.exists(ref_path), f"Reference file {ref_name} must exist")
            with open(ref_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertGreater(len(content.strip().splitlines()), 20, f"{ref_name} must have substantial content (>20 lines)")

    def test_three_tier_content_coverage(self):
        """Verify three_tier_architecture.md covers all 3 tiers and Attention Budget."""
        ref_path = os.path.join(self.refs_dir, "three_tier_architecture.md")
        with open(ref_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Tier 1: Always Do", content)
        self.assertIn("Tier 2: Ask First", content)
        self.assertIn("Tier 3: Never Do", content)
        self.assertIn("Attention Budget Governance", content)

    def test_audit_criteria_vectors_coverage(self):
        """Verify audit_criteria.md details all 5 audit vectors."""
        ref_path = os.path.join(self.refs_dir, "audit_criteria.md")
        with open(ref_path, "r", encoding="utf-8") as f:
            content = f.read()

        for vector_num in range(1, 6):
            self.assertIn(f"Vector {vector_num}:", content, f"Vector {vector_num} must be documented")

    def test_review_template_structure(self):
        """Verify review_template.md includes telemetry table and confirmation checkpoint."""
        ref_path = os.path.join(self.refs_dir, "review_template.md")
        with open(ref_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Attention Budget & Telemetry Summary", content)
        self.assertIn("Audit Findings by Vector", content)
        self.assertIn("Proposed 3-Tier Refactored Ruleset", content)
        self.assertIn("Confirmation Checkpoint", content)

    def test_evals_json_structure(self):
        """Verify evals.json is valid JSON and contains test cases."""
        self.assertTrue(os.path.exists(self.evals_file), "evals.json must exist")
        with open(self.evals_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("skill_name"), "agent-rules-reviewer")
        evals = data.get("evals", [])
        self.assertGreaterEqual(len(evals), 3, "Must have at least 3 evaluation test cases")
        for item in evals:
            self.assertIn("id", item)
            self.assertIn("prompt", item)
            self.assertIn("expected_output", item)

    def test_readme_and_adrs_exist(self):
        """Verify README.md exists and documents all 4 Architecture Decision Records (ADRs)."""
        readme_path = os.path.join(self.skill_dir, "README.md")
        self.assertTrue(os.path.exists(readme_path), "README.md must exist in skill directory")
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ADR-001:", content)
        self.assertIn("ADR-002:", content)
        self.assertIn("ADR-003:", content)
        self.assertIn("ADR-004:", content)

if __name__ == "__main__":
    unittest.main()
