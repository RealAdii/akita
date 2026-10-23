# OneHot merge chunk width screen, 2026-10-24

## Decision

Keep `MERGE_COL_CHUNK` at 32. A 16-pair confirmation found no improvement for width 16. Setup plus commitment plus proving was a median 1.43% slower than width 32, the candidate won 7 of 16 pairs, and the paired 95% bootstrap interval was -8.63% to +13.30%. Commitment alone was a median 2.65% slower, with 6 of 16 wins. The result is inconclusive about small effects and does not justify changing the default.

The initial four-pair screens also found no clear alternative. Width 64 was a median 3.77% slower on setup plus commitment plus proving and 3.43% slower on commitment. Width 128 was effectively flat on commitment at +0.17%, and its four-pair total screen is too small to support a conclusion. The width 16 screen looked slightly faster, but the independent 16-pair confirmation did not reproduce that signal.

## Scope and method

This experiment isolates the merge column chunk width. Both binaries select the existing Merge sweep for the same `onehot_fp64:35:1:direct` case. The baseline is the exact width 32 binary from source commit `fac45c9d80b92556c1c2f729ed89d65ee0af0b47`. Each candidate binary uses the same source and build settings, with only the chunk width changed.

The profile used Rust 1.95.0, `parallel,profile-ci-fp64,transcript-blake2b`, four Rayon workers, four prover threads, and four verifier workers on a 12 logical CPU, 24 GiB Apple Silicon Mac. Each measured run includes setup, commitment, proving, proof size, peak RSS, and single-threaded plus multithreaded verification. The confirmation used 16 fresh-process pairs with an 8 to 8 order split and a 50,000-resample paired bootstrap interval. One warmup per binary was checked before measurement.

The initial screen used four randomized, balanced pairs each for widths 16, 64, and 128. It is only a screening pass. The later confirmation only tested width 16, the sole candidate with a weak positive screen signal.

## Correctness observations

All measured proofs were 77,438 bytes. Both verifier modes passed in every warmup and measured run. Median peak RSS in the width 16 confirmation was 1.989 GiB for width 32 and 1.993 GiB for width 16.

No code change was made from this experiment. The production constant remains 32. The measurements do not establish a performance improvement from changing chunk width.

## Artifacts

- `screening/width-16`, `screening/width-64`, and `screening/width-128` contain the raw run rows, paired rows, and screening summaries.
- `confirmation/width-16` contains all 16 confirmation pairs, the summary, the binary manifest, and the machine preflight capture.
- Binaries and full per-run logs remain on the workstation SSD at `/Volumes/DockerData/akita-merge-chunk-screen-20261024/`.

No test suites were run. This was a performance experiment only.
