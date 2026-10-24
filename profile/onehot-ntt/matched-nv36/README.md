# Matched fp128 nv36 benchmark

## Result

On this host and workload, the candidate exact NTT path reduced median setup + commitment + proving time by **33.04%** versus the base accumulation path across 12 paired runs. It was faster in all 12 pairs. The paired bootstrap 95% interval for the median relative change was **-34.39% to -31.79%**. Negative values mean less elapsed time.

The benefit came from commitment: median commitment time fell **42.74%** (95% interval -44.11% to -41.00%, faster in 12/12 pairs). Setup was **15.35% slower** at the median, with a wide interval (1.62% to 90.01%). Proving was **2.30% slower** at the median (interval -1.03% to 3.13%). These measurements support a strong end-to-end win for this case, while identifying setup as a cost to investigate.

Median peak RSS was 10.18 GiB for base accumulation and 10.07 GiB for candidate NTT, a 1.08% decrease. Candidate accumulation was 10.57 GiB, 3.85% above base. All 36 proof runs produced 81,763-byte proofs and passed both verifier modes.

## Method

- Case: `onehot_fp128:36:1:direct:standard` (direct, non-recursive fp128 one-hot, nv36, one polynomial).
- Compared three arms in randomized, paired triplets: base accumulation, candidate accumulation, and candidate exact NTT.
- 12 pairs, 8 threads, 12 logical CPUs, 24 GiB physical memory.
- Paired bootstrap: 50,000 resamples, seed `20261024`.
- Each arm appeared four times in each run position. Three readiness samples met the runner's quiet rule before measurement.
- Base source: `cc3ea3690d5a17123c2309c5ec84c41341005e96`.
- Candidate source: `a2b5ba81d8acfb554c4a75b8ea0a7a312d218480`.
- Base binary SHA-256: `93c6146d9db860ed48d17b5ff6f4baab52fb3d0029f14879aa8e13573ca5f8de`.
- Both candidate arms use binary SHA-256: `7e692332b1c3c279d23e917d032373235e89e4a69653153c625cb87d62554530`.

## Scope and caveats

This is a local direct nv36 result. It is not a recursive nv36 result and does not establish performance for nv38 or other machines. A separate low-priority research script ran for about 0.6 seconds during one benchmark arm; the exact pair was not retained, so a small amount of incidental contention cannot be ruled out. The three pre-run quiet samples and randomized paired ordering reduce, but do not eliminate, host-noise concerns. The setup increase deserves follow-up profiling before attributing the end-to-end result to a specific implementation detail.

## Reproduction files

- `matched-runs.csv`: all 36 measurements.
- `matched-summary.json`: paired statistics, machine details, readiness samples, proof and verifier status.
- `raw-logs/`: archived logs for pairs 5 to 12.
- `logs/`: warmup and final measured logs.
- `ntt_matched_runner.py`: runner used for the measurement.

All benchmark runs exited successfully. This is a performance measurement, not a security finding.
