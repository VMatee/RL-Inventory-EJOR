#!/usr/bin/env python3
"""Static structure/citation checks, not scientific or bibliographic validation."""
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    'README.md', 'AGENTS.md', 'docs/STATUS.md', 'docs/TASKS.md',
    'docs/WORKFLOW.md', 'docs/CLAIMS.md', 'docs/EXPERIMENT_RUNBOOK.md',
    'docs/PROJECT_CHARTER.md', 'experiments/protocol/EVALUATION.md',
    'manuscript/main.tex', 'manuscript/references.bib', 'manuscript/provenance.json',
    'manuscript/sections/01_introduction.tex', 'research/literature/REFERENCE_AUDIT.md',
)

def validate(root: Path = ROOT) -> tuple[list[str], int, int]:
    errors = [f'Missing: {p}' for p in REQUIRED if not (root / p).is_file()]
    bib = root / 'manuscript/references.bib'
    keys = re.findall(r'@\w+\s*\{\s*([^,\s]+)\s*,', bib.read_text() if bib.exists() else '')
    if len(keys) != len(set(keys)):
        errors.append('Duplicate bibliography keys')
    cited: set[str] = set()
    for file in (root / 'manuscript').rglob('*.tex'):
        text = '\n'.join(line for line in file.read_text().splitlines() if not line.lstrip().startswith('%'))
        if re.search(r'\\\\(?:section|documentclass|begin|end)\b', text):
            errors.append(f'Escaped LaTeX command: {file.relative_to(root)}')
        for group in re.findall(r'\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}', text):
            cited.update(k.strip() for k in group.split(','))
        for rel in re.findall(r'\\input\{([^}]+)\}', text):
            target = root / 'manuscript' / rel
            if not target.suffix:
                target = target.with_suffix('.tex')
            if not target.is_file():
                errors.append(f'Missing LaTeX input: {rel}')
    errors.extend(f'Undefined citation: {k}' for k in sorted(cited-set(keys)))
    if not keys:
        errors.append('No bibliography entries')
    if not cited:
        errors.append('No manuscript citations')
    return errors, len(keys), len(cited)

def main() -> int:
    errors, entries, cited = validate()
    if errors:
        for error in errors:
            print('FAIL:', error)
        return 1
    print(f'PASS: repository structure; {entries} bibliography entries; {cited} cited keys resolve.')
    print('Scope: infrastructure only; no source fact-check, TeX build or research validation.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
