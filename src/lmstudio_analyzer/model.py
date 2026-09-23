from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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

