import os
import unittest


class TestContentSummaryTemplate(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_template_path = os.path.join(
            self.base_dir,
            ".agents/skills/content-summary/references/output_template.md",
        )
        self.summarise_path = os.path.join(
            self.base_dir,
            ".agents/skills/content-summary/references/summarise.md",
        )
        self.distiller_template_path = os.path.join(
            self.base_dir,
            ".agents/skills/daily-distiller/assets/output_template.md",
        )

    def test_v5_answer_first_pyramid_order(self):
        with open(self.output_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        conclusion_idx = content.find("🎯 一句話結論")
        rating_idx = content.find("- **⭐ 推薦度**")
        action_idx = content.find("- **⚡ 下一步**")
        source_idx = content.find("- **🔗 來源**")
        takeaways_idx = content.find("## 💡 核心重點")
        table_idx = content.find("## 📊 一張表看懂")
        deep_dive_idx = content.find("## 🔍 深入解構")
        relevance_idx = content.find("🧭 <b>對我的意義與來源資訊</b>")

        for name, idx in [
            ("1-Sentence Conclusion", conclusion_idx),
            ("Rating Bullet", rating_idx),
            ("Next Action Bullet", action_idx),
            ("Source Bullet", source_idx),
            ("Core Takeaways", takeaways_idx),
            ("At-a-Glance Table", table_idx),
            ("Deep Breakdown Accordions", deep_dive_idx),
            ("Relevance & Metadata Footer", relevance_idx),
        ]:
            self.assertNotEqual(idx, -1, f"{name} missing in output_template.md")

        self.assertLess(conclusion_idx, rating_idx, "1-sentence conclusion must come first")
        self.assertLess(rating_idx, action_idx, "Rating bullet must precede Next Action bullet")
        self.assertLess(action_idx, source_idx, "Next Action bullet must precede Source bullet")
        self.assertLess(source_idx, takeaways_idx, "Top vertical bullets must precede Core Takeaways")
        self.assertLess(takeaways_idx, table_idx, "Core takeaways must precede comparison table")
        self.assertLess(table_idx, deep_dive_idx, "Comparison table must precede collapsible deep dive")
        self.assertLess(deep_dive_idx, relevance_idx, "Deep dive accordions must precede footer")

    def test_per_topic_details_have_gfm_blank_lines(self):
        with open(self.output_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("</summary>\n\n", content, "GFM requires blank line after </summary>")
        self.assertIn("\n\n</details>", content, "GFM requires blank line before </details>")

    def test_summarise_enforces_inverted_pyramid_and_just_in_time_context(self):
        with open(self.summarise_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(
            "Internal Reasoning Order vs Visual Output Order",
            content,
            "summarise.md must explain Two-Step CoT reasoning",
        )
        self.assertIn(
            "Answer First, Explain Later",
            content,
            "summarise.md must enforce Answer-First Pyramid principle",
        )
        self.assertIn(
            "Zone A+: Just-in-Time Context Bridge",
            content,
            "summarise.md must define Just-in-Time inline analogies",
        )
        self.assertIn(
            "≤5 items",
            content,
            "summarise.md must enforce ≤5 item working-memory cap",
        )

    def test_daily_distiller_uses_answer_first_pyramid(self):
        with open(self.distiller_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("🎯 今日一句話結論", content)
        self.assertIn("## 💡 今日核心重點", content)
        self.assertIn("## 📊 跨來源主題速覽", content)
        self.assertIn("<details>", content)


if __name__ == "__main__":
    unittest.main()
