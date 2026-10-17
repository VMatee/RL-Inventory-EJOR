# Canonical manuscript

Edit sections/*.tex and references.bib. main.tex builds the supplied Introduction and its 16 references. Other sections are excluded placeholders. No authors, abstract results or findings were invented.

Source Word: EJOR_Introduction_Limited_Data_GP_RL.docx. Hash and conversion details are in provenance.json; full source text is archived in research/briefs/INTRODUCTION_SOURCE_20261017.md. Prose is preserved; citation markup is converted to natbib. Source verification is a separate pending task.

## Build

Requires elsarticle.cls, elsarticle-harv.bst, BibTeX, latexmk and common TeX packages including xurl/microtype.

```bash
make manuscript
# Or from manuscript/:
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Generated files are ignored. Inspect PDF pages, references and overflow. Static checks do not compile TeX. The PC lacked TeX at setup; ask before installing system packages. See results/summaries/SETUP_VALIDATION.md for any build performed elsewhere.

One section per task/branch. New references need primary-source support in research/literature/REFERENCE_AUDIT.md. Keep proposal language until evidence exists. Word/PDF are review copies; transfer accepted edits back to LaTeX.

This is an editable Elsevier-style draft, not a complete submission or a claim of compliance with all current EJOR requirements. Before submission recheck journal instructions, actual authors, abstract, proofs/results, declarations and AI-use disclosure.

https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors
