from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lmstudio_analyzer.parser import LMStudioLogParser, parse_logs


MATCHING_LINES = [
    "[2026-01-02 03:04:05][DEBUG] I srv load_model: loading model 'models/Qwen3.6-35B-A3B-Q4_K_M.gguf'\n",
    "[2026-01-02 03:04:08][DEBUG] I slot print_timing: id  2 | task 17 | prompt eval time = 1000.00 ms /  2048 tokens (0.49 ms per token, 2048.00 tokens per second)\n",
    "0.04.000 I slot print_timing: id  2 | task 17 |        eval time = 2000.00 ms /   100 tokens (20.00 ms per token, 50.00 tokens per second)\n",
    "[2026-01-02 03:04:11][DEBUG] I slot release: id  2 | task 17 | stop processing: n_tokens = 10100, truncated = 0\n",
]


class ParserTests(TestCase):
    def test_pairs_timing_and_reconstructs_context(self) -> None:
        parser = LMStudioLogParser(r"Qwen3\.6-35B-A3B")
        records = list(parser.parse_lines(MATCHING_LINES))

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.timestamp, datetime(2026, 1, 2, 3, 4, 8))
        self.assertEqual(record.evaluated_prompt_tokens, 2048)
        self.assertEqual(record.prefill_tokens_per_second, 2048.0)
        self.assertEqual(record.decoded_tokens, 100)
        self.assertEqual(record.decode_tokens_per_second, 50.0)
        self.assertEqual(record.final_slot_tokens, 10100)
        self.assertEqual(record.context_tokens, 10000)

    def test_nonmatching_model_is_ignored(self) -> None:
        parser = LMStudioLogParser(r"DifferentModel")
        self.assertEqual(list(parser.parse_lines(MATCHING_LINES)), [])

    def test_directory_parsing_keeps_state_across_rotated_logs(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "001.log").write_text("".join(MATCHING_LINES[:2]), encoding="utf-8")
            (root / "002.log").write_text("".join(MATCHING_LINES[2:]), encoding="utf-8")
            records = parse_logs([root], r"Qwen3\.6-35B-A3B")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].context_tokens, 10000)
