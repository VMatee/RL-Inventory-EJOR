# Project charter

## Objective
Study when limited pre-deployment demand histories suffice for defensible inventory policy improvement. Proposed method: GP posterior for unknown demand, exact inventory stock-flow simulation, and inventory-specific uncertainty analysis for policy differences against a strong baseline.

## Fixed initial scope
Single item; periodic review; lost sales; fixed known lead time; limited initial demand observations; neural policy learning. Do not add rolling service constraints or multi-echelon control as core contributions.

## Proposed contributions (NOT established)
1. Inventory-structured estimation/bounds for uncertainty in paired policy cost differences.
2. Policy improvement that resists exploiting GP model error.
3. Decision-relevant criterion for when limited data are sufficient.

## Acceptance gates
Mathematically defensible result or meaningful validated algorithmic advance; matched-data and matched-compute ablations; comparisons against strong inventory methods; transparent failures and reproducible evaluation.
