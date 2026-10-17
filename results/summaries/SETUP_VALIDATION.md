# Workflow setup validation - 2026-10-17

**Infrastructure evidence only. No inventory/GP/RL experiment or scientific claim is validated.**

Tested code commit: `ebdfca7162eb28f7b0167c08bd59f3994816ea4d`.

## Local PC through SeneraAiServer

Checkout: `/home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR`.
Interpreter: existing `.venv/bin/python`, Python 3.10.12.

| Check | Observed outcome |
|---|---|
| Static repository/citation check | Passed; 16 bibliography entries, 16 cited keys resolve |
| unittest discovery | 6 infrastructure tests passed |
| bash syntax / Python compilation | Passed for sync/check/runner/test files |
| git diff --check | Passed |
| Clean-tree smoke | Exit 0, succeeded, source unchanged |
| Deliberate child exit 7 | Wrapper returned 7, status failed, source unchanged |
| Deliberate 3-second sleep with 1-second limit | Wrapper returned 124, status timed_out, source unchanged |
| Sync requested from non-main branch | Refused with exit 2; no source discarded |

Success run: `20261017T115923Z-smoke-0482a48e`.
Failure-propagation test: `20261017T115924Z-smoke-d2e56419`.
Timeout test: `20261017T115924Z-smoke-0d51d4d0`.
These deliberate failure cases passed their expected-behavior checks; they were not research failures.

The success manifest is retained in `setup_smoke_manifest.json`. Full logs/config/environment snapshots stay in ignored local results/runs directories. The wrapper records the seed/config but the supplied child algorithm must consume them explicitly.

## Manuscript build in the ChatGPT temporary environment, NOT on the PC

The main.tex, Introduction, BibTeX and archived source hashes matched the PC files. A 7-page PDF compiled with elsarticle and was visually inspected on every page. No undefined citations or overfull boxes remained. Some normal underfull typesetting warnings remained. The empty abstract/author areas reflect the intentionally incomplete Introduction-only manuscript, not a submission-ready paper.

Build command in that environment:

```bash
latexmk -pdf -e '$bibtex = "bibtex.original %O %B";' -interaction=nonstopmode -halt-on-error main.tex
```

The temporary environment had a broken default bibtex symlink; its existing bibtex.original executable was used without changing system packages. On a normally configured PC, use `make manuscript`. Local TeX remains uninstalled/unverified.

Verified source SHA-256:

| File | SHA-256 |
|---|---|
| manuscript/main.tex | 562fe30f6632cb7997bb5a027e6d83e7a3f6fed3a2ce4d6aab080a6d9b4ace66 |
| manuscript/sections/01_introduction.tex | 194b11f25e8284f62a6f478946178cdd6dc7d95e3ccea15e95d3192a602f3685 |
| manuscript/references.bib | 8496594f361250a863a1060dc73ceb9c10cac7c9356a149561a54586e12e6da7 |
| research/briefs/INTRODUCTION_SOURCE_20261017.md | 664d4da753be60f1d6f7bffffdf3366a856f2d63f57e485229269fb927d59457 |

## Not performed

No independent reference audit, Codex login/task, scientific implementation, benchmark reproduction, raw data download, GPU training, ML dependency installation, GitHub Actions run, change of visibility/credentials or journal submission. The local Git identity was configured from existing commit metadata only, without changing global identity.

Next milestone: M1 model conventions and minimal deterministic inventory environment.
