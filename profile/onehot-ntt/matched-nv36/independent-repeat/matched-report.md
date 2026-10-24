# Independent matched fp128 nv36 benchmark

## Result

A second, independent 12-pair run confirms the exact NTT improvement on the direct fp128 nv36 workload. Candidate exact NTT reduced median setup + commitment + proving time by **33.12%** versus base accumulation, faster in all 12 pairs. The paired bootstrap 95% interval was **-33.63% to -32.15%**. Negative values mean the candidate used less time.

Across both batches, the pooled 24-pair median reduction was **33.12%**, with a paired bootstrap 95% interval of **-33.41% to -32.55%**. Exact NTT was faster in all 24 pairs. The first batch had a brief low-priority research script overlap at an unknown arm. The separate repeat below independently reproduces the gain without that specific overlap.

| Phase | Independent repeat median change vs base | 95% paired interval | Faster pairs |
| --- | ---: | ---: | ---: |
| Setup | +9.97% | +5.08% to +19.31% | 1/12 |
| Commitment | -43.09% | -43.83% to -42.33% | 12/12 |
| Proving | +5.81% | +3.05% to +8.76% | 2/12 |
| Setup + commitment + proving | -33.12% | -33.63% to -32.15% | 12/12 |

The candidate accumulation path by itself was 2.31% slower than base on total time in this repeat. The measured end-to-end win is specific to the candidate exact NTT path.

Median peak RSS in the independent repeat was 10.75 GiB for base accumulation, 10.56 GiB for candidate accumulation, and 10.07 GiB for candidate exact NTT. Candidate exact NTT used 6.32% less peak RSS than base at the median.

All 36 runs in this repeat exited successfully, passed both verifier modes, and reported a proof size of 81,763 bytes. The saved `.proof` artifact files are 81,771 bytes on disk. For every one of the 12 measured pairs, candidate exact NTT and candidate accumulation produced byte-identical commitment and proof artifacts. Base artifacts were not saved, so this does not claim byte identity against the base arm.

## Method

- Workload: `onehot_fp128:36:1:direct:standard`, one polynomial, direct and non-recursive.
- 12 randomized triplets comparing base accumulation, candidate accumulation, and candidate exact NTT.
- A different randomized order seed from the first batch. Each arm occupied each of the three run positions four times.
- 8 worker threads on a host reporting 12 logical CPUs and 24 GiB physical memory.
- 50,000 paired bootstrap resamples, seed `20261025` for this repeat.
- The runner recorded three readiness values that meet its thresholds: CPU idle 82.7% to 85.3%, one-minute load 3.01 to 3.33, available memory 55.54% to 56.46%. Its code requires three consecutive qualifying samples, but timestamps were not saved, so the packet cannot independently verify their spacing.
- The specific low-priority script overlap identified in the initial batch was not part of this repeat. The measured CSV, logs, saved candidate artifacts, and runner are included here.
- Base source: `cc3ea3690d5a17123c2309c5ec84c41341005e96`.
- Candidate source: `a2b5ba81d8acfb554c4a75b8ea0a7a312d218480`.
- Base binary SHA-256: `93c6146d9db860ed48d17b5ff6f4baab52fb3d0029f14879aa8e13573ca5f8de`.
- Both candidate arms use binary SHA-256: `7e692332b1c3c279d23e917d032373235e89e4a69653153c625cb87d62554530`.

## Scope

This is a local performance result for one direct, non-recursive fp128 nv36 case. It does not establish results for recursive nv36, nv38, other machines, or other workloads. It is not a security finding. The pooled 24-pair interval includes the initial batch and its disclosed incidental overlap; the separate 12-pair repeat is the clean confirmation.

## Reproduction files

- `matched-runs.csv`: all 36 measurements from the independent repeat.
- `matched-summary.json`: paired statistics, binary hashes, proof status, machine details, and readiness samples.
- `matched-combined.csv` and `matched-combined-summary.json`: both batches and the pooled 24-pair calculation.
- `raw-logs/`: all 36 measured arm logs, archived separately.
- `logs/`: warmup and final measured logs.
- `proofs/`: saved candidate commitments and proofs.
- `ntt_matched_runner.py`: benchmark runner with independent order and bootstrap seeds.
- `archive_measured_logs.py`: log archiver used during this repeat.
- `combine_matched_runs.py`: script that builds the pooled CSV and summary.
