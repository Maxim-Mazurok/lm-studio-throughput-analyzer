from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .dataset import (
    read_sanitized_dataset,
    read_sanitized_dataset_with_metadata,
    write_sanitized_dataset,
)
from .model import TimingSeries
from .parser import default_log_paths, parse_llama_server_log, parse_logs
from .report import write_report
from .stats import analyze_comparison


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lmstudio-throughput",
        description=(
            "Compare LM Studio and standalone llama.cpp server timing logs in a "
            "self-contained HTML throughput report. Raw log contents are never embedded."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "Log file or directory. Defaults to ~/.lmstudio/server-logs and "
            "~/.lmstudio/apps/*/server-logs."
        ),
    )
    parser.add_argument(
        "--llama-log",
        action="append",
        default=[],
        type=Path,
        help=(
            "Standalone llama.cpp server log to compare with LM Studio. "
            "Repeat to add multiple captures."
        ),
    )
    parser.add_argument(
        "--llama-json",
        action="append",
        default=[],
        type=Path,
        help=(
            "Sanitized standalone llama.cpp telemetry to compare with LM Studio. "
            "Repeat to add multiple datasets."
        ),
    )
    parser.add_argument(
        "--model",
        default=r"Qwen3\.6-35B-A3B",
        help="Case-insensitive regular expression matched against loaded model paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("lmstudio-throughput-report.html"),
        help="Destination HTML report.",
    )
    parser.add_argument(
        "--json-summary",
        type=Path,
        help="Optional destination for aggregate JSON. Contains no raw log text.",
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        help="Read a sanitized telemetry dataset instead of LM Studio log files.",
    )
    parser.add_argument(
        "--export-sanitized",
        type=Path,
        help=(
            "Export record-level numeric telemetry without prompts, responses, "
            "token IDs, exact timestamps, local paths, or raw log lines."
        ),
    )
    parser.add_argument(
        "--title",
        default="LM Studio vs llama.cpp Throughput",
        help="Report title.",
    )
    parser.add_argument(
        "--decode-min-tokens",
        type=int,
        default=32,
        help="Minimum decoded tokens for decode statistics (default: 32).",
    )
    parser.add_argument(
        "--context-prefill-min-tokens",
        type=int,
        default=128,
        help="Minimum evaluated tokens for context/prefill statistics (default: 128).",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated report in the default browser.",
    )
    return parser


def main(command_line_arguments: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(command_line_arguments)
    if (
        arguments.decode_min_tokens < 1
        or arguments.context_prefill_min_tokens < 1
    ):
        raise SystemExit("Token thresholds must be positive integers.")

    if arguments.input_json and arguments.paths:
        raise SystemExit("Do not combine --input-json with log paths.")

    if arguments.input_json:
        lm_studio_records = read_sanitized_dataset(
            arguments.input_json.expanduser().resolve()
        )
    else:
        lm_studio_paths = arguments.paths or default_log_paths()
        if (
            not lm_studio_paths
            and not arguments.llama_log
            and not arguments.llama_json
        ):
            print(
                "No default LM Studio log directories were found. Pass an LM Studio "
                "path, --input-json, --llama-json, or --llama-log.",
                file=sys.stderr,
            )
            return 2
        lm_studio_records = parse_logs(lm_studio_paths, arguments.model)

    timing_series: list[TimingSeries] = []
    if lm_studio_records:
        timing_series.append(
            TimingSeries(
                identifier="lm-studio",
                label="LM Studio",
                runtime="lm-studio",
                records=lm_studio_records,
            )
        )

    llama_series_index = 0
    for llama_dataset_path in arguments.llama_json:
        llama_series_index += 1
        llama_records, metadata = read_sanitized_dataset_with_metadata(
            llama_dataset_path.expanduser().resolve()
        )
        if not llama_records:
            continue
        timing_series.append(
            TimingSeries(
                identifier=f"llama-server-{llama_series_index}",
                label=metadata.get("label", f"llama.cpp dataset {llama_series_index}"),
                runtime=metadata.get("runtime", "llama.cpp"),
                records=llama_records,
            )
        )

    for llama_log_path in arguments.llama_log:
        llama_series_index += 1
        llama_records, tensor_split = parse_llama_server_log(
            llama_log_path,
            arguments.model,
        )
        if not llama_records:
            continue
        label = (
            f"llama.cpp · tensor split {tensor_split}"
            if tensor_split
            else f"llama.cpp capture {llama_series_index}"
        )
        timing_series.append(
            TimingSeries(
                identifier=f"llama-server-{llama_series_index}",
                label=label,
                runtime="llama.cpp",
                records=llama_records,
            )
        )
    if not timing_series:
        print(
            f"No completed timing records matched model expression {arguments.model!r}.",
            file=sys.stderr,
        )
        return 1

    summary = analyze_comparison(
        timing_series,
        decode_min_tokens=arguments.decode_min_tokens,
        context_prefill_min_tokens=arguments.context_prefill_min_tokens,
    )
    output = arguments.output.expanduser().resolve()
    write_report(summary, output, arguments.title, arguments.model)

    if arguments.export_sanitized:
        if not lm_studio_records:
            raise SystemExit("No LM Studio records are available to export.")
        sanitized_output = arguments.export_sanitized.expanduser().resolve()
        write_sanitized_dataset(lm_studio_records, sanitized_output)
        print(f"Wrote sanitized telemetry: {sanitized_output}")

    if arguments.json_summary:
        json_output = arguments.json_summary.expanduser().resolve()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Wrote aggregate JSON: {json_output}")

    for series in timing_series:
        print(f"Matched {len(series.records):,} completed requests for {series.label}.")
    print(f"Wrote report: {output}")
    if arguments.open:
        webbrowser.open(output.as_uri())
    return 0
