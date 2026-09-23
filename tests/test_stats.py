from datetime import datetime, timedelta
from unittest import TestCase

from lmstudio_analyzer.model import TimingRecord, TimingSeries
from lmstudio_analyzer.stats import analyze, analyze_comparison, percentile, summarize


def record(index: int, context: int, prefill: float, decode: float) -> TimingRecord:
    return TimingRecord(
        timestamp=datetime(2026, 1, 1) + timedelta(days=index),
        model_path="synthetic-model.gguf",
        slot_id=0,
        task_id=index,
        evaluated_prompt_tokens=2048,
        prefill_tokens_per_second=prefill,
        decoded_tokens=128,
        decode_tokens_per_second=decode,
        final_slot_tokens=context + 128,
        context_tokens=context,
    )


class StatsTests(TestCase):
    def test_percentile_uses_linear_interpolation(self) -> None:
        self.assertEqual(percentile([0.0, 10.0], 0.25), 2.5)
        self.assertEqual(percentile([0.0, 10.0], 0.50), 5.0)

    def test_summary(self) -> None:
        result = summarize([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(result.count, 4)
        self.assertEqual(result.median, 2.5)
        self.assertEqual(result.mean, 2.5)

    def test_context_bins(self) -> None:
        result = analyze(
            [
                record(0, 3000, 200.0, 20.0),
                record(1, 12000, 180.0, 14.0),
                record(2, 70000, 110.0, 4.0),
                record(3, 110000, 90.0, 3.0),
            ]
        )
        decode_bins = {item["label"]: item for item in result["decode_by_context"]}
        self.assertEqual(decode_bins["0–4k"]["summary"]["median"], 20.0)
        self.assertEqual(decode_bins["64–96k"]["summary"]["median"], 4.0)
        self.assertEqual(decode_bins["96k+"]["summary"]["median"], 3.0)

    def test_comparison_keeps_runtime_series_separate(self) -> None:
        result = analyze_comparison(
            [
                TimingSeries(
                    identifier="lm-studio",
                    label="LM Studio",
                    runtime="lm-studio",
                    records=[record(0, 3000, 200.0, 20.0)],
                ),
                TimingSeries(
                    identifier="llama-server",
                    label="llama.cpp",
                    runtime="llama.cpp",
                    records=[record(0, 3000, 400.0, 40.0)],
                ),
            ]
        )

        self.assertEqual(len(result["series"]), 2)
        self.assertEqual(result["series"][0]["decode"]["median"], 20.0)
        self.assertEqual(result["series"][1]["decode"]["median"], 40.0)
        forward_comparison = result["workload_comparisons"][0]
        reverse_comparison = result["workload_comparisons"][1]
        self.assertEqual(forward_comparison["source_id"], "lm-studio")
        self.assertEqual(forward_comparison["target_id"], "llama-server")
        self.assertAlmostEqual(
            forward_comparison["total"]["target_speed_ratio"],
            2.0,
        )
        self.assertAlmostEqual(
            reverse_comparison["total"]["target_speed_ratio"],
            0.5,
        )
        self.assertEqual(forward_comparison["prefill"]["coverage_fraction"], 1.0)
