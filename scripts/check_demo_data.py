#!/usr/bin/env python3
"""Assert the recorded demo still tells the story, before it is published.

A demo page that silently goes quiet -- no cascade, no refusal, no flagged
decision -- would be worse than no demo at all, because it would look fine. This
runs in the publish workflow so a broken recording can never become the live
demo.
"""

from __future__ import annotations

import json
import pathlib
import sys

DATA_JS = pathlib.Path(__file__).resolve().parent.parent / "web" / "data.js"


def load() -> dict:
    raw = DATA_JS.read_text()
    # window.RESCIND_DATA = { ... };
    _, _, payload = raw.partition("=")
    return json.loads(payload.strip().rstrip(";"))


def main() -> int:
    if not DATA_JS.exists():
        print(f"{DATA_JS} is missing; run scripts/record_demo.py", file=sys.stderr)
        return 1

    d = load()
    checks = [
        ("starts at release", d["before"]["decision"]["verdict"] == "release"),
        ("ends at refused", d["after"]["decision"]["verdict"] == "refused"),
        ("cascade reaches beyond the roots", d["retraction"]["cascade_beyond_roots"] >= 1),
        ("flags at least one decision", d["retraction"]["decisions_flagged"] >= 1),
        ("replay shows a withdrawn memory", len(d["replay"]["withdrawn_since"]) >= 1),
        ("replay knew more than it knows", len(d["replay"]["knew_then"]) > len(d["replay"]["knows_now"])),
    ]

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")

    if failed:
        print(f"\ndemo data no longer tells the story: {failed}", file=sys.stderr)
        return 1

    r = d["retraction"]
    print(
        f"\ndemo intact: {r['facts_retracted']} retracted, "
        f"{r['cascade_beyond_roots']} by cascade, "
        f"{r['decisions_flagged']} flagged"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
