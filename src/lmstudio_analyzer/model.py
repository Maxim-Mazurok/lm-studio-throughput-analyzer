from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True, slots=True)
class TimingRecord:
    """One completed LM Studio generation with paired timing information."""

    timestamp: datetime
    model_path: str
    slot_id: int
    task_id: int
    evaluated_prompt_tokens: int
    prefill_tokens_per_second: float
    decoded_tokens: int
    decode_tokens_per_second: float
    final_slot_tokens: int
    context_tokens: int


@dataclass(frozen=True, slots=True)
class TimingSeries:
    """One named runtime's timing records for side-by-side analysis."""

    identifier: str
    label: str
    runtime: str
    records: Sequence[TimingRecord]
