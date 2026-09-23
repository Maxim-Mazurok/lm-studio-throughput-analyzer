from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lmstudio_analyzer.dataset import read_sanitized_dataset, write_sanitized_dataset
from lmstudio_analyzer.model import TimingRecord


class DatasetTests(TestCase):
    def test_round_trip_omits_content_and_identifiers(self) -> None:
        record = TimingRecord(
            timestamp=datetime(2026, 1, 2, 3, 4, 5),
            model_path=r"C:\private\models\Synthetic-Model.gguf",
            slot_id=7,
            task_id=42,
            evaluated_prompt_tokens=2048,
            prefill_tokens_per_second=200.5,
            decoded_tokens=128,
            decode_tokens_per_second=18.25,
            final_slot_tokens=10128,
            context_tokens=10000,
        )
        with TemporaryDirectory() as directory:
            output = Path(directory) / "dataset.json"
            write_sanitized_dataset([record], output)
            content = output.read_text(encoding="utf-8")
            restored = read_sanitized_dataset(output)

        self.assertNotIn("C:\\private", content)
        self.assertNotIn("03:04:05", content)
        self.assertNotIn('"slot_id"', content)
        self.assertNotIn('"task_id"', content)
        self.assertEqual(restored[0].model_path, "Synthetic-Model.gguf")
        self.assertEqual(restored[0].context_tokens, 10000)
        self.assertEqual(restored[0].timestamp, datetime(2026, 1, 2))
