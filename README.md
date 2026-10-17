# RL Inventory EJOR Research

**Working title:** *When Is Limited Demand Data Enough? Decision-Sensitive Policy Learning for Inventory Control*

**Status:** Research design / pre-experiment. This repository contains research plans, a draft manuscript skeleton, and future computational scaffolding. **No new theoretical results, empirical findings, or journal acceptance are claimed.**

## Primary research question

When is a limited history of demand sufficient to justify changing from a tuned baseline inventory policy to a learned one, and can inventory structure help quantify decision-relevant policy-improvement uncertainty more efficiently?

## Proposed scope

Single-item, periodic-review, lost-sales inventory with a known, fixed positive lead time; limited initial demand histories; Gaussian-process demand uncertainty; an inventory simulator with known stock-flow dynamics; and policy learning with decision-sensitive safeguards. Rolling service constraints, multi-echelon extensions, and censored-demand inference are **not** the core contributions in the current research brief.

## Repository map

- `research/briefs/`: original research strategy (Thai), preserved for traceability
- `research/literature/` and `research/novelty/`: verified references and prior-art checks
- `docs/`: charter, decisions, and milestones
- `manuscript/`: EJOR-oriented LaTeX draft, currently placeholders
- `theory/`: inventory specification and proposed claims requiring proof
- `data/`: dataset provenance and leakage-safe data handling (no raw datasets committed)
- `experiments/`: fixed evaluation protocols, baseline registry, and experiment configurations
- `src/inventory_ejor/` and `tests/`: future Python implementation and tests
- `results/`: eventually reproducible outputs, with provenance
- `infrastructure/`: local Serena/GitHub setup guidance

## Proposed evidence plan

1. Controlled synthetic cases and small-state dynamic programming references.
2. M5 sales-driven inventory simulations with strictly limited training windows (28, 56, 112, 224 days proposed).
3. Favorita as external validation once the method and evaluation protocol are frozen.

M5 and Favorita report retail **sales**, not complete latent demand, real replenishment decisions, or actual operational cost ledgers. Cost and lead-time values used in simulation must be reported as scenario assumptions unless supported by data.

## Research integrity and reproducibility

Do not invent citations, mathematical guarantees, test results, or business impact. Compare strong inventory-specific baselines under matched information and computational budgets, track training/validation/test information separately, and preregister non-inferiority margins **before** examining final results.

See `AGENTS.md` for rules used by ChatGPT/Codex/Serena and the original Thai strategy in `research/briefs/`.

## Getting started

Read `docs/PROJECT_CHARTER.md`, `experiments/protocol/`, and `infrastructure/SERENA_GITHUB_SETUP.md` before implementing new algorithms. The repository is **not yet an implemented experiment pipeline**.
