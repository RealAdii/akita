from __future__ import annotations
import shutil
import time
from pathlib import Path

root = Path(__file__).resolve().parent
logs = root / "logs"
out = root / "raw-logs"
variants = ("base_accum", "candidate_accum", "candidate_ntt")
counts = {variant: 0 for variant in variants}
last = {}
stable = {}

while any(counts[v] < 12 for v in variants):
    for variant in variants:
        src = logs / f"measured-{variant}.log"
        if not src.exists():
            continue
        stat = src.stat()
        fingerprint = (stat.st_mtime_ns, stat.st_size)
        if fingerprint != last.get(variant):
            last[variant] = fingerprint
            stable[variant] = 0
            continue
        stable[variant] = stable.get(variant, 0) + 1
        if stable[variant] == 2 and counts[variant] < 12:
            counts[variant] += 1
            dst = out / f"pair-{counts[variant]:02d}-{variant}.log"
            shutil.copy2(src, dst)
            print(f"archived {dst.name}", flush=True)
    time.sleep(0.5)
print("all measured logs archived", flush=True)
