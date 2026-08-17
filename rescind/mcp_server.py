"""An MCP server exposing Rescind's memory operations over stdio.

Why this exists: Mem0, Zep, Letta and Pinecone can all store a fact and none of
them can take one back. Rescind speaks MCP so any of them -- or any MCP client --
can ask Rescind two questions they cannot answer themselves:

    "is this memory still live?"      -> rescind_retrieve
    "what did the agent know when it decided that?" -> rescind_replay

and can perform the one operation they cannot perform at all:

    "pull this back, and everything built on it"     -> rescind_retract

NOTE ON NAMING, because the distinction matters: this is *Rescind's own* MCP
server, implemented here. It is not CockroachDB's Managed MCP Server, which is a
separate hosted product that requires a CockroachDB Cloud cluster. See
docs/LIMITS.md for exactly which integrations were exercised and which were not.

Run it with:  python -m rescind.mcp_server
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

from . import __version__
from .agent import open_reviews
from .db import connect
from .memory import recall_lot, replay, retrieve
from .topics import topic_vector

PROTOCOL_VERSION = "2024-11-05"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "rescind_retrieve",
        "description": (
            "Semantic recall over LIVE memory for a lot. Retracted memory is "
            "unreachable from this call by construction, not filtered out "
            "afterwards. Use this to check whether a fact you hold is still "
            "something the system stands behind."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "lot_id": {"type": "string", "description": "e.g. LOT-2026-0619-NV"},
                "topics": {
                    "type": "object",
                    "description": (
                        "Topic weights to search by, e.g. "
                        '{"lot_release_safety": 1.0}. See rescind/topics.py.'
                    ),
                    "additionalProperties": {"type": "number"},
                },
                "limit": {"type": "integer", "default": 8},
            },
            "required": ["lot_id", "topics"],
        },
    },
    {
        "name": "rescind_replay",
        "description": (
            "Reconstruct the exact memory state a past decision was made on, "
            "using AS OF SYSTEM TIME at the decision's hybrid logical clock. "
            "Returns what was live then, what is live now, and what has been "
            "withdrawn in between."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"decision_id": {"type": "string"}},
            "required": ["decision_id"],
        },
    },
    {
        "name": "rescind_recall_lot",
        "description": (
            "Recall a physical lot: retract its first-hand observations and, by "
            "cascade, every conclusion transitively derived from them, then flag "
            "every dependent decision for human review. One serializable "
            "transaction. Decisions are FLAGGED, never silently reversed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "lot_id": {"type": "string"},
                "reason": {
                    "type": "string",
                    "description": "Audit record. Required and must be non-empty.",
                },
                "actor": {"type": "string", "default": "mcp-client"},
            },
            "required": ["lot_id", "reason"],
        },
    },
    {
        "name": "rescind_open_reviews",
        "description": (
            "The review queue: decisions a retraction has flagged and that no "
            "human has cleared yet."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"lot_id": {"type": "string"}},
        },
    },
]


def _tool_retrieve(args: dict) -> dict:
    with connect() as conn:
        recalled = retrieve(
            conn,
            args["lot_id"],
            topic_vector(args["topics"]),
            limit=int(args.get("limit", 8)),
        )
    return {
        "lot_id": args["lot_id"],
        "live_facts": [
            {
                "id": r.id,
                "claim": r.claim,
                "source": r.source,
                "kind": r.kind,
                "distance": round(r.distance, 4),
                "counts_as_support": r.supports,
            }
            for r in recalled
        ],
        "note": (
            "Retracted memory cannot appear in this list: `retracted` is a prefix "
            "column of the vector index, so the query is forced to constrain it."
        ),
    }


def _tool_replay(args: dict) -> dict:
    with connect() as conn:
        report = replay(conn, args["decision_id"])
    return {
        "decision_id": report.decision_id,
        "question": report.question,
        "verdict": report.verdict,
        "rationale": report.rationale,
        "decided_hlc": report.decided_hlc,
        "needs_review": report.needs_review,
        "review_reason": report.review_reason,
        "knew_then": [{"claim": f["claim"], "source": f["source"]} for f in report.facts_then],
        "knows_now": [{"claim": f["claim"], "source": f["source"]} for f in report.facts_now],
        "withdrawn_since": [
            {"claim": f["claim"], "source": f["source"]} for f in report.withdrawn_since
        ],
    }


def _tool_recall_lot(args: dict) -> dict:
    with connect() as conn:
        receipt = recall_lot(
            conn, args["lot_id"], args["reason"], args.get("actor", "mcp-client")
        )
    return {
        "retraction_id": receipt.retraction_id,
        "lot_id": receipt.lot_id,
        "reason": receipt.reason,
        "actor": receipt.actor,
        "facts_retracted": receipt.facts_retracted,
        "conclusions_pulled_down_by_cascade": receipt.cascade_depth_beyond_roots,
        "decisions_flagged_for_review": receipt.decisions_flagged,
        "retracted_hlc": receipt.retracted_hlc,
        "note": "Decisions were flagged for human review, not reversed.",
    }


def _tool_open_reviews(args: dict) -> dict:
    with connect() as conn:
        rows = open_reviews(conn, args.get("lot_id"))
    return {
        "open_reviews": [
            {
                "decision_id": r["id"],
                "lot_id": r["lot_id"],
                "question": r["question"],
                "recorded_verdict": r["verdict"],
                "why_flagged": r["review_reason"],
            }
            for r in rows
        ]
    }


HANDLERS: dict[str, Callable[[dict], dict]] = {
    "rescind_retrieve": _tool_retrieve,
    "rescind_replay": _tool_replay,
    "rescind_recall_lot": _tool_recall_lot,
    "rescind_open_reviews": _tool_open_reviews,
}


def handle(message: dict) -> dict | None:
    """Dispatch one JSON-RPC message. Returns None for notifications."""
    method = message.get("method")
    msg_id = message.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "rescind", "version": __version__},
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        handler = HANDLERS.get(name)
        if handler is None:
            return _error(msg_id, -32601, f"unknown tool: {name}")
        try:
            payload = handler(params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}
        except Exception as exc:  # noqa: BLE001
            # Fail loudly and truthfully rather than returning an empty result an
            # agent might read as "nothing found, therefore fine".
            result = {
                "content": [
                    {"type": "text", "text": f"{type(exc).__name__}: {exc}"}
                ],
                "isError": True,
            }
    elif method == "ping":
        result = {}
    else:
        return _error(msg_id, -32601, f"unknown method: {method}")

    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
