from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lmstudio_analyzer.report import write_report


class ReportTests(TestCase):
    def test_report_contains_only_supplied_aggregates(self) -> None:
        summary = {
            "record_count": 0,
            "date_min": None,
            "date_max": None,
            "context_min": None,
            "context_max": None,
            "decode": {"count": 0, "median": None, "q1": None, "q3": None},
            "substantial_prefill": {"count": 0, "median": None, "q1": None, "q3": None},
            "large_prefill": {"count": 0, "median": None, "q1": None, "q3": None},
            "prefill_by_prompt_tokens": [],
            "daily_decode": [],
            "prefill_by_context": [],
            "decode_by_context": [],
            "filters": {},
        }
        with TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            write_report(summary, output, "Synthetic report", "SyntheticModel")
            content = output.read_text(encoding="utf-8")
            self.assertIn("Synthetic report", content)
            self.assertIn("Generated locally", content)
            self.assertNotIn("C:\\Users", content)
            self.assertNotIn("prompt content", content)
