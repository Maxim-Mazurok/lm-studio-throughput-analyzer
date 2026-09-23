import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lmstudio_analyzer.dataset import (
    read_sanitized_dataset,
    read_sanitized_dataset_with_metadata,
    write_sanitized_dataset,
)
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
            write_sanitized_dataset(
                [record],
                output,
                runtime="llama.cpp",
                label="llama.cpp test",
            )
            content = output.read_text(encoding="utf-8")
            restored = read_sanitized_dataset(output)
            _records, metadata = read_sanitized_dataset_with_metadata(output)

        self.assertNotIn("C:\\private", content)
        self.assertNotIn("03:04:05", content)
        self.assertNotIn('"slot_id"', content)
        self.assertNotIn('"task_id"', content)
        self.assertEqual(restored[0].model_path, "Synthetic-Model.gguf")
        self.assertEqual(restored[0].context_tokens, 10000)
        self.assertEqual(restored[0].timestamp, datetime(2026, 1, 2))
        self.assertEqual(metadata["runtime"], "llama.cpp")
        self.assertEqual(metadata["label"], "llama.cpp test")

    def test_public_datasets_contain_only_approved_telemetry(self) -> None:
        data_directory = Path(__file__).resolve().parents[1] / "data"
        allowed_top_level_fields = {
            "schema_version",
            "description",
            "privacy",
            "models",
            "records",
            "runtime",
            "label",
        }
        allowed_record_fields = {
            "date",
            "model",
            "evaluated_prompt_tokens",
            "prefill_tokens_per_second",
            "decoded_tokens",
            "decode_tokens_per_second",
            "final_slot_tokens",
            "context_tokens",
        }
        numeric_record_fields = allowed_record_fields - {"date", "model"}

        for dataset_path in data_directory.glob("*.json"):
            with self.subTest(dataset=dataset_path.name):
                payload = json.loads(dataset_path.read_text(encoding="utf-8"))
                self.assertLessEqual(set(payload), allowed_top_level_fields)
                self.assertEqual(payload["schema_version"], 1)
                self.assertIsInstance(payload["models"], list)
                self.assertIsInstance(payload["records"], list)
                for model in payload["models"]:
                    self.assertIsInstance(model, str)
                    self.assertEqual(Path(model).name, model)
                    self.assertTrue(model.lower().endswith(".gguf"))
                for record in payload["records"]:
                    self.assertEqual(set(record), allowed_record_fields)
                    self.assertRegex(record["date"], r"^\d{4}-\d{2}-\d{2}$")
                    self.assertIn(record["model"], payload["models"])
                    for numeric_record_field in numeric_record_fields:
                        self.assertIsInstance(
                            record[numeric_record_field],
                            (int, float),
                        )
