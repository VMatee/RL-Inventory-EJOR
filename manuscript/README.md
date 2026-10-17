# Canonical manuscript

Edit sections/*.tex and references.bib. main.tex builds the current Introduction and its 16 references using elsarticle with author-year citations. Other sections remain excluded placeholders. No authors, abstract findings or research results were invented.

## Source and revisions

The initial Word source was EJOR_Introduction_Limited_Data_GP_RL.docx. Its checksum and initial conversion record are preserved in provenance.json; the original text remains archived in research/briefs/INTRODUCTION_SOURCE_20261017.md.

The Introduction was substantively revised on 2026-10-17 at the user's request, preserving the agreed limited-demand-data inventory direction. It is no longer a verbatim conversion of the Word draft. The revision sharpens the policy-change question, states the policy-cost difference explicitly and distinguishes proposed inventory-specific analysis from established Bayesian and baseline-relative methods.

See provenance.json for source hashes, research/literature/REFERENCE_AUDIT.md for scoped source checks, and results/summaries/INTRODUCTION_REVISION_20261017.md for validation. Source checks do not establish that the proposed method is novel or successful. Conditional contribution language must be replaced by evidence-backed claims only after the work is completed.

## Build

Requires elsarticle.cls, elsarticle-harv.bst, BibTeX, latexmk and common TeX packages including xurl/microtype.

```bash
make manuscript
# Or from manuscript/:
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Generated files are ignored. Inspect PDF pages, references and overflow. Static checks do not compile TeX. The local PC lacked TeX during this revision; no system packages were installed. Matching revised sources compiled to seven visually reviewed pages in the ChatGPT temporary environment only.

One section per task/branch. New references need primary-source support in research/literature/REFERENCE_AUDIT.md. Word/PDF are derived review copies; transfer accepted edits back to LaTeX. Preserve source provenance when revising prose.

## Submission status

This is an editable Elsevier-style Introduction, not a complete submission. The author guide endpoint could not be read in the current check; no claim of full compliance with the latest EJOR submission requirements is made. Before submission recheck actual authors, abstract, proofs/results, declarations, AI-use disclosure, current formatting and the complete compiled document.

https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors
