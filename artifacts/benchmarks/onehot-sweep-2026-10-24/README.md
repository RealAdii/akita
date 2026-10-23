# OneHot sweep selector comparison, 2026-10-24

## Scope

This compares the parent revision with the selector candidate that chooses Merge for `D >= 1024`, `active_a_cols > 256`, and at least 32 blocks per worker. It covers two supported profile shapes. Each run uses the same case for parent and candidate, with 16 randomized pairs and a balanced 8/8 order split. The order seed is 1024.

A negative percentage means the candidate is faster. Total time is setup + commitment + proving. The reported 95% intervals use 50,000 bootstrap resamples of paired percentage changes.

## Results

| Case | Ring dimension | Commitment median change | Commitment wins | Total median change | Total wins | 95% bootstrap interval | Proof bytes | Verifiers | Peak RSS median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `onehot_fp64:35:1:direct` | 1024 | -6.54% | 16/16 | -4.13% | 11/16 | -7.01% to +1.63% | 77,438, equal | Both passed in all runs | 1.995 GiB parent, 1.993 GiB candidate |
| `onehot_fp32:34:1:direct` | 2048 | +1.21% | 3/16 | +0.24% | 5/16 | -0.34% to +2.62% | 75,398, equal | Both passed in all runs | 1.186 GiB parent, 1.177 GiB candidate |

The fp64 shape has a consistent commitment improvement, while its end-to-end interval still includes no change. The fp32 shape does not show a commitment or end-to-end improvement. These measurements do not establish a general high-dimension win.

## Revisions and binaries

- Parent source: `dfdbd7674cab5cfbe95243e947d1b10a982f232b`
- Candidate source: `bc512f242ef637071191dc20714e63688c414e08`
- fp64 parent binary SHA-256: `a34948056b6558484453ffc29e7a08da9e8906fe72b2088f60f50c0df9c7b5be`
- fp64 candidate binary SHA-256: `3634611ebe82a0220bc52a09c527fddcf9afe468e681e4588bd9ecefd711783f`
- fp32 parent binary SHA-256: `2e3a0e1e8072ad151118c57ddf6a7e71f2b9c2f6dd257e42708af05ecdb10e43`
- fp32 candidate binary SHA-256: `28e662236e617ea2f0afeec924cf5abf8332e4e54b988dbfd4e01cf3196ea106`

The fp32 binaries were built with Rust 1.95 and `parallel,profile-ci-fp32,transcript-blake2b`. The fp64 binaries were built with the equivalent `profile-ci-fp64` feature set. Both comparisons ran on the same 12-logical-CPU, 24 GiB Mac with four Rayon workers, four prover threads, and four threaded-verifier workers. The single-threaded verifier also ran in every pair. The fp64 preflight required 1-minute load at most 4.0, CPU idle at least 65%, and free memory at least 40% for three consecutive samples. The fp32 run used load at most 8.0 with the same CPU and memory thresholds after a completed background job left the load average temporarily elevated. Its post-run snapshot had load 17.38 and CPU idle 19.26%, so the fp32 result should be treated as directional and repeated in a fully quiet window before making a strong claim. Exact phase rows and machine preflight records are included next to this report.

## Follow-up selector change

The candidate condition is narrowed to `D == 1024` while retaining the existing active-column and blocks-per-worker checks. This keeps the measured fp64 path and leaves higher dimensions on the general selector. A rebuilt profile binary selected Bucketed at `D=2048` and Merge at `D=1024`; both warmups produced the expected proof size and passed both verifier modes. The narrowed fp32 and fp64 binaries have SHA-256 `d8d9ba09fb22dcfcab91e0ba6879466877d721fdc7f3b7ab18d19d405b4e7f8e` and `732c4e88dd8ad6ae17e44968b82c43f8a1f32c89eab2b5b134b0998cb8fd4de6`, respectively.

This selector change has been compiled and smoke-measured. The two full paired results above compare the original broad candidate with its parent, not the narrowed revision.
