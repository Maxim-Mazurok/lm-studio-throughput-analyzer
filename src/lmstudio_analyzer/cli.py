from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .dataset import read_sanitized_dataset, write_sanitized_dataset
from .parser import default_log_paths, parse_logs
from .report import write_report
from .stats import analyze


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lmstudio-throughput",
        description=(
            "Analyze LM Studio server timing logs and generate a self-contained "
            "HTML throughput report. Raw log contents are never embedded."
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
        default="LM Studio Throughput Report",
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.decode_min_tokens < 1 or args.context_prefill_min_tokens < 1:
        raise SystemExit("Token thresholds must be positive integers.")

    if args.input_json and args.paths:
        raise SystemExit("Do not combine --input-json with log paths.")

    if args.input_json:
        records = read_sanitized_dataset(args.input_json.expanduser().resolve())
    else:
        paths = args.paths or default_log_paths()
        if not paths:
            print(
                "No default LM Studio log directories were found. Pass one or more paths.",
                file=sys.stderr,
            )
            return 2
        records = parse_logs(paths, args.model)
    if not records:
        print(
            f"No completed timing records matched model expression {args.model!r}.",
            file=sys.stderr,
        )
        return 1

    summary = analyze(
        records,
        decode_min_tokens=args.decode_min_tokens,
        context_prefill_min_tokens=args.context_prefill_min_tokens,
    )
    output = args.output.expanduser().resolve()
    write_report(summary, output, args.title, args.model)

    if args.export_sanitized:
        sanitized_output = args.export_sanitized.expanduser().resolve()
        write_sanitized_dataset(records, sanitized_output)
        print(f"Wrote sanitized telemetry: {sanitized_output}")

    if args.json_summary:
        json_output = args.json_summary.expanduser().resolve()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Wrote aggregate JSON: {json_output}")

    print(f"Matched {len(records):,} completed requests.")
    print(f"Wrote report: {output}")
    if args.open:
        webbrowser.open(output.as_uri())
    return 0
