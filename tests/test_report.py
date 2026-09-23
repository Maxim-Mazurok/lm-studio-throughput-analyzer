from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lmstudio_analyzer.report import write_report


class ReportTests(TestCase):
    def test_report_contains_only_supplied_aggregates(self) -> None:
        summary = {
            "series": [
                {
                    "id": "lm-studio",
                    "label": "LM Studio",
                    "runtime": "lm-studio",
                    "record_count": 1,
                    "context_max": 4096,
                    "decode": {"median": 20},
                    "substantial_prefill": {"median": 200},
                    "prefill_by_prompt_tokens": [],
                    "prefill_by_context": [],
                    "decode_by_context": [],
                },
                {
                    "id": "llama-server",
                    "label": "llama.cpp",
                    "runtime": "llama.cpp",
                    "record_count": 1,
                    "context_max": 4096,
                    "decode": {"median": 40},
                    "substantial_prefill": {"median": 400},
                    "prefill_by_prompt_tokens": [],
                    "prefill_by_context": [],
                    "decode_by_context": [],
                },
            ],
            "workload_comparisons": [
                {
                    "source_id": "lm-studio",
                    "source_label": "LM Studio",
                    "target_id": "llama-server",
                    "target_label": "llama.cpp",
                    "prefill": {
                        "tokens": 2048,
                        "request_count": 1,
                        "eligible_request_count": 1,
                        "coverage_fraction": 1,
                        "source_seconds": 10.24,
                        "target_seconds": 5.12,
                        "target_speed_ratio": 2,
                    },
                    "decode": {
                        "tokens": 128,
                        "request_count": 1,
                        "eligible_request_count": 1,
                        "coverage_fraction": 1,
                        "source_seconds": 6.4,
                        "target_seconds": 3.2,
                        "target_speed_ratio": 2,
                    },
                    "total": {
                        "source_seconds": 16.64,
                        "target_seconds": 8.32,
                        "target_speed_ratio": 2,
                    },
                }
            ],
            "filters": {},
        }
        with TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            write_report(summary, output, "Synthetic report", "SyntheticModel")
            content = output.read_text(encoding="utf-8")
            self.assertIn("Synthetic report", content)
            self.assertIn("LM Studio", content)
            self.assertIn("llama.cpp", content)
            self.assertIn("Replay the workload", content)
            self.assertIn("Generated locally", content)
            self.assertNotIn("C:\\Users", content)
            self.assertNotIn("prompt content", content)
