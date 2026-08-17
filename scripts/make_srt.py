#!/usr/bin/env python3
"""Generate docs/rescind.srt and a narration sheet from web/timeline.js.

One source of truth: the burned-in captions on the presentation page, the
subtitle track uploaded to YouTube, and the narration script all come from the
same cue list, so they cannot drift apart.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TIMELINE = ROOT / "web" / "timeline.js"
SRT = ROOT / "docs" / "rescind.srt"
SHEET = ROOT / "docs" / "NARRATION.md"


def load() -> dict:
    raw = TIMELINE.read_text()
    _, _, payload = raw.partition("=")
    return json.loads(payload.strip().rstrip(";"))


def stamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> int:
    data = load()
    cues = data["cues"]

    # Overlap check: subtitles that overlap render on top of each other.
    for a, b in zip(cues, cues[1:]):
        if round(a["start"] + a["dur"], 3) > round(b["start"], 3) + 1e-6:
            print(
                f"cue at {a['start']}s overruns the next cue at {b['start']}s",
                file=sys.stderr,
            )
            return 1

    blocks, n = [], 0
    for cue in cues:
        if not cue["text"].strip():
            continue  # deliberate silence carries no subtitle
        n += 1
        blocks.append(
            f"{n}\n{stamp(cue['start'])} --> {stamp(cue['start'] + cue['dur'])}\n"
            f"{cue['text'].strip()}\n"
        )

    SRT.parent.mkdir(exist_ok=True)
    SRT.write_text("\n".join(blocks))

    total = cues[-1]["start"] + cues[-1]["dur"]
    spoken = sum(c["dur"] for c in cues if c["text"].strip())
    silence = total - spoken
    words = sum(len(c["text"].split()) for c in cues)

    # The narration sheet: what to say, when, at a glance.
    lines = [
        "# Narration sheet",
        "",
        f"Generated from `web/timeline.js` by `scripts/make_srt.py`. Do not edit by hand.",
        "",
        f"- **Total runtime: {int(total // 60)}:{int(total % 60):02d}** "
        f"(hard cap is 3:00 — judges are not required to watch past it)",
        f"- Spoken: {spoken:.0f}s across {n} cues, {words} words "
        f"(~{words / (spoken / 60):.0f} words/minute — a calm, unhurried pace)",
        f"- Deliberate silence: {silence:.0f}s",
        "",
        "Open `web/present.html`, press **Space**, and read each line as it "
        "appears. The captions are burned in at these exact times, so if you "
        "read along you are automatically in sync.",
        "",
        "Where the text is blank, **say nothing** — the visual is carrying that "
        "beat alone. Those silences are deliberate and they are doing work.",
        "",
        "| Time | Scene | Say |",
        "|---|---|---|",
    ]
    for cue in cues:
        t = f"{int(cue['start'] // 60)}:{int(cue['start'] % 60):02d}"
        text = cue["text"].strip() or "_(silence — say nothing)_"
        lines.append(f"| {t} | {cue['scene']} | {text} |")

    SHEET.write_text("\n".join(lines) + "\n")

    print(f"wrote {SRT.relative_to(ROOT)} ({n} subtitle cues)")
    print(f"wrote {SHEET.relative_to(ROOT)}")
    print(f"runtime {int(total // 60)}:{int(total % 60):02d}, {silence:.0f}s of silence")
    if total > 180:
        print("WARNING: runtime exceeds the 3:00 cap", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
