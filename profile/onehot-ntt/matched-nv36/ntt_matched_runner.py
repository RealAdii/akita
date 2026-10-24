#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import os
import random
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, "/Volumes/DockerData/akita-ssd-worktree/scripts")
from profile_bench_report import extract_summary

COUNT = 12
THREADS = 8
ORDER_SEED = 102436
BOOTSTRAP_SEED = 20261024
VARIANTS = ("base_accum", "candidate_accum", "candidate_ntt")
BINARIES = {variant: ROOT / f"profile-{variant}" for variant in VARIANTS}
LOGS = ROOT / "logs"
PROOFS = ROOT / "proofs"


def quiet_sample() -> dict[str, float]:
    idle = 100.0 - psutil.cpu_percent(interval=1.0)
    return {
        "load_average_1_min": os.getloadavg()[0],
        "cpu_idle_percent": idle,
        "available_memory_percent": 100.0 * psutil.virtual_memory().available / psutil.virtual_memory().total,
    }


def wait_for_quiet() -> list[dict[str, float]]:
    qualified: list[dict[str, float]] = []
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        sample = quiet_sample()
        if (
            sample["load_average_1_min"] <= 6.0
            and sample["cpu_idle_percent"] >= 65.0
            and sample["available_memory_percent"] >= 40.0
        ):
            qualified.append(sample)
            if len(qualified) == 3:
                return qualified
        else:
            qualified.clear()
        time.sleep(20)
    raise TimeoutError("machine did not meet the quiet rule within 15 minutes")


def run_one(variant: str, pair: int, label: str, measured: bool) -> dict[str, object]:
    env = dict(os.environ)
    env.update({
        "AKITA_MODE": "onehot_fp128",
        "AKITA_NUM_VARS": "36",
        "AKITA_NUM_POLYS": "1",
        "AKITA_SETUP_MODE": "direct",
        "AKITA_PROFILE_TRACE": "0",
        "AKITA_PROFILE_SPAN_CLOSES": "0",
        "AKITA_PROFILE_LOG": "info",
        "AKITA_PROFILE_ANSI": "0",
        "AKITA_PROFILE_PROVE_THREADS": str(THREADS),
        "AKITA_PROFILE_VERIFY_THREADS": str(THREADS),
        "RAYON_NUM_THREADS": str(THREADS),
        "AKITA_ONEHOT_COMMIT": "ntt-exact" if variant == "candidate_ntt" else "accumulation",
        "AKITA_PROFILE_SAVE_BYTES": str(PROOFS / f"pair-{pair:02d}-{label}-{variant}"),
        "RUST_MIN_STACK": "67108864",
    })
    env.pop("AKITA_PROFILE_COMPARE_ONEHOT", None)
    env.pop("AKITA_PROFILE_COMPARE_ORDER", None)
    if variant == "candidate_ntt":
        env["AKITA_PROFILE_COMPARE_ORDER"] = "ntt-exact"
    started = time.perf_counter()
    proc = subprocess.run(
        ["/usr/bin/time", "-l", str(BINARIES[variant])],
        capture_output=True,
        text=True,
        env=env,
    )
    elapsed = time.perf_counter() - started
    log = proc.stdout + proc.stderr
    (LOGS / f"{label}-{variant}.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"{label} {variant} exited {proc.returncode}")
    result = extract_summary(log, mode="onehot_fp128", num_vars=36, num_polys=1, setup_mode="direct")
    if result.get("verification_modes") != "multi_and_single":
        raise RuntimeError(f"{label} {variant} did not pass both verifier modes")
    rss = re.search(r"(\d+)\s+maximum resident set size", log)
    row = {
        "label": label,
        "pair": pair,
        "variant": variant,
        "elapsed_s": elapsed,
        "setup_s": result["setup_s"],
        "commit_s": result["commit_s"],
        "prove_s": result["prove_total_s"],
        "verify_multi_s": result["verify_total_s"],
        "verify_single_s": result["verify_single_total_s"],
        "proof_bytes": result["proof_size_bytes"],
        "verification_modes": result["verification_modes"],
        "peak_rss_bytes": int(rss.group(1)) if rss else None,
        "exit_code": proc.returncode,
    }
    if measured:
        return row
    return row


def paired_deltas(rows: list[dict[str, object]], left: str, right: str, metric: str) -> list[float]:
    indexed = {(str(row["variant"]), int(row["pair"])): float(row[metric]) for row in rows if row["label"] == "measured"}
    return [100.0 * (indexed[(left, pair)] / indexed[(right, pair)] - 1.0) for pair in range(1, COUNT + 1)]


def bootstrap_interval(values: list[float], rng: random.Random) -> list[float]:
    bootstrap = [statistics.median(values[rng.randrange(len(values))] for _ in values) for _ in range(50_000)]
    bootstrap.sort()
    return [bootstrap[499], bootstrap[49_499]]


def main() -> None:
    LOGS.mkdir(exist_ok=True)
    PROOFS.mkdir(exist_ok=True)
    for variant, path in BINARIES.items():
        if not path.is_file():
            raise FileNotFoundError(path)
    machine = {
        "logical_cpus": psutil.cpu_count(logical=True),
        "physical_memory_bytes": psutil.virtual_memory().total,
        "baseline_source": "cc3ea3690d5a17123c2309c5ec84c41341005e96",
        "candidate_source": "a2b5ba81d8acfb554c4a75b8ea0a7a312d218480",
        "binary_sha256": {
            variant: hashlib.sha256(path.read_bytes()).hexdigest() for variant, path in BINARIES.items()
        },
        "case": "onehot_fp128:36:1:direct:standard",
        "threads": THREADS,
        "count": COUNT,
    }
    readiness = wait_for_quiet()
    rows: list[dict[str, object]] = []
    for variant in VARIANTS:
        rows.append(run_one(variant, 0, "warmup", False))
    permutations = [list(item) for item in itertools.permutations(VARIANTS)] * (COUNT // 6)
    random.Random(ORDER_SEED).shuffle(permutations)
    for pair, order in enumerate(permutations, 1):
        for variant in order:
            rows.append(run_one(variant, pair, "measured", True))
        print(f"completed pair {pair}/{COUNT}: {' > '.join(order)}", flush=True)
    csv_rows = [row for row in rows if row["label"] == "measured"]
    with (ROOT / "matched-runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    proof_sizes = {int(row["proof_bytes"]) for row in rows}
    if len(proof_sizes) != 1:
        raise RuntimeError(f"proof size changed across variants: {sorted(proof_sizes)}")
    comparisons = (
        ("candidate_accum", "base_accum"),
        ("candidate_ntt", "candidate_accum"),
        ("candidate_ntt", "base_accum"),
    )
    metrics = ("setup_s", "commit_s", "prove_s", "verify_multi_s", "verify_single_s")
    rng = random.Random(BOOTSTRAP_SEED)
    deltas: dict[str, dict[str, object]] = {}
    for faster, baseline in comparisons:
        key = f"{faster}_vs_{baseline}"
        metric_deltas = {}
        for metric in metrics:
            values = paired_deltas(rows, faster, baseline, metric)
            metric_deltas[metric] = {
                "paired_median_delta_percent": statistics.median(values),
                "paired_bootstrap_95_percent_interval": bootstrap_interval(values, rng),
                "faster_pairs": sum(value < 0 for value in values),
            }
        totals = ["setup_s", "commit_s", "prove_s"]
        total_values = []
        for pair in range(1, COUNT + 1):
            indexed = {(str(row["variant"]), int(row["pair"])): row for row in rows if row["label"] == "measured"}
            left = sum(float(indexed[(faster, pair)][metric]) for metric in totals)
            right = sum(float(indexed[(baseline, pair)][metric]) for metric in totals)
            total_values.append(100.0 * (left / right - 1.0))
        metric_deltas["setup_commit_prove_total_s"] = {
            "paired_median_delta_percent": statistics.median(total_values),
            "paired_bootstrap_95_percent_interval": bootstrap_interval(total_values, rng),
            "faster_pairs": sum(value < 0 for value in total_values),
        }
        deltas[key] = metric_deltas
    summary = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "machine": machine,
        "quiet_rule": {
            "load_average_1_min_max": 6.0,
            "cpu_idle_percent_min": 65.0,
            "available_memory_percent_min": 40.0,
            "consecutive_samples": 3,
        },
        "quiet_samples": readiness,
        "orders_per_position": {variant: {str(pos): sum(order[pos] == variant for order in permutations) for pos in range(3)} for variant in VARIANTS},
        "bootstrap_resamples": 50_000,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "proof_bytes": next(iter(proof_sizes)),
        "all_runs_passed_both_verifiers": all(row["verification_modes"] == "multi_and_single" for row in rows),
        "peak_rss_measured_for_all_runs": all(row["peak_rss_bytes"] is not None for row in rows),
        "paired_results": deltas,
    }
    (ROOT / "matched-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
