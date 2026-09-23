from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .model import TimingRecord


LOAD_RE = re.compile(r"load_model: loading model '([^']+)'")
PROMPT_RE = re.compile(
    r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]"
    r".*?id\s+(?P<slot>\d+)\s+\|\s+task\s+(?P<task>\d+)\s+\|"
    r"\s+prompt eval time\s*=\s*[\d.]+\s+ms\s+/\s+"
    r"(?P<tokens>\d+)\s+tokens.*?,\s+(?P<speed>[\d.]+)\s+tokens per second\)"
)
DECODE_RE = re.compile(
    r"id\s+(?P<slot>\d+)\s+\|\s+task\s+(?P<task>\d+)\s+\|"
    r"\s+eval time\s*=\s*[\d.]+\s+ms\s+/\s+"
    r"(?P<tokens>\d+)\s+tokens.*?,\s+(?P<speed>[\d.]+)\s+tokens per second\)"
)
RELEASE_RE = re.compile(
    r"slot\s+release:\s+id\s+(?P<slot>\d+)\s+\|\s+task\s+(?P<task>\d+)"
    r"\s+\|\s+stop processing:\s+n_tokens\s*=\s*(?P<tokens>\d+)"
)


@dataclass(slots=True)
class _PromptTiming:
    timestamp: datetime
    model_path: str
    slot_id: int
    task_id: int
    tokens: int
    speed: float


@dataclass(slots=True)
class _PairedTiming:
    prompt: _PromptTiming
    decoded_tokens: int
    decode_speed: float


class LMStudioLogParser:
    """Stateful parser for one ordered LM Studio log stream."""

    def __init__(self, model_pattern: str) -> None:
        self.model_pattern = re.compile(model_pattern, re.IGNORECASE)
        self.active_model: str | None = None
        self._prompt: dict[tuple[int, int], _PromptTiming] = {}
        self._paired: dict[tuple[int, int], _PairedTiming] = {}

    def reset(self) -> None:
        self.active_model = None
        self._prompt.clear()
        self._paired.clear()

    def parse_lines(self, lines: Iterable[str]) -> Iterator[TimingRecord]:
        for line in lines:
            load_match = LOAD_RE.search(line)
            if load_match:
                self.active_model = load_match.group(1)
                self._prompt.clear()
                self._paired.clear()
                continue

            if not self.active_model or not self.model_pattern.search(self.active_model):
                continue

            prompt_match = PROMPT_RE.search(line)
            if prompt_match:
                slot_id = int(prompt_match.group("slot"))
                task_id = int(prompt_match.group("task"))
                self._prompt[(slot_id, task_id)] = _PromptTiming(
                    timestamp=datetime.strptime(
                        prompt_match.group("timestamp"), "%Y-%m-%d %H:%M:%S"
                    ),
                    model_path=self.active_model,
                    slot_id=slot_id,
                    task_id=task_id,
                    tokens=int(prompt_match.group("tokens")),
                    speed=float(prompt_match.group("speed")),
                )
                continue

            decode_match = DECODE_RE.search(line)
            if decode_match:
                key = (int(decode_match.group("slot")), int(decode_match.group("task")))
                prompt = self._prompt.pop(key, None)
                if prompt is not None:
                    self._paired[key] = _PairedTiming(
                        prompt=prompt,
                        decoded_tokens=int(decode_match.group("tokens")),
                        decode_speed=float(decode_match.group("speed")),
                    )
                continue

            release_match = RELEASE_RE.search(line)
            if release_match:
                key = (int(release_match.group("slot")), int(release_match.group("task")))
                paired = self._paired.pop(key, None)
                if paired is None:
                    continue
                final_tokens = int(release_match.group("tokens"))
                context_tokens = final_tokens - paired.decoded_tokens
                if context_tokens <= 0:
                    continue
                yield TimingRecord(
                    timestamp=paired.prompt.timestamp,
                    model_path=paired.prompt.model_path,
                    slot_id=paired.prompt.slot_id,
                    task_id=paired.prompt.task_id,
                    evaluated_prompt_tokens=paired.prompt.tokens,
                    prefill_tokens_per_second=paired.prompt.speed,
                    decoded_tokens=paired.decoded_tokens,
                    decode_tokens_per_second=paired.decode_speed,
                    final_slot_tokens=final_tokens,
                    context_tokens=context_tokens,
                )


def discover_log_files(paths: Sequence[Path]) -> list[list[Path]]:
    """Return sorted file groups; parser state is retained within each directory."""

    groups: list[list[Path]] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved.is_file():
            groups.append([resolved])
        elif resolved.is_dir():
            files = sorted(p for p in resolved.rglob("*.log") if p.is_file())
            if files:
                groups.append(files)
    return groups


def default_log_paths() -> list[Path]:
    root = Path.home() / ".lmstudio"
    candidates = [root / "server-logs"]
    candidates.extend(sorted((root / "apps").glob("*/server-logs")))
    return [path for path in candidates if path.exists()]


def parse_logs(paths: Sequence[Path], model_pattern: str) -> list[TimingRecord]:
    records: list[TimingRecord] = []
    for group in discover_log_files(paths):
        parser = LMStudioLogParser(model_pattern)
        for file_path in group:
            with file_path.open("r", encoding="utf-8", errors="replace") as handle:
                records.extend(parser.parse_lines(handle))
    records.sort(key=lambda record: record.timestamp)
    return records
