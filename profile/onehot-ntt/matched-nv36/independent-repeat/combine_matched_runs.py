from __future__ import annotations
import csv
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INITIAL = ROOT.parent / "nv36"
BATCHES = (("initial_batch", INITIAL), ("independent_repeat", ROOT))
METRICS = ("setup_s", "commit_s", "prove_s", "total_s")

rows: list[dict[str, object]] = []
for batch_name, directory in BATCHES:
    with (directory / "matched-runs.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            row["batch"] = batch_name
            row["pair"] = int(row["pair"])
            rows.append(row)

with (ROOT / "matched-combined.csv").open("w", newline="", encoding="utf-8") as stream:
    fields = ["batch", "label", "pair", "variant", "elapsed_s", "setup_s", "commit_s", "prove_s", "verify_multi_s", "verify_single_s", "proof_bytes", "verification_modes", "peak_rss_bytes", "exit_code"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

results: dict[str, dict[str, object]] = {}
for metric in METRICS:
    values = []
    for batch_name, _ in BATCHES:
        indexed = {(str(r["variant"]), int(r["pair"])): r for r in rows if r["batch"] == batch_name}
        for pair in range(1, 13):
            candidate = indexed[("candidate_ntt", pair)]
            baseline = indexed[("base_accum", pair)]
            if metric == "total_s":
                left = sum(float(candidate[k]) for k in ("setup_s", "commit_s", "prove_s"))
                right = sum(float(baseline[k]) for k in ("setup_s", "commit_s", "prove_s"))
            else:
                left, right = float(candidate[metric]), float(baseline[metric])
            values.append(100.0 * (left / right - 1.0))
    seed = 20261050
    rng = random.Random(seed)
    bootstrap = sorted(statistics.median(rng.choice(values) for _ in values) for _ in range(50_000))
    results[metric] = {
        "paired_median_delta_percent": statistics.median(values),
        "paired_bootstrap_95_percent_interval": [bootstrap[1249], bootstrap[48_749]],
        "faster_pairs": sum(value < 0 for value in values),
        "paired_count": len(values),
        "bootstrap_resamples": 50_000,
        "bootstrap_seed": seed,
    }

summary = {
    "case": "onehot_fp128:36:1:direct:standard",
    "baseline_source": "cc3ea3690d5a17123c2309c5ec84c41341005e96",
    "candidate_source": "a2b5ba81d8acfb554c4a75b8ea0a7a312d218480",
    "batches": {
        name: {
            "pairs": 12,
            "csv": "../nv36/matched-runs.csv" if directory != ROOT else "matched-runs.csv",
            "note": "The initial batch had a brief low-priority research-script overlap at an unknown arm." if name == "initial_batch" else "Separate repeat with balanced randomized order and a passing three-sample quiet-host gate.",
        }
        for name, directory in BATCHES
    },
    "pooled_pair_count": 24,
    "delta_convention": "negative means candidate used less time than base",
    "paired_results": results,
}
(ROOT / "matched-combined-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2, sort_keys=True))
