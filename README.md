# LM Studio Throughput Analyzer

Generate a private, self-contained HTML dashboard from LM Studio server logs.
The report charts:

- prefill throughput by newly evaluated prompt size;
- decode throughput by day;
- prefill throughput by active context size; and
- decode throughput by active context size.

The analyzer is dependency-free and runs entirely on your computer.

## Privacy

The repository contains **no LM Studio logs or extracted benchmark data**.

The analyzer reads only timing and slot-accounting lines. Generated reports contain
aggregated counts and percentiles—not prompts, responses, raw log lines, source file
paths, or model files. Common log, model, and report filenames are excluded in
`.gitignore`.

No network requests are made by the analyzer or generated report.

## Install

Requires Python 3.10 or later.

```powershell
git clone https://github.com/Maxim-Mazurok/lm-studio-throughput-analyzer.git
cd lm-studio-throughput-analyzer
python -m pip install -e .
```

## Run

LM Studio's normal log locations are discovered automatically:

```powershell
lmstudio-throughput --model "Qwen3\.6-35B-A3B" --open
```

Or pass specific files or directories:

```powershell
lmstudio-throughput `
  "$env:USERPROFILE\.lmstudio\server-logs" `
  --model "Qwen3\.6-35B-A3B" `
  --output qwen-35b-report.html `
  --open
```

Run without installing:

```powershell
$env:PYTHONPATH = "src"
python -m lmstudio_analyzer --model "Qwen3\.6-35B-A3B" --open
```

Use `--help` to see thresholds and optional aggregate JSON output.

## How context size is reconstructed

LM Studio emits a final slot token count when a task is released. For each completed
request, the analyzer pairs:

1. `prompt eval time` — newly evaluated prompt tokens and prefill throughput;
2. `eval time` — decoded tokens and decode throughput; and
3. `slot release ... n_tokens` — final tokens retained by the slot.

The active context at decode start is reconstructed as:

```text
context tokens = final slot tokens - decoded tokens
```

This lets the report show how throughput changes as the KV-cache context grows,
including when most of the prompt is reused from cache.

## Statistical choices

- The line or bar is the median.
- The band or whisker is the 25th–75th percentile range.
- Decode summaries ignore outputs shorter than 32 tokens by default.
- Context/prefill summaries ignore prefills shorter than 128 newly evaluated tokens
  by default, reducing small-batch overhead noise.
- Percentiles use linear interpolation between adjacent observations.

Thresholds are configurable from the command line.

## Supported log format

The parser targets recent LM Studio server logs backed by llama.cpp-style timing
messages. It recognizes loaded model paths and pairs timing records by slot and task.
Files in each supplied directory are processed in sorted order so model state can
continue across rotated logs.

If LM Studio changes its debug log wording, open an issue with a short **redacted,
synthetic** example rather than uploading personal logs.

## Development

```powershell
python -m unittest discover -s tests -v
```

The tests use fabricated timing lines only.

## License

MIT
