import os
import re
import unittest

class TestSuggestionArchetypes(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ai_analysis_path = os.path.join(
            self.base_dir,
            ".agents/skills/content-summary/references/ai_analysis.md"
        )
        self.rubric_path = os.path.join(
            self.base_dir,
            ".agents/skills/rubric-grader/references/rubric.md"
        )
        self.blocklist_path = os.path.join(
            self.base_dir,
            "examples/data/rubric_blocklist.md"
        )

    def test_ai_analysis_contains_5_archetypes(self):
        with open(self.ai_analysis_path, "r", encoding="utf-8") as f:
            content = f.read()

        expected_archetypes = [
            "JIRA_BACKLOG",
            "ADR_DOC",
            "PROMPT_TEMPLATE",
            "TEST_FIXTURE",
            "TAKEAWAY_ONLY",
        ]
        for archetype in expected_archetypes:
            self.assertIn(
                archetype,
                content,
                f"ai_analysis.md must explicitly define archetype {archetype}"
            )

        self.assertIn(
            "Forced Prompt Wrapping",
            content,
            "ai_analysis.md must contain explicit negative rule against Forced Prompt Wrapping"
        )

        self.assertIn(
            "suggestions_filtered.md",
            content,
            "ai_analysis.md must still route failing actionable suggestions to suggestions_filtered.md"
        )
        self.assertIn(
            "Discard. Do not stage a suggestion JSON",
            content,
            "ai_analysis.md must discard TAKEAWAY_ONLY without writing to pending or filtered"
        )

    def test_rubric_archetype_fit_and_forced_prompt_penalty(self):
        with open(self.rubric_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(
            "Archetype-Content Fit",
            content,
            "rubric.md must evaluate Archetype-Content Fit under Preference Alignment"
        )
        self.assertIn(
            "Forced Prompt Wrapping",
            content,
            "rubric.md must dock points for Forced Prompt Wrapping under Preference Alignment"
        )

        for archetype in ["JIRA_BACKLOG", "ADR_DOC", "PROMPT_TEMPLATE", "TEST_FIXTURE"]:
            self.assertIn(
                archetype,
                content,
                f"rubric.md must validate {archetype} under Actionability"
            )

    def test_rubric_blocklist_contains_forced_prompt_wrapping_veto(self):
        with open(self.blocklist_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(
            "Forced Prompt Wrapping",
            content,
            "rubric_blocklist.md must contain Forced Prompt Wrapping as a hard veto"
        )

    def test_simulation_takeaway_only_is_discarded(self):
        """Simulate suggestion triage logic to verify TAKEAWAY_ONLY is written nowhere."""
        def triage_suggestion(archetype: str, text: str):
            if archetype == "TAKEAWAY_ONLY" or text.startswith("[TAKEAWAY_ONLY]"):
                return None
            return "data/suggestions_pending.md"

        self.assertIsNone(
            triage_suggestion("TAKEAWAY_ONLY", "[TAKEAWAY_ONLY] 本期核心觀點為模型對齊趨勢...")
        )
        self.assertEqual(
            triage_suggestion("JIRA_BACKLOG", "[JIRA_BACKLOG] 整理為 Jira 待辦項目提案（目標 Epic: PROJ-3）..."),
            "data/suggestions_pending.md"
        )
        self.assertEqual(
            triage_suggestion("PROMPT_TEMPLATE", "[PROMPT_TEMPLATE] 整理為 1 個面試模擬提示詞..."),
            "data/suggestions_pending.md"
        )

    def test_simulation_forced_prompt_wrapping_vetoed(self):
        """Simulate blocklist detection for forced prompt wrapping on non-interactive news/architecture."""
        def check_forced_prompt_veto(topic_category: str, archetype: str, text: str) -> bool:
            with open(self.blocklist_path, "r", encoding="utf-8") as f:
                blocklist = f.read()
            if "Forced Prompt Wrapping" not in blocklist:
                return False

            non_interactive_categories = ["新聞", "政治", "架構", "宏觀趨勢"]
            if archetype == "PROMPT_TEMPLATE" and topic_category in non_interactive_categories:
                return True
            if "data/prompts/" in text and topic_category in ["新聞", "政治"]:
                return True
            return False

        # Macro political news wrapped in a prompt must be vetoed
        self.assertTrue(
            check_forced_prompt_veto(
                "新聞",
                "PROMPT_TEMPLATE",
                "整理為 1 個提示詞模板存入 data/prompts/australian_pm_ai_delay.md"
            )
        )
        # Legitimate interview tool must pass
        self.assertFalse(
            check_forced_prompt_veto(
                "職涯",
                "PROMPT_TEMPLATE",
                "整理為 1 個結構化面試評分提示詞存入 data/prompts/interview_coach.md"
            )
        )

    def test_ai_analysis_defines_archetype_priority(self):
        with open(self.ai_analysis_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Archetype Priority", content)
        section = content.split("Archetype Priority", 1)[1].split("## Fields required", 1)[0]
        top = section.index("JIRA_BACKLOG")
        self.assertLess(top, section.index("`ADR_DOC`"))
        self.assertLess(section.index("`ADR_DOC`"), section.index("`TAKEAWAY_ONLY`"))
        for a in ["PROMPT_TEMPLATE", "TEST_FIXTURE"]:
            self.assertLess(section.index(a), section.index("`ADR_DOC`"))

    def test_rubric_demotes_adr_doc(self):
        with open(self.rubric_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("(PROJ-1..PROJ-7) or `ADR_DOC`", content)
        self.assertIn("lower-priority fallback", content)

    def test_simulation_single_suggestion_priority(self):
        priority = ["JIRA_BACKLOG", "PROMPT_TEMPLATE", "TEST_FIXTURE", "ADR_DOC", "TAKEAWAY_ONLY"]
        top_tier = {"JIRA_BACKLOG", "PROMPT_TEMPLATE", "TEST_FIXTURE"}

        def select(cands, best_top=None):
            tops = [c for c in cands if c in top_tier]
            if tops:
                return best_top if best_top in tops else tops[0]
            for a in ["ADR_DOC", "TAKEAWAY_ONLY"]:
                if a in cands:
                    return a
            return None

        self.assertEqual(select({"ADR_DOC", "JIRA_BACKLOG"}), "JIRA_BACKLOG")
        self.assertEqual(select({"ADR_DOC", "PROMPT_TEMPLATE", "TAKEAWAY_ONLY"}), "PROMPT_TEMPLATE")
        self.assertEqual(select({"ADR_DOC", "TAKEAWAY_ONLY"}), "ADR_DOC")
        self.assertEqual(select({"TAKEAWAY_ONLY"}), "TAKEAWAY_ONLY")

if __name__ == "__main__":
    unittest.main()
