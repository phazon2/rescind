# Narration sheet

Generated from `web/timeline.js` by `scripts/make_srt.py`. Do not edit by hand.

- **Total runtime: 2:44** (hard cap is 3:00 — judges are not required to watch past it)
- Spoken: 148s across 35 cues, 366 words (~149 words/minute — a calm, unhurried pace)
- Deliberate silence: 16s

Open `web/present.html`, press **Space**, and read each line as it appears. The captions are burned in at these exact times, so if you read along you are automatically in sync.

Where the text is blank, **say nothing** — the visual is carrying that beat alone. Those silences are deliberate and they are doing work.

| Time | Scene | Say |
|---|---|---|
| 0:00 | lot | At 3:00 PM, Northvale Dairy Co-op recalls a lot of infant formula. |
| 0:04 | lot | At 3:04, the agent tells the distribution centre it's fine to ship 4,800 tins. |
| 0:10 | lot | The agent isn't broken. It's remembering a certificate that no longer exists. |
| 0:14 | memory | This is the agent's memory of that lot. |
| 0:17 | memory | Three things it observed. Three conclusions it built on top of them. |
| 0:21 | memory | Every memory store on the market can write these. Not one of them can take one back. |
| 0:26 | memory | Retraction needs transactions, foreign keys, and time travel. |
| 0:30 | release | No vector database has any of the three. CockroachDB has all three. |
| 0:35 | release | Right now, the agent says: release. |
| 0:38 | recall | _(silence — say nothing)_ |
| 0:42 | cascade | One certificate withdrawn. |
| 0:44 | cascade | Two conclusions built on it came down with it. |
| 0:48 | cascade | One decision already given to a human, flagged for review. |
| 0:52 | cascade | One transaction. All of it, or none of it. |
| 0:56 | refused | Same lot. Same question. Asked again. |
| 0:59 | refused | The agent refuses. |
| 1:02 | refused | Not because a model changed its mind. |
| 1:05 | refused | Because it can now find only one live supporting memory, and the threshold is two. |
| 1:10 | refused | Retraction didn't hide a row. It changed what the agent is able to conclude. |
| 1:15 | replay | And it can still prove what it used to know. |
| 1:19 | replay | This is not a reconstruction. |
| 1:21 | replay | The decision stored the cluster's hybrid logical clock, |
| 1:25 | replay | so this reads the exact snapshot the agent read at 3:04. |
| 1:29 | hold | _(silence — say nothing)_ |
| 1:37 | index | One detail, because it is why this works at all. |
| 1:41 | index | The retracted flag is a computed column, and a prefix column of the vector index. |
| 1:47 | index | CockroachDB will not use a vector index unless every prefix column is constrained. |
| 1:52 | index | So every single search is forced to say: retracted = false. |
| 1:56 | index | Retracted memory isn't filtered out. It is unreachable. |
| 2:00 | receipt | Every test runs against a real CockroachDB cluster, on every push. |
| 2:05 | receipt | No database mocks. The behaviour only exists in CockroachDB. |
| 2:09 | receipt | _(silence — say nothing)_ |
| 2:11 | close | The buyer is a director of quality assurance at a food or pharma distributor. |
| 2:16 | close | The budget line is FSMA 204. Compliance date: July 20th, 2028. |
| 2:21 | close | They cannot deploy an agent into a recall workflow today, |
| 2:25 | close | because they cannot prove what it knew, and cannot take back what it learned. |
| 2:30 | claim | When a lot is recalled, Rescind pulls back every conclusion the agent built on it - |
| 2:35 | claim | in one transaction, with proof of what the agent knew before and after. |
| 2:41 | end | _(silence — say nothing)_ |
