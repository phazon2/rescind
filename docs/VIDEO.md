# Video script — 2:35, word for word

Hard cap is 3:00 and judges are not required to watch past it. This runs 2:35
with two deliberate silences.

**Narration:** Spanish is fine — better, even. Burn English captions. A real
accent on a real supply-chain problem reads as domain credibility, not as a
liability. What gets scored is the writing, not the production.

**Recording notes**
- Screen-record the demo page at `https://phazon2.github.io/rescind/` (or
  `web/index.html` opened from disk — it works either way).
- One browser tab. No terminal, no logs, no architecture diagram on screen.
- Do not narrate over the two silences. They are doing work.
- Read the last line slightly slower than the rest.

---

### 0:00 — 0:14 · Hook

**On screen:** the demo page, top of the lot card. `LOT-2026-0619-NV`, Northvale
Dairy Co-op, 4,800 units staged for Meridian Foods DC-7.

> At three o'clock, Northvale Dairy recalls a lot of infant formula.
> At three-oh-four, the AI agent tells the distribution centre it's fine to ship
> four thousand eight hundred tins.
>
> The agent isn't broken. It's remembering a certificate that doesn't exist any
> more.

---

### 0:14 — 0:38 · Setup

**On screen:** scroll slowly through the six memories. Let the two `concluded`
badges land.

> This is the agent's memory of that lot. Three things it observed — a
> certificate of analysis, a cold chain log, a supplier audit. And three
> conclusions it built on top of them.
>
> Every memory store on the market can write these. Not one of them can take one
> back. To do that you need transactions, foreign keys, and time travel — and no
> vector database has any of the three.

**On screen:** the agent's answer panel — `RELEASE`, 4 live supporting memories.

> Right now the agent says: release.

---

### 0:38 — 1:20 · The peak beat — cascade, refusal, proof

**On screen:** click the recall button. Then **stop talking.** Let the page
change on its own: three memories strike through, the verdict flips to
`REFUSED`, the flag appears.

> *(silence — 4 seconds)*

**On screen:** the blast-radius panel — 3 / 2 / 1.

> One certificate was withdrawn. Two conclusions built on it came down with it.
> One decision already given to a human got flagged for review.
>
> One transaction. All of it, or none of it — because a half-finished retraction
> is worse than none at all.

**On screen:** back up to the answer panel, now `REFUSED`.

> And here's the part that matters. Same lot, same question, asked again.
>
> The agent refuses. Not because a model changed its mind — because it can now
> only find one live supporting memory, and the threshold is two. Retraction
> didn't just hide a row. It changed what the agent is able to conclude.

**On screen:** the time-travel panel. Knew 4, knows 1.

> And it can still prove what it used to know. This isn't a reconstruction — the
> decision stored the cluster's logical clock, so this reads the exact same
> snapshot the agent read at three-oh-four.

---

### 1:20 — 1:30 · Silence

**On screen:** hold on the two columns side by side — four memories on the left,
one on the right.

> *(silence — 8 seconds. Do not narrate. This is the whole product in one frame.)*

---

### 1:30 — 2:05 · Why it's built this way

**On screen:** `sql/001_schema.sql`, the `CREATE VECTOR INDEX` line highlighted.

> One detail, because it's the reason this works at all.
>
> The retracted flag is a computed column, and it's a prefix column of the vector
> index. CockroachDB won't use a vector index unless every prefix column is
> constrained — so every single search is forced to say `retracted = false`.
>
> Retracted memory isn't filtered out in application code. It's unreachable. You
> can't write the fast query and forget the filter, because the filter is what
> makes it fast.

**On screen:** `ci/latest.json`, scrolled to the test summary.

> Thirteen tests, against a real CockroachDB cluster, on every push. No database
> mocks — the behaviour only exists in CockroachDB, so mocking it would prove
> nothing.

---

### 2:05 — 2:35 · Close

**On screen:** the demo page, back at the top.

> The buyer is a director of quality assurance at a food or pharma distributor.
> The budget line is FSMA 204 — the FDA traceability rule, compliance date July
> twentieth, 2028.
>
> They can't deploy an agent into a recall workflow today, because they can't
> prove what it knew, and they can't take back what it learned.
>
> **When a lot is recalled, Rescind pulls back every conclusion the agent built
> on it — in one transaction, with proof of what the agent knew before and after.**

**On screen:** `github.com/phazon2/rescind`. Hold 3 seconds. End.

---

## The one thing not to change

The final sentence is the same sentence in the README, the app UI, and the
Devpost description, worded identically. Do not add a caveat to it on camera.
Caveats live in `docs/LIMITS.md`, and there are plenty of them there.
