import re
from typing import Any, Dict, List
import unittest


REQUIRED_FIELDS = [
    "date",
    "source_type",
    "title",
    "source_url",
    "category",
    "suggestion",
    "report_path",
]

VALID_SOURCE_TYPES = {"Newsletter", "Threads", "Website", "YouTube"}


def validate_suggestion_payload(payload: Dict[str, Any]) -> List[str]:
    """Validates a staged suggestion JSON payload produced by subagents.
    
    Returns a list of validation error messages. An empty list indicates a valid payload.
    """
    errors: List[str] = []

    if not isinstance(payload, dict):
        return ["Payload must be a dictionary."]

    # 1. Required fields presence and non-empty check
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: '{field}'")
        else:
            val = payload[field]
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"Field '{field}' must not be empty.")

    if errors:
        return errors

    # 2. Date format check (YYYY-MM-DD)
    date_val = str(payload.get("date", "")).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_val):
        errors.append(f"Invalid date format '{date_val}', expected 'YYYY-MM-DD'.")

    # 3. Source type check
    source_type = payload.get("source_type", "")
    if source_type not in VALID_SOURCE_TYPES:
        errors.append(
            f"Invalid source_type '{source_type}', expected one of {sorted(VALID_SOURCE_TYPES)}."
        )

    # 4. URL format check
    source_url = str(payload.get("source_url", "")).strip()
    if not (source_url.startswith("http://") or source_url.startswith("https://") or source_url.startswith("mailto:")):
        errors.append(f"Invalid source_url '{source_url}', must start with http://, https://, or mailto:.")

    # 5. Report path check
    report_path = str(payload.get("report_path", "")).strip()
    if not report_path.endswith(".md"):
        errors.append(f"Field 'report_path' must point to a Markdown file ending in .md, got '{report_path}'.")

    return errors


class TestSuggestionPayloadSchema(unittest.TestCase):
    def test_valid_newsletter_payload(self):
        payload = {
            "date": "2026-09-30",
            "source_type": "Newsletter",
            "title": "Why has Shopify dropped React Native?",
            "source_url": "https://newsletter.pragmaticengineer.com/p/shopify-native-mobile",
            "category": "技術",
            "suggestion": "本週花 20 分鐘在 tests/ 新增無頭測試腳本...",
            "report_path": "reports/Newsletter_2026_09_30/The_Pragmatic_Engineer_Why_has_Shopify_dropped_React_Native.md",
        }
        errors = validate_suggestion_payload(payload)
        self.assertEqual(errors, [], f"Expected valid payload, got errors: {errors}")

    def test_valid_website_payload(self):
        payload = {
            "date": "2026-09-30",
            "source_type": "Website",
            "title": "How to Survive a Live Machine Learning Coding Interview",
            "source_url": "https://amanxai.com/2026/09/29/how-to-survive-a-live-machine-learning-coding-interview/",
            "category": "職涯",
            "suggestion": "本週安排 25 分鐘針對 AI/ML Live Coding 面試建立檢查卡...",
            "report_path": "reports/Website_2026_09_30/amanxai.com_how_to_survive_a_live_machine_learning_coding_interview.md",
        }
        errors = validate_suggestion_payload(payload)
        self.assertEqual(errors, [], f"Expected valid payload, got errors: {errors}")

    def test_missing_required_field(self):
        payload = {
            "date": "2026-09-30",
            "source_type": "Newsletter",
            "title": "Sample Title",
            # missing source_url
            "category": "技術",
            "suggestion": "Some suggestion",
            "report_path": "reports/test.md",
        }
        errors = validate_suggestion_payload(payload)
        self.assertTrue(any("Missing required field: 'source_url'" in e for e in errors))

    def test_empty_field(self):
        payload = {
            "date": "2026-09-30",
            "source_type": "Newsletter",
            "title": "",
            "source_url": "https://example.com",
            "category": "技術",
            "suggestion": "   ",
            "report_path": "reports/test.md",
        }
        errors = validate_suggestion_payload(payload)
        self.assertTrue(any("Field 'title' must not be empty" in e for e in errors))
        self.assertTrue(any("Field 'suggestion' must not be empty" in e for e in errors))

    def test_invalid_date(self):
        payload = {
            "date": "2026/09/30",
            "source_type": "Newsletter",
            "title": "Title",
            "source_url": "https://example.com",
            "category": "技術",
            "suggestion": "Suggestion",
            "report_path": "reports/test.md",
        }
        errors = validate_suggestion_payload(payload)
        self.assertTrue(any("Invalid date format" in e for e in errors))

    def test_invalid_source_type(self):
        payload = {
            "date": "2026-09-30",
            "source_type": "Podcast",
            "title": "Title",
            "source_url": "https://example.com",
            "category": "技術",
            "suggestion": "Suggestion",
            "report_path": "reports/test.md",
        }
        errors = validate_suggestion_payload(payload)
        self.assertTrue(any("Invalid source_type 'Podcast'" in e for e in errors))

    def test_invalid_report_path(self):
        payload = {
            "date": "2026-09-30",
            "source_type": "YouTube",
            "title": "Title",
            "source_url": "https://youtube.com/watch?v=123",
            "category": "技術",
            "suggestion": "Suggestion",
            "report_path": "reports/video.txt",
        }
        errors = validate_suggestion_payload(payload)
        self.assertTrue(any("must point to a Markdown file ending in .md" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
