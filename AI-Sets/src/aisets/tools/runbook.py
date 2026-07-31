"""Read tool: `find_runbook` — a simple keyword search over the runbook
markdown files in `data/runbooks/`, the agent's equivalent of an internal
wiki search."""

from __future__ import annotations

from pathlib import Path

from aisets.agent.tools import tool


def make_find_runbook_tool(runbooks_dir: Path):
    @tool(permission="read", name="find_runbook")
    def find_runbook(keywords: str) -> list[dict]:
        """Search runbook documents for any of the given space-separated
        keywords (e.g. 'payments timeout gateway'). Returns a list of
        {filename, snippet} for every runbook that contains at least one
        keyword, most-keyword-matches first. Use this once you have a
        hypothesis about WHAT is wrong, to find the recommended diagnosis/
        fix steps — don't guess at a fix without checking a runbook first."""
        terms = [t.lower() for t in keywords.split() if t.strip()]
        if not terms:
            return []

        results = []
        for path in sorted(Path(runbooks_dir).glob("*.md")):
            content = path.read_text(encoding="utf-8")
            lowered = content.lower()
            match_count = sum(lowered.count(term) for term in terms)
            if match_count > 0:
                snippet = content.strip().splitlines()[0:6]
                results.append({
                    "filename": path.name,
                    "match_count": match_count,
                    "snippet": "\n".join(snippet),
                })

        results.sort(key=lambda r: r["match_count"], reverse=True)
        return results

    return find_runbook
