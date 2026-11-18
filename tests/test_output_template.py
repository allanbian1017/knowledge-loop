import os
import unittest

class TestContentSummaryTemplate(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_template_path = os.path.join(
            self.base_dir,
            ".agents/skills/content-summary/references/output_template.md"
        )
        self.summarise_path = os.path.join(
            self.base_dir,
            ".agents/skills/content-summary/references/summarise.md"
        )

    def test_output_template_reading_decision_before_tldr(self):
        with open(self.output_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        reading_decision_idx = content.find("## ⭐ Reading Decision")
        tldr_idx = content.find("## 📝 TL;DR")
        core_thesis_idx = content.find("## 🎯 Core Thesis")
        reasoning_map_idx = content.find("## 🗺️ Reasoning Map")

        self.assertNotEqual(reading_decision_idx, -1, "Reading Decision header missing")
        self.assertNotEqual(tldr_idx, -1, "TL;DR header missing")
        self.assertNotEqual(core_thesis_idx, -1, "Core Thesis header missing")
        self.assertNotEqual(reasoning_map_idx, -1, "Reasoning Map header missing")

        # Assert Reading Decision comes BEFORE TL;DR
        self.assertLess(
            reading_decision_idx,
            tldr_idx,
            "Reading Decision must come before TL;DR for fast triage"
        )

        # Assert TL;DR comes BEFORE Core Thesis
        self.assertLess(
            tldr_idx,
            core_thesis_idx,
            "TL;DR must come before Core Thesis"
        )

        # Assert Core Thesis comes BEFORE Reasoning Map
        self.assertLess(
            core_thesis_idx,
            reasoning_map_idx,
            "Core Thesis must come before Reasoning Map"
        )

    def test_summarise_reference_contains_two_step_cot(self):
        with open(self.summarise_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(
            "Internal Reasoning Order vs Visual Output Order",
            content,
            "summarise.md must explain Two-Step CoT reasoning"
        )

if __name__ == "__main__":
    unittest.main()
