from __future__ import annotations

import html
import json
from pathlib import Path


def write_report(
    summary: dict[str, object],
    output: Path,
    title: str,
    model_pattern: str,
) -> None:
    """Write a self-contained offline comparison report containing aggregates only."""

    payload = json.dumps(summary, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    document = (
        _HTML.replace("__TITLE__", html.escape(title))
        .replace("__MODEL_PATTERN__", html.escape(model_pattern))
        .replace("__DATA__", payload)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")


_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <meta name="description" content="Local LM Studio and llama.cpp throughput comparison generated from aggregate timing data.">
  <style>
    :root {
      color-scheme: light;
      --paper: oklch(96% 0.025 82);
      --sheet: oklch(99% 0.012 82);
      --ink: oklch(23% 0.035 48);
      --muted: oklch(48% 0.028 53);
      --faint: oklch(70% 0.022 67);
      --rule: oklch(82% 0.028 72);
      --accent: oklch(50% 0.15 38);
      --focus: oklch(48% 0.14 245);
      --shadow: 0 1.2rem 3.5rem color-mix(in oklch, var(--ink) 8%, transparent);
      font-family: "Avenir Next", Avenir, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
      font-synthesis: none;
    }
    * { box-sizing: border-box; }
    html { min-width: 20rem; }
    body { margin: 0; min-height: 100vh; font-variant-numeric: tabular-nums; }
    button, input { font: inherit; }
    button:focus-visible, input:focus-visible {
      outline: 0.16rem solid var(--focus);
      outline-offset: 0.16rem;
    }
    .page {
      width: min(92rem, 100%);
      margin-inline: auto;
      padding: clamp(1.25rem, 4vw, 4rem);
    }
    .masthead {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(18rem, 0.75fr);
      gap: clamp(2rem, 8vw, 8rem);
      align-items: end;
      padding: clamp(3rem, 8vw, 7rem) 0 clamp(2rem, 5vw, 4rem);
      border-bottom: 0.16rem solid var(--ink);
    }
    .eyebrow {
      margin: 0 0 0.8rem;
      color: var(--accent);
      font-size: 0.74rem;
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
    }
    h1, h2 { font-family: Georgia, "Times New Roman", serif; text-wrap: balance; }
    h1 {
      margin: 0;
      max-width: 12ch;
      font-size: clamp(3.3rem, 8vw, 7.7rem);
      line-height: 0.86;
      letter-spacing: -0.06em;
    }
    .lede {
      max-width: 34rem;
      margin: 0;
      color: var(--muted);
      font: clamp(1.05rem, 1.8vw, 1.35rem)/1.55 Georgia, "Times New Roman", serif;
    }
    .report-meta {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      margin: 0;
      border-bottom: 0.0625rem solid var(--ink);
    }
    .report-meta div { padding: 1rem 1rem 1rem 0; }
    .report-meta div + div { border-left: 0.0625rem solid var(--rule); padding-left: 1rem; }
    .report-meta dt {
      color: var(--muted);
      font-size: 0.68rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .report-meta dd { margin: 0.3rem 0 0; font-size: clamp(1rem, 2vw, 1.45rem); font-weight: 750; }
    .source-controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1.5rem;
      padding: clamp(2rem, 4vw, 3.5rem) 0 1rem;
      border-bottom: 0.0625rem solid var(--ink);
    }
    .source-controls h2 { margin: 0; font-size: clamp(1.45rem, 2.5vw, 2.1rem); }
    .source-controls p { margin: 0.25rem 0 0; color: var(--muted); font-size: 0.82rem; }
    .source-picker { display: flex; flex-wrap: wrap; justify-content: end; gap: 0.6rem; }
    .source-picker label {
      display: inline-flex;
      align-items: center;
      gap: 0.55rem;
      min-height: 2.6rem;
      border: 0.0625rem solid var(--ink);
      padding: 0.55rem 0.8rem;
      background: var(--sheet);
      cursor: pointer;
    }
    .source-picker label:has(input:not(:checked)) { color: var(--faint); border-color: var(--rule); }
    .source-picker input { accent-color: var(--ink); }
    .source-swatch { width: 1.25rem; height: 0.2rem; background: var(--series-color); }
    .summary-table { width: 100%; border-collapse: collapse; margin: 0 0 clamp(3rem, 6vw, 6rem); }
    .summary-table th, .summary-table td {
      border-bottom: 0.0625rem solid var(--rule);
      padding: 0.9rem 0.75rem;
      text-align: right;
    }
    .summary-table th:first-child, .summary-table td:first-child { padding-left: 0; text-align: left; }
    .summary-table th {
      color: var(--muted);
      font-size: 0.68rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .summary-table td { font-weight: 700; }
    .summary-table td small { color: var(--muted); font-weight: 500; }
    .source-name { display: inline-flex; align-items: center; gap: 0.65rem; }
    .source-name::before { width: 1.5rem; height: 0.22rem; background: var(--series-color); content: ""; }
    .workload-estimator {
      margin: 0 0 clamp(3.5rem, 8vw, 7rem);
      border-block: 0.16rem solid var(--ink);
      padding: clamp(1.5rem, 4vw, 3rem) 0;
    }
    .workload-heading {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 2rem;
      align-items: end;
    }
    .workload-heading h2 { margin: 0; font-size: clamp(2rem, 4vw, 3.8rem); letter-spacing: -0.035em; }
    .workload-heading p { max-width: 52rem; margin: 0.45rem 0 0; color: var(--muted); }
    .workload-picker { display: flex; flex-wrap: wrap; justify-content: end; border: 0.0625rem solid var(--ink); }
    .workload-picker button {
      min-height: 2.7rem;
      border: 0;
      background: transparent;
      padding: 0.55rem 0.85rem;
      cursor: pointer;
    }
    .workload-picker button + button { border-left: 0.0625rem solid var(--ink); }
    .workload-picker button[aria-pressed="true"] { background: var(--ink); color: var(--sheet); }
    .workload-verdict {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(15rem, 0.75fr);
      gap: clamp(2rem, 6vw, 7rem);
      align-items: end;
      padding: clamp(2rem, 5vw, 4.5rem) 0;
    }
    .workload-verdict strong {
      display: block;
      max-width: 17ch;
      font: 700 clamp(2rem, 5vw, 5rem)/0.95 Georgia, "Times New Roman", serif;
      letter-spacing: -0.045em;
    }
    .workload-verdict p { max-width: 34rem; margin: 0; color: var(--muted); font-size: 1rem; line-height: 1.65; }
    .duration-chart { display: grid; gap: 1.2rem; }
    .duration-row { display: grid; grid-template-columns: minmax(12rem, 0.32fr) minmax(18rem, 1fr) auto; gap: 1rem; align-items: center; }
    .duration-label strong, .duration-label small { display: block; }
    .duration-label small { color: var(--muted); font-size: 0.72rem; }
    .duration-track { display: flex; height: 2.25rem; background: color-mix(in oklch, var(--rule) 45%, transparent); }
    .duration-segment { min-width: 0.12rem; transform-origin: left; }
    .duration-segment.prefill { background: var(--accent); }
    .duration-segment.decode { background: oklch(42% 0.1 250); }
    .duration-time { min-width: 7rem; text-align: right; font: 700 1.15rem Georgia, "Times New Roman", serif; }
    .duration-legend { display: flex; justify-content: end; gap: 1rem; color: var(--muted); font-size: 0.72rem; }
    .duration-legend span { display: inline-flex; align-items: center; gap: 0.35rem; }
    .duration-legend i { width: 0.9rem; height: 0.2rem; background: var(--accent); }
    .duration-legend span:last-child i { background: oklch(42% 0.1 250); }
    .phase-comparison { width: 100%; border-collapse: collapse; margin-top: 2rem; }
    .phase-comparison th, .phase-comparison td { border-top: 0.0625rem solid var(--rule); padding: 0.8rem 0.7rem; text-align: right; }
    .phase-comparison th:first-child, .phase-comparison td:first-child { padding-left: 0; text-align: left; }
    .phase-comparison th { color: var(--muted); font-size: 0.67rem; letter-spacing: 0.06em; text-transform: uppercase; }
    .phase-comparison td { font-size: 0.86rem; font-weight: 700; }
    .estimation-note { max-width: 78rem; margin: 1rem 0 0; color: var(--muted); font-size: 0.75rem; line-height: 1.55; }
    .chart-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: clamp(3rem, 6vw, 6rem) clamp(1.5rem, 3vw, 3rem);
    }
    .chart-panel { min-width: 0; }
    .chart-panel:last-child { grid-column: 1 / -1; }
    .chart-heading { min-height: 5.4rem; border-top: 0.0625rem solid var(--rule); padding-top: 0.8rem; }
    .chart-heading h2 { margin: 0; font-size: clamp(1.4rem, 2.5vw, 2rem); }
    .chart-heading p { max-width: 48rem; margin: 0.3rem 0 0; color: var(--muted); font-size: 0.84rem; }
    .chart-frame {
      min-height: 25rem;
      border: 0.0625rem solid var(--rule);
      background-color: var(--sheet);
      background-image:
        linear-gradient(to right, color-mix(in oklch, var(--rule) 18%, transparent) 1px, transparent 1px),
        linear-gradient(to bottom, color-mix(in oklch, var(--rule) 18%, transparent) 1px, transparent 1px);
      background-size: 2rem 2rem;
      box-shadow: var(--shadow);
    }
    .chart-frame svg { display: block; width: 100%; height: auto; min-height: 25rem; }
    .chart-frame text { fill: var(--muted); font: 0.72rem "Avenir Next", Avenir, sans-serif; }
    .chart-frame .axis { stroke: var(--ink); stroke-width: 1.1; }
    .chart-frame .gridline { stroke: var(--rule); stroke-width: 0.8; }
    .chart-frame .series-line { fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
    .chart-frame .whisker { stroke-width: 1.5; }
    .chart-frame .point { stroke: var(--sheet); stroke-width: 2.5; }
    .empty-chart { display: grid; min-height: 25rem; place-items: center; color: var(--muted); }
    .method-note {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 1rem 2rem;
      margin-top: clamp(3rem, 7vw, 7rem);
      border-top: 0.16rem solid var(--ink);
      padding-top: 1rem;
      color: var(--muted);
      font-size: 0.78rem;
      line-height: 1.6;
    }
    .method-note strong { color: var(--ink); }
    .method-note p { max-width: 80ch; margin: 0; }
    .method-note code { color: var(--ink); }
    @media (max-width: 62rem) {
      .chart-grid { grid-template-columns: 1fr; }
      .chart-panel:last-child { grid-column: auto; }
    }
    @media (max-width: 44rem) {
      .page { padding-inline: max(0.9rem, env(safe-area-inset-left)); }
      .masthead { grid-template-columns: 1fr; gap: 1.5rem; }
      .report-meta { grid-template-columns: 1fr; }
      .report-meta div + div { border-top: 0.0625rem solid var(--rule); border-left: 0; padding-left: 0; }
      .source-controls { align-items: start; flex-direction: column; }
      .source-picker { justify-content: start; }
      .summary-table { display: block; overflow-x: auto; }
      .workload-heading, .workload-verdict { grid-template-columns: 1fr; }
      .workload-picker { justify-self: start; }
      .duration-row { grid-template-columns: 1fr auto; }
      .duration-track { grid-column: 1 / -1; grid-row: 2; }
      .phase-comparison { display: block; overflow-x: auto; }
      .chart-heading { min-height: 0; padding-bottom: 0.8rem; }
      .chart-frame, .chart-frame svg { min-height: 21rem; }
      .method-note { grid-template-columns: 1fr; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { scroll-behavior: auto !important; }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <div>
        <p class="eyebrow">Local inference field test</p>
        <h1>Runtime showdown</h1>
      </div>
      <p class="lede">LM Studio and standalone llama.cpp measured on equal statistical ground: medians by active context, with the middle 50% left visible.</p>
    </header>

    <dl class="report-meta">
      <div><dt>Runtimes</dt><dd id="runtimeCount">0</dd></div>
      <div><dt>Completed requests</dt><dd id="requestCount">0</dd></div>
      <div><dt>Model filter</dt><dd><code>__MODEL_PATTERN__</code></dd></div>
    </dl>

    <section class="source-controls" aria-labelledby="sourceTitle">
      <div>
        <h2 id="sourceTitle">Evidence on the charts</h2>
        <p>Toggle a runtime without changing the underlying aggregate.</p>
      </div>
      <div class="source-picker" id="sourcePicker"></div>
    </section>

    <table class="summary-table">
      <thead>
        <tr>
          <th>Runtime</th>
          <th>Requests</th>
          <th>Median prefill</th>
          <th>Median decode</th>
          <th>Maximum context</th>
        </tr>
      </thead>
      <tbody id="summaryRows"></tbody>
    </table>

    <section class="workload-estimator" aria-labelledby="workloadTitle">
      <div class="workload-heading">
        <div>
          <p class="eyebrow">Same tokens, another engine</p>
          <h2 id="workloadTitle">Replay the workload</h2>
          <p>Estimate how long one runtime would take to process the other runtime’s observed prefill and decode work.</p>
        </div>
        <div class="workload-picker" id="workloadPicker" role="group" aria-label="Workload to replay"></div>
      </div>
      <div class="workload-verdict">
        <strong id="workloadVerdict">Select a workload comparison.</strong>
        <p id="workloadExplanation"></p>
      </div>
      <div class="duration-chart" id="durationChart" aria-label="Estimated workload duration comparison"></div>
      <div class="duration-legend"><span><i></i>Prefill</span><span><i></i>Decode</span></div>
      <table class="phase-comparison">
        <thead>
          <tr>
            <th>Phase</th>
            <th>Token workload</th>
            <th id="sourceTimeHeading">Measured source</th>
            <th id="targetTimeHeading">Estimated target</th>
            <th>Target pace</th>
            <th>Coverage</th>
          </tr>
        </thead>
        <tbody id="phaseComparisonRows"></tbody>
      </table>
      <p class="estimation-note">Estimate method: each source request uses the target runtime’s median throughput from the same active-context band. Requests are omitted only when the target has no evidence in that band; coverage reports the included share. Times represent prompt evaluation plus decode compute, not queueing, model load, or application overhead.</p>
    </section>

    <section class="chart-grid" aria-label="Runtime comparison charts">
      <article class="chart-panel">
        <div class="chart-heading">
          <h2>Prefill by active context</h2>
          <p>Only requests meeting the configured evaluated-token floor contribute.</p>
        </div>
        <div class="chart-frame" id="contextPrefillChart"></div>
      </article>
      <article class="chart-panel">
        <div class="chart-heading">
          <h2>Decode by active context</h2>
          <p>Short outputs are excluded so setup overhead does not dominate decode rate.</p>
        </div>
        <div class="chart-frame" id="contextDecodeChart"></div>
      </article>
      <article class="chart-panel">
        <div class="chart-heading">
          <h2>Prefill by evaluated prompt size</h2>
          <p>Separates batching efficiency from the cost of attending over retained context.</p>
        </div>
        <div class="chart-frame" id="promptPrefillChart"></div>
      </article>
    </section>

    <footer class="method-note">
      <strong>Method</strong>
      <p>Generated locally from completed timing records. The report contains aggregates only—no prompts, responses, raw log lines, source paths, or model files. Lines show medians; whiskers show the 25th–75th percentile range.</p>
    </footer>
  </main>

  <script>
    const reportData = __DATA__;
    const seriesColors = ["#b74228", "#254b76", "#2f766f", "#9b6b00", "#8f3f65", "#684f8e"];
    const svgNamespace = "http://www.w3.org/2000/svg";
    const visibleSeriesIdentifiers = new Set(reportData.series.map((series) => series.id));
    let selectedWorkloadComparisonIndex = 0;

    function formatNumber(value, digits = 1) {
      if (value == null || !Number.isFinite(Number(value))) return "—";
      return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
    }

    function formatDuration(seconds) {
      if (seconds == null || !Number.isFinite(Number(seconds))) return "—";
      const totalSeconds = Number(seconds);
      if (totalSeconds < 60) return `${formatNumber(totalSeconds)} sec`;
      if (totalSeconds < 3600) return `${formatNumber(totalSeconds / 60)} min`;
      if (totalSeconds < 86400) return `${formatNumber(totalSeconds / 3600, 2)} hr`;
      return `${formatNumber(totalSeconds / 86400, 2)} days`;
    }

    function formatPace(targetSpeedRatio) {
      if (targetSpeedRatio == null || !Number.isFinite(Number(targetSpeedRatio))) return "—";
      if (targetSpeedRatio >= 1) return `${formatNumber(targetSpeedRatio, 2)}× faster`;
      return `${formatNumber(1 / targetSpeedRatio, 2)}× slower`;
    }

    function createSvgElement(name, attributes = {}, text = "") {
      const element = document.createElementNS(svgNamespace, name);
      for (const [attribute, value] of Object.entries(attributes)) {
        element.setAttribute(attribute, value);
      }
      if (text) element.textContent = text;
      return element;
    }

    function createSummaryValueCell(value, unit = "") {
      const cell = document.createElement("td");
      cell.append(document.createTextNode(value));
      if (unit) {
        const suffix = document.createElement("small");
        suffix.textContent = ` ${unit}`;
        cell.append(suffix);
      }
      return cell;
    }

    function renderSummary() {
      document.getElementById("runtimeCount").textContent = reportData.series.length.toLocaleString();
      document.getElementById("requestCount").textContent = reportData.series
        .reduce((total, series) => total + series.record_count, 0)
        .toLocaleString();

      const sourcePicker = document.getElementById("sourcePicker");
      const summaryRows = document.getElementById("summaryRows");
      sourcePicker.replaceChildren();
      summaryRows.replaceChildren();

      reportData.series.forEach((series, index) => {
        const color = seriesColors[index % seriesColors.length];
        const label = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = visibleSeriesIdentifiers.has(series.id);
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) visibleSeriesIdentifiers.add(series.id);
          else visibleSeriesIdentifiers.delete(series.id);
          drawCharts();
        });
        const swatch = document.createElement("span");
        swatch.className = "source-swatch";
        swatch.style.setProperty("--series-color", color);
        const name = document.createElement("span");
        name.textContent = series.label;
        label.append(checkbox, swatch, name);
        sourcePicker.append(label);

        const row = document.createElement("tr");
        row.dataset.seriesIdentifier = series.id;
        const sourceCell = document.createElement("td");
        const sourceName = document.createElement("span");
        sourceName.className = "source-name";
        sourceName.style.setProperty("--series-color", color);
        sourceName.textContent = series.label;
        sourceCell.append(sourceName);
        row.append(
          sourceCell,
          createSummaryValueCell(series.record_count.toLocaleString()),
          createSummaryValueCell(formatNumber(series.substantial_prefill.median), "tok/s"),
          createSummaryValueCell(formatNumber(series.decode.median), "tok/s"),
          createSummaryValueCell(formatNumber(series.context_max, 0), "tokens"),
        );
        summaryRows.append(row);
      });
    }

    function createDurationRow(label, qualifier, prefillSeconds, decodeSeconds, maximumSeconds) {
      const row = document.createElement("div");
      row.className = "duration-row";
      const labelContainer = document.createElement("div");
      labelContainer.className = "duration-label";
      const name = document.createElement("strong");
      name.textContent = label;
      const detail = document.createElement("small");
      detail.textContent = qualifier;
      labelContainer.append(name, detail);

      const track = document.createElement("div");
      track.className = "duration-track";
      const prefill = document.createElement("span");
      prefill.className = "duration-segment prefill";
      prefill.style.width = `${prefillSeconds / maximumSeconds * 100}%`;
      prefill.title = `Prefill: ${formatDuration(prefillSeconds)}`;
      const decode = document.createElement("span");
      decode.className = "duration-segment decode";
      decode.style.width = `${decodeSeconds / maximumSeconds * 100}%`;
      decode.title = `Decode: ${formatDuration(decodeSeconds)}`;
      track.append(prefill, decode);

      const duration = document.createElement("div");
      duration.className = "duration-time";
      duration.textContent = formatDuration(prefillSeconds + decodeSeconds);
      row.append(labelContainer, track, duration);
      return row;
    }

    function createPhaseComparisonRow(label, metric) {
      const row = document.createElement("tr");
      const values = [
        label,
        `${formatNumber(metric.tokens, 0)} tokens · ${metric.request_count.toLocaleString()} requests`,
        formatDuration(metric.source_seconds),
        formatDuration(metric.target_seconds),
        formatPace(metric.target_speed_ratio),
        metric.coverage_fraction == null ? "—" : `${formatNumber(metric.coverage_fraction * 100)}%`,
      ];
      values.forEach((value, index) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        if (index === 0) {
          const strong = document.createElement("strong");
          strong.textContent = value;
          cell.replaceChildren(strong);
        }
        row.append(cell);
      });
      return row;
    }

    function renderWorkloadComparison() {
      const comparisons = reportData.workload_comparisons || [];
      const picker = document.getElementById("workloadPicker");
      picker.replaceChildren();
      if (!comparisons.length) {
        document.getElementById("workloadVerdict").textContent = "Add two runtimes to estimate replay time.";
        document.getElementById("workloadExplanation").textContent = "";
        return;
      }

      comparisons.forEach((comparison, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.setAttribute("aria-pressed", String(index === selectedWorkloadComparisonIndex));
        button.textContent = `${comparison.source_label} workload`;
        button.addEventListener("click", () => {
          selectedWorkloadComparisonIndex = index;
          renderWorkloadComparison();
        });
        picker.append(button);
      });

      const comparison = comparisons[selectedWorkloadComparisonIndex];
      const targetPace = formatPace(comparison.total.target_speed_ratio);
      document.getElementById("workloadVerdict").textContent =
        `${comparison.target_label} is estimated ${targetPace}`;
      document.getElementById("workloadExplanation").textContent =
        `${comparison.source_label} processed the matched work in ${formatDuration(comparison.total.source_seconds)}. At ${comparison.target_label} rates from the same context bands, it would take about ${formatDuration(comparison.total.target_seconds)}.`;
      document.getElementById("sourceTimeHeading").textContent =
        `${comparison.source_label} measured`;
      document.getElementById("targetTimeHeading").textContent =
        `${comparison.target_label} estimated`;

      const maximumSeconds = Math.max(
        comparison.total.source_seconds,
        comparison.total.target_seconds,
        1,
      );
      const durationChart = document.getElementById("durationChart");
      durationChart.replaceChildren(
        createDurationRow(
          comparison.source_label,
          "Measured workload",
          comparison.prefill.source_seconds,
          comparison.decode.source_seconds,
          maximumSeconds,
        ),
        createDurationRow(
          comparison.target_label,
          "Estimated replay",
          comparison.prefill.target_seconds,
          comparison.decode.target_seconds,
          maximumSeconds,
        ),
      );

      const phaseComparisonRows = document.getElementById("phaseComparisonRows");
      phaseComparisonRows.replaceChildren(
        createPhaseComparisonRow("Prefill", comparison.prefill),
        createPhaseComparisonRow("Decode", comparison.decode),
      );
    }

    function drawComparisonChart(elementId, summaryKey) {
      const host = document.getElementById(elementId);
      const visibleSeries = reportData.series.filter(
        (series) => visibleSeriesIdentifiers.has(series.id),
      );
      host.replaceChildren();
      if (!visibleSeries.length) {
        const emptyState = document.createElement("div");
        emptyState.className = "empty-chart";
        emptyState.textContent = "Select a runtime to draw this chart.";
        host.append(emptyState);
        return;
      }

      const categories = visibleSeries[0][summaryKey].map((item) => item.label);
      const summaries = visibleSeries.flatMap((series) => series[summaryKey]);
      const maximumValue = Math.max(
        1,
        ...summaries.flatMap((item) => [
          item.summary.q3 || 0,
          item.summary.maximum || 0,
        ]),
      );
      const width = 820;
      const height = 410;
      const margin = { top: 28, right: 26, bottom: 58, left: 72 };
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      const x = (index) => (
        margin.left
        + (categories.length === 1 ? innerWidth / 2 : index / (categories.length - 1) * innerWidth)
      );
      const y = (value) => margin.top + innerHeight - value / maximumValue * innerHeight;
      const svg = createSvgElement("svg", {
        viewBox: `0 0 ${width} ${height}`,
        role: "img",
        "aria-label": "Median throughput comparison with interquartile whiskers",
      });

      for (let index = 0; index <= 5; index += 1) {
        const value = maximumValue * index / 5;
        const verticalPosition = y(value);
        svg.append(createSvgElement("line", {
          class: "gridline",
          x1: margin.left,
          x2: width - margin.right,
          y1: verticalPosition,
          y2: verticalPosition,
        }));
        svg.append(createSvgElement("text", {
          x: margin.left - 10,
          y: verticalPosition + 4,
          "text-anchor": "end",
        }, formatNumber(value)));
      }

      svg.append(createSvgElement("line", {
        class: "axis",
        x1: margin.left,
        x2: width - margin.right,
        y1: margin.top + innerHeight,
        y2: margin.top + innerHeight,
      }));

      categories.forEach((category, index) => {
        svg.append(createSvgElement("text", {
          x: x(index),
          y: height - 26,
          "text-anchor": "middle",
        }, category));
      });

      visibleSeries.forEach((series) => {
        const sourceIndex = reportData.series.findIndex(
          (candidate) => candidate.id === series.id,
        );
        const color = seriesColors[sourceIndex % seriesColors.length];
        const points = series[summaryKey]
          .map((item, index) => ({ index, item }))
          .filter(({ item }) => item.summary.median != null);
        if (!points.length) return;

        const pathData = points.map(({ index, item }, pointIndex) => (
          `${pointIndex ? "L" : "M"} ${x(index)} ${y(item.summary.median)}`
        )).join(" ");
        svg.append(createSvgElement("path", {
          class: "series-line",
          d: pathData,
          stroke: color,
        }));

        points.forEach(({ index, item }) => {
          const horizontalPosition = x(index);
          const lowerPosition = y(item.summary.q1 ?? item.summary.median);
          const upperPosition = y(item.summary.q3 ?? item.summary.median);
          const whisker = createSvgElement("line", {
            class: "whisker",
            x1: horizontalPosition,
            x2: horizontalPosition,
            y1: lowerPosition,
            y2: upperPosition,
            stroke: color,
          });
          const point = createSvgElement("circle", {
            class: "point",
            cx: horizontalPosition,
            cy: y(item.summary.median),
            r: 5,
            fill: color,
          });
          point.append(createSvgElement(
            "title",
            {},
            `${series.label} · ${item.label}: ${formatNumber(item.summary.median)} tok/s · middle 50% ${formatNumber(item.summary.q1)}–${formatNumber(item.summary.q3)} · ${item.summary.count} requests`,
          ));
          svg.append(whisker, point);
        });
      });

      svg.append(createSvgElement("text", {
        x: 18,
        y: margin.top + innerHeight / 2,
        transform: `rotate(-90 18 ${margin.top + innerHeight / 2})`,
        "text-anchor": "middle",
      }, "Tokens per second"));
      host.append(svg);
    }

    function drawCharts() {
      for (const row of document.querySelectorAll("[data-series-identifier]")) {
        row.hidden = !visibleSeriesIdentifiers.has(row.dataset.seriesIdentifier);
      }
      drawComparisonChart("contextPrefillChart", "prefill_by_context");
      drawComparisonChart("contextDecodeChart", "decode_by_context");
      drawComparisonChart("promptPrefillChart", "prefill_by_prompt_tokens");
    }

    renderSummary();
    renderWorkloadComparison();
    drawCharts();
  </script>
</body>
</html>
'''
