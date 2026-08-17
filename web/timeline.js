// Single source of truth for the video: captions, timings and scene changes.
//
// web/present.html renders this as an auto-playing presentation to screen-record.
// scripts/make_srt.py generates docs/rescind.srt from this same file, so the
// burned-in captions, the narration script and the uploaded subtitle track can
// never drift apart.
//
// `start` and `dur` are seconds. A cue with no `text` is a deliberate silence:
// do not narrate over it, the visual is carrying the beat alone.
window.RESCIND_TIMELINE = {
  "title": "Rescind - retractable agent memory",
  "cues": [
    { "start": 0.0,   "dur": 4.5, "scene": "lot",      "text": "At 3:00 PM, Northvale Dairy Co-op recalls a lot of infant formula." },
    { "start": 4.5,   "dur": 5.5, "scene": "lot",      "text": "At 3:04, the agent tells the distribution centre it's fine to ship 4,800 tins." },
    { "start": 10.0,  "dur": 4.0, "scene": "lot",      "text": "The agent isn't broken. It's remembering a certificate that no longer exists." },

    { "start": 14.0,  "dur": 3.0, "scene": "memory",   "text": "This is the agent's memory of that lot." },
    { "start": 17.0,  "dur": 4.5, "scene": "memory",   "text": "Three things it observed. Three conclusions it built on top of them." },
    { "start": 21.5,  "dur": 5.0, "scene": "memory",   "text": "Every memory store on the market can write these. Not one of them can take one back." },
    { "start": 26.5,  "dur": 3.5, "scene": "memory",   "text": "Retraction needs transactions, foreign keys, and time travel." },

    { "start": 30.0,  "dur": 5.0, "scene": "release",  "text": "No vector database has any of the three. CockroachDB has all three." },
    { "start": 35.0,  "dur": 3.0, "scene": "release",  "text": "Right now, the agent says: release." },

    { "start": 38.0,  "dur": 4.0, "scene": "recall",   "text": "" },

    { "start": 42.0,  "dur": 2.5, "scene": "cascade",  "text": "One certificate withdrawn." },
    { "start": 44.5,  "dur": 3.5, "scene": "cascade",  "text": "Two conclusions built on it came down with it." },
    { "start": 48.0,  "dur": 4.0, "scene": "cascade",  "text": "One decision already given to a human, flagged for review." },
    { "start": 52.0,  "dur": 4.0, "scene": "cascade",  "text": "One transaction. All of it, or none of it." },

    { "start": 56.0,  "dur": 3.5, "scene": "refused",  "text": "Same lot. Same question. Asked again." },
    { "start": 59.5,  "dur": 2.5, "scene": "refused",  "text": "The agent refuses." },
    { "start": 62.0,  "dur": 3.0, "scene": "refused",  "text": "Not because a model changed its mind." },
    { "start": 65.0,  "dur": 5.5, "scene": "refused",  "text": "Because it can now find only one live supporting memory, and the threshold is two." },
    { "start": 70.5,  "dur": 5.0, "scene": "refused",  "text": "Retraction didn't hide a row. It changed what the agent is able to conclude." },

    { "start": 75.5,  "dur": 3.5, "scene": "replay",   "text": "And it can still prove what it used to know." },
    { "start": 79.0,  "dur": 2.5, "scene": "replay",   "text": "This is not a reconstruction." },
    { "start": 81.5,  "dur": 3.5, "scene": "replay",   "text": "The decision stored the cluster's hybrid logical clock," },
    { "start": 85.0,  "dur": 4.5, "scene": "replay",   "text": "so this reads the exact snapshot the agent read at 3:04." },

    { "start": 89.5,  "dur": 8.0, "scene": "hold",     "text": "" },

    { "start": 97.5,  "dur": 3.5, "scene": "index",    "text": "One detail, because it is why this works at all." },
    { "start": 101.0, "dur": 6.0, "scene": "index",    "text": "The retracted flag is a computed column, and a prefix column of the vector index." },
    { "start": 107.0, "dur": 5.5, "scene": "index",    "text": "CockroachDB will not use a vector index unless every prefix column is constrained." },
    { "start": 112.5, "dur": 4.0, "scene": "index",    "text": "So every single search is forced to say: retracted = false." },
    { "start": 116.5, "dur": 4.0, "scene": "index",    "text": "Retracted memory isn't filtered out. It is unreachable." },

    { "start": 120.5, "dur": 4.5, "scene": "receipt",  "text": "Every test runs against a real CockroachDB cluster, on every push." },
    { "start": 125.0, "dur": 4.5, "scene": "receipt",  "text": "No database mocks. The behaviour only exists in CockroachDB." },
    { "start": 129.5, "dur": 1.5, "scene": "receipt",  "text": "" },

    { "start": 131.0, "dur": 5.5, "scene": "close",    "text": "The buyer is a director of quality assurance at a food or pharma distributor." },
    { "start": 136.5, "dur": 5.0, "scene": "close",    "text": "The budget line is FSMA 204. Compliance date: July 20th, 2028." },
    { "start": 141.5, "dur": 3.5, "scene": "close",    "text": "They cannot deploy an agent into a recall workflow today," },
    { "start": 145.0, "dur": 5.0, "scene": "close",    "text": "because they cannot prove what it knew, and cannot take back what it learned." },
    { "start": 150.0, "dur": 5.5, "scene": "claim",    "text": "When a lot is recalled, Rescind pulls back every conclusion the agent built on it -" },
    { "start": 155.5, "dur": 5.5, "scene": "claim",    "text": "in one transaction, with proof of what the agent knew before and after." },
    { "start": 161.0, "dur": 3.0, "scene": "end",      "text": "" }
  ]
};
