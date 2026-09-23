from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from math import ceil, floor
from typing import Callable, Iterable, Sequence

from .model import TimingRecord


@dataclass(frozen=True, slots=True)
class Summary:
    count: int
    minimum: float | None
    p10: float | None
    q1: float | None
    median: float | None
    q3: float | None
    p90: float | None
    maximum: float | None
    mean: float | None

    def to_dict(self) -> dict[str, int | float | None]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Bin:
    label: str
    minimum: int
    maximum: int | None

    def contains(self, value: int) -> bool:
        return value >= self.minimum and (self.maximum is None or value <= self.maximum)


PROMPT_BINS = (
    Bin("2–31", 2, 31),
    Bin("32–127", 32, 127),
    Bin("128–511", 128, 511),
    Bin("512–2k", 512, 2047),
    Bin("2k+", 2048, None),
)

CONTEXT_BINS = (
    Bin("0–4k", 0, 4095),
    Bin("4–8k", 4096, 8191),
    Bin("8–16k", 8192, 16383),
    Bin("16–32k", 16384, 32767),
    Bin("32–64k", 32768, 65535),
    Bin("64–96k", 65536, 98303),
    Bin("96k+", 98304, None),
)


def percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = floor(position)
    high = ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (position - low) * (ordered[high] - ordered[low])


def summarize(values: Iterable[float]) -> Summary:
    items = [float(value) for value in values]
    if not items:
        return Summary(0, None, None, None, None, None, None, None, None)
    return Summary(
        count=len(items),
        minimum=round(min(items), 2),
        p10=round(percentile(items, 0.10) or 0, 2),
        q1=round(percentile(items, 0.25) or 0, 2),
        median=round(percentile(items, 0.50) or 0, 2),
        q3=round(percentile(items, 0.75) or 0, 2),
        p90=round(percentile(items, 0.90) or 0, 2),
        maximum=round(max(items), 2),
        mean=round(sum(items) / len(items), 2),
    )


def _binned_summary(
    records: Sequence[TimingRecord],
    bins: Sequence[Bin],
    bin_value: Callable[[TimingRecord], int],
    metric_value: Callable[[TimingRecord], float],
    predicate: Callable[[TimingRecord], bool] = lambda _: True,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for item in bins:
        matching = [record for record in records if item.contains(bin_value(record))]
        eligible = [record for record in matching if predicate(record)]
        output.append(
            {
                "label": item.label,
                "total_count": len(matching),
                "summary": summarize(metric_value(record) for record in eligible).to_dict(),
            }
        )
    return output


def analyze(
    records: Sequence[TimingRecord],
    decode_min_tokens: int = 32,
    context_prefill_min_tokens: int = 128,
) -> dict[str, object]:
    valid_decode = [
        record
        for record in records
        if record.decoded_tokens >= decode_min_tokens
        and record.decode_tokens_per_second > 0
    ]
    substantial_prefill = [
        record
        for record in records
        if record.evaluated_prompt_tokens >= 512
        and record.prefill_tokens_per_second > 0
    ]
    large_prefill = [
        record
        for record in records
        if record.evaluated_prompt_tokens >= 2048
        and record.prefill_tokens_per_second > 0
    ]

    by_date: dict[str, list[TimingRecord]] = defaultdict(list)
    for record in valid_decode:
        by_date[record.timestamp.date().isoformat()].append(record)
    daily_decode = [
        {
            "date": date,
            "summary": summarize(
                record.decode_tokens_per_second for record in by_date[date]
            ).to_dict(),
        }
        for date in sorted(by_date)
    ]

    context_prefill = _binned_summary(
        records,
        CONTEXT_BINS,
        lambda record: record.context_tokens,
        lambda record: record.prefill_tokens_per_second,
        lambda record: record.evaluated_prompt_tokens >= context_prefill_min_tokens
        and record.prefill_tokens_per_second > 0,
    )
    context_decode = _binned_summary(
        records,
        CONTEXT_BINS,
        lambda record: record.context_tokens,
        lambda record: record.decode_tokens_per_second,
        lambda record: record.decoded_tokens >= decode_min_tokens
        and record.decode_tokens_per_second > 0,
    )

    return {
        "record_count": len(records),
        "date_min": records[0].timestamp.date().isoformat() if records else None,
        "date_max": records[-1].timestamp.date().isoformat() if records else None,
        "context_min": min((record.context_tokens for record in records), default=None),
        "context_max": max((record.context_tokens for record in records), default=None),
        "decode": summarize(
            record.decode_tokens_per_second for record in valid_decode
        ).to_dict(),
        "substantial_prefill": summarize(
            record.prefill_tokens_per_second for record in substantial_prefill
        ).to_dict(),
        "large_prefill": summarize(
            record.prefill_tokens_per_second for record in large_prefill
        ).to_dict(),
        "prefill_by_prompt_tokens": _binned_summary(
            records,
            PROMPT_BINS,
            lambda record: record.evaluated_prompt_tokens,
            lambda record: record.prefill_tokens_per_second,
            lambda record: record.prefill_tokens_per_second > 0,
        ),
        "daily_decode": daily_decode,
        "prefill_by_context": context_prefill,
        "decode_by_context": context_decode,
        "filters": {
            "decode_min_tokens": decode_min_tokens,
            "context_prefill_min_tokens": context_prefill_min_tokens,
        },
    }
