from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Sequence

from .model import TimingRecord


SCHEMA_VERSION = 1
_REQUIRED_RECORD_FIELDS = {
    "date",
    "model",
    "evaluated_prompt_tokens",
    "prefill_tokens_per_second",
    "decoded_tokens",
    "decode_tokens_per_second",
    "final_slot_tokens",
    "context_tokens",
}


def _model_filename(model_path: str) -> str:
    """Return a model filename without retaining its local directory."""

    return re.split(r"[\\/]", model_path)[-1]


def sanitized_payload(
    records: Sequence[TimingRecord],
    runtime: str | None = None,
    label: str | None = None,
) -> dict[str, object]:
    """Create content-free performance telemetry from parsed timing records."""

    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "description": "Sanitized inference performance telemetry; numeric metrics only.",
        "privacy": {
            "omitted": [
                "prompts",
                "responses",
                "token_ids",
                "raw_log_lines",
                "exact_timestamps",
                "local_paths",
                "slot_ids",
                "task_ids",
            ],
            "retained": [
                "model_filename",
                "calendar_date",
                "numeric_token_counts",
                "prefill_speed",
                "decode_speed",
                "context_size",
            ],
        },
        "models": sorted({_model_filename(record.model_path) for record in records}),
        "records": [
            {
                "date": record.timestamp.date().isoformat(),
                "model": _model_filename(record.model_path),
                "evaluated_prompt_tokens": record.evaluated_prompt_tokens,
                "prefill_tokens_per_second": record.prefill_tokens_per_second,
                "decoded_tokens": record.decoded_tokens,
                "decode_tokens_per_second": record.decode_tokens_per_second,
                "final_slot_tokens": record.final_slot_tokens,
                "context_tokens": record.context_tokens,
            }
            for record in records
        ],
    }
    if runtime:
        payload["runtime"] = runtime
    if label:
        payload["label"] = label
    return payload


def write_sanitized_dataset(
    records: Sequence[TimingRecord],
    output: Path,
    runtime: str | None = None,
    label: str | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            sanitized_payload(records, runtime=runtime, label=label),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def read_sanitized_dataset_with_metadata(
    source: Path,
) -> tuple[list[TimingRecord], dict[str, str]]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported sanitized dataset schema in {source}")
    rows = payload.get("records")
    if not isinstance(rows, list):
        raise ValueError(f"Sanitized dataset has no records array: {source}")

    records: list[TimingRecord] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != _REQUIRED_RECORD_FIELDS:
            raise ValueError(f"Invalid sanitized record {index} in {source}")
        records.append(
            TimingRecord(
                timestamp=datetime.strptime(str(row["date"]), "%Y-%m-%d"),
                model_path=str(row["model"]),
                slot_id=0,
                task_id=index,
                evaluated_prompt_tokens=int(row["evaluated_prompt_tokens"]),
                prefill_tokens_per_second=float(row["prefill_tokens_per_second"]),
                decoded_tokens=int(row["decoded_tokens"]),
                decode_tokens_per_second=float(row["decode_tokens_per_second"]),
                final_slot_tokens=int(row["final_slot_tokens"]),
                context_tokens=int(row["context_tokens"]),
            )
        )
    metadata = {
        key: str(payload[key])
        for key in ("runtime", "label")
        if isinstance(payload.get(key), str) and payload[key]
    }
    return records, metadata


def read_sanitized_dataset(source: Path) -> list[TimingRecord]:
    records, _metadata = read_sanitized_dataset_with_metadata(source)
    return records
