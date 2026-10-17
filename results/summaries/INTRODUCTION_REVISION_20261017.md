# Introduction revision: validation record

Date: 2026-10-17.

## Scope

User-requested manuscript revision for the existing EJOR project. No research-scope change, method implementation, dataset download, experiment or proof was performed. This record concerns editing, compilation, source support and infrastructure checks only.

Starting main: `89933c8eff05417e9396bc0ce71fb253966d34e4`.

Validated manuscript source: `17e9304c67d6993a0631fed2d8b5be872730708a` on `docs/introduction-ejor-revision-20261017`. Subsequent documentation-only commits may contain this validation record without changing the source hashes below.

## Manuscript changes

- Approximately 1,550 words in the English Introduction; 16 existing reference keys remain cited, including eight EJOR articles.
- Sharper replenishment-policy-change motivation under limited initial real demand data.
- Explicit policy-cost-difference equation under a common demand process, initial state and horizon.
- No novelty claim for GP+RL, small data, posterior sampling, common random numbers or baseline-relative regret alone.
- Inventory-specific analysis remains a research objective, not a completed theorem.
- Explicit epistemic/aleatoric/Monte Carlo distinctions, adaptive-selection caveat, and frozen-deployment information protocol.
- Synthetic, M5 and external Favorita evaluation remain planned. Sales replay is not observed retailer policy improvement or uncensored demand.
- The original Word-derived archive remains unchanged. Current prose is no longer described as a verbatim conversion.

## Local PC checks

Executed through SeneraAiServer using the existing project Python interpreter, in a temporary detached worktree at the validated manuscript-source SHA:

```bash
.venv/bin/python scripts/check_project.py
.venv/bin/python -m unittest discover -s tests -v
git diff --check 89933c8eff05417e9396bc0ce71fb253966d34e4 17e9304c67d6993a0631fed2d8b5be872730708a
```

The interpreter was addressed by its absolute path when running inside the temporary worktree.

Results: repository/citation check passed; 16 bibliography entries and 16 cited keys resolved; six infrastructure tests passed; diff whitespace check passed. Introduction, bibliography and main.tex SHA256 values matched the compiled temporary-environment sources. The worktree was removed normally. Local main was left unchanged and clean during this pre-merge check.

## Compilation and visual verification

Environment: ChatGPT temporary container, NOT the user's PC.

Build: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` with the existing elsarticle/natbib scaffold. The container's broken BibTeX executable link required an isolated PATH shim to `/usr/bin/bibtex.original`; no system installation or PC change was made.

Result: seven pages. Final log: no unresolved citations, LaTeX warnings, overfull boxes or underfull boxes. All pages were rendered and visually reviewed; the two reference pages affected by the final capitalization corrections were rerendered and reviewed. The remaining five page images were byte-identical to their reviewed versions.

| Source | SHA256 |
|---|---|
| manuscript/sections/01_introduction.tex | a02187633f9e215ff0dc9b747c084790235fbc99d92539e919d83bc518c9f6a7 |
| manuscript/references.bib | b78ba8f9e007b0000e05a45e224c0360f7658ba2c7284dc33a8cf33745200238 |
| manuscript/main.tex | 562fe30f6632cb7997bb5a027e6d83e7a3f6fed3a2ce4d6aab080a6d9b4ace66 |
| Review PDF (not committed) | 9b637ef569cd0b911e723b1ae7262902e63533df2cd14de571f015d2f4075ac4 |

## What this does not establish

- No local-PC TeX build: TeX tools were not detected and no installation was authorized/performed.
- No scientific validation, new theorem, sample-efficiency result or EJOR acceptance claim.
- No complete reference metadata audit, proof comparison or systematic novelty search. The actual scoped checks are recorded in research/literature/REFERENCE_AUDIT.md.
- No data access/license verification or M5/Favorita reproduction.
- No author details, abstract, Methods or Results were invented.
- The full current EJOR author-guide endpoint was inaccessible. The draft is Elsevier-style, not certified compliant with every submission requirement.

Final publication/synchronization should be checked against the PR merge and actual local/remote HEAD values. The next scientific task is M1: inventory timing/initial/terminal conventions and deterministic simulator tests.
