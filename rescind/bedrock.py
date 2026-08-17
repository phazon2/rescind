"""AWS Bedrock: Titan for embeddings, Claude for reasoning.

Offline mode exists so the test suite and CI can run without AWS credentials.
It is deliberately LOUD -- it warns on every call, and every decision it touches
is stamped offline_mode = true in the database. A quiet fallback that silently
produced plausible-looking output would be exactly the kind of unaccountable
behaviour this project argues against.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import warnings
from typing import Sequence

from .config import (
    BEDROCK_EMBED_MODEL,
    BEDROCK_REASONING_MODEL,
    EMBED_DIM,
)

log = logging.getLogger("rescind.bedrock")

# The reasoning contract. Two clauses here are safety-critical:
#
#   * absence of evidence is not evidence of safety -- an agent that reads "no
#     recall notice found" as an all-clear is precisely the failure this project
#     exists to prevent;
#   * the model must not infer anything from facts it was not given, because the
#     facts it was not given may be facts that were retracted.
SYSTEM_PROMPT = """You are a quality-assurance assistant for a food and pharmaceutical distributor.
You advise a human recall coordinator on whether a staged shipment may be released.

Rules you must follow exactly:

1. Reason ONLY from the supporting records supplied to you. Do not use outside
   knowledge about the product, the supplier, or the lot.
2. An empty, silent, or incomplete record set DOES NOT clear a lot. Absence of
   evidence is not evidence of safety. If the records do not positively
   establish that the lot is safe to ship, answer "hold".
3. Records may have been withdrawn before you were asked. If the evidence looks
   thin, answer "hold" and say what is missing.
4. You advise; you do not act. A human makes the release decision.

Respond with a single JSON object and nothing else:
{"verdict": "release" | "hold", "rationale": "<one or two sentences>"}"""


class OfflineMode(UserWarning):
    """Raised as a warning whenever a deterministic stand-in is used for Bedrock."""


def offline_forced() -> bool:
    return os.environ.get("RESCIND_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def _warn_offline(what: str, detail: str = "") -> None:
    message = (
        f"RESCIND OFFLINE MODE: {what} is a deterministic local stand-in, NOT AWS "
        f"Bedrock. Results are reproducible but carry no semantic authority. {detail}".strip()
    )
    warnings.warn(message, OfflineMode, stacklevel=3)
    log.warning(message)


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


def _normalise(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        # A zero vector would sit at a constant distance from everything, which
        # would quietly defeat the support threshold. Refuse instead.
        raise ValueError("cannot normalise a zero embedding")
    return [v / norm for v in vec]


def offline_embedding(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Deterministic hashed bag-of-tokens embedding, unit-normalised.

    Same text always yields the same vector, and lexically similar texts land
    closer together, which is enough to exercise the retrieval and threshold
    paths. It is NOT semantic. See docs/LIMITS.md.
    """
    vec = [0.0] * dim
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    if not tokens:
        raise ValueError("cannot embed empty text")
    for token in tokens:
        for salt in range(3):
            digest = hashlib.sha256(f"{token}:{salt}".encode()).digest()
            idx = int.from_bytes(digest[:4], "big") % dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[idx] += sign
    return _normalise(vec)


def embed(text: str, client=None) -> list[float]:
    """Embed text with Titan, falling back loudly to a deterministic stand-in."""
    if offline_forced():
        _warn_offline("embedding", "RESCIND_OFFLINE is set.")
        return offline_embedding(text)

    try:
        client = client or _runtime()
        response = client.invoke_model(
            modelId=BEDROCK_EMBED_MODEL,
            body=json.dumps({"inputText": text, "dimensions": EMBED_DIM, "normalize": True}),
        )
        payload = json.loads(response["body"].read())
        vector = payload["embedding"]
        if len(vector) != EMBED_DIM:
            raise ValueError(
                f"{BEDROCK_EMBED_MODEL} returned {len(vector)} dimensions, "
                f"schema expects {EMBED_DIM}"
            )
        return [float(v) for v in vector]
    except Exception as exc:  # noqa: BLE001 - we want every failure to be loud
        _warn_offline("embedding", f"Bedrock call failed: {type(exc).__name__}: {exc}")
        return offline_embedding(text)


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------


def offline_reasoning(question: str, supporting: Sequence[str]) -> dict:
    """Deterministic stand-in for Claude.

    Fails closed in the same direction the real prompt does: it will only say
    "release" when the supporting records positively contain a clearing signal,
    and says "hold" otherwise.
    """
    blob = " ".join(supporting).lower()
    clearing = ("passed" in blob or "within specification" in blob or "no findings" in blob)
    blocking = ("recall" in blob or "contamination" in blob or "failed" in blob
                or "positive" in blob or "withdrawn" in blob)

    if blocking or not clearing:
        return {
            "verdict": "hold",
            "rationale": (
                "Offline reasoning: the supporting records do not positively "
                "establish that this lot is safe to ship."
            ),
        }
    return {
        "verdict": "release",
        "rationale": (
            "Offline reasoning: every supporting record for this lot reports a "
            "passing result and none reports a recall or contamination finding."
        ),
    }


def reason(question: str, supporting: Sequence[str], client=None) -> dict:
    """Ask Claude for a release/hold recommendation.

    A malformed model response FAILS CLOSED -- it holds the lot. It never
    invents a verdict, and it never treats an unparseable answer as approval.
    """
    if offline_forced():
        _warn_offline("reasoning", "RESCIND_OFFLINE is set.")
        result = offline_reasoning(question, supporting)
        result["model_id"] = "offline-deterministic"
        result["offline"] = True
        return result

    records = "\n".join(f"- {s}" for s in supporting) or "(no records supplied)"
    user = f"Question from the recall coordinator: {question}\n\nSupporting records:\n{records}"

    try:
        client = client or _runtime()
        response = client.converse(
            modelId=BEDROCK_REASONING_MODEL,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": 400, "temperature": 0.0},
        )
        text = response["output"]["message"]["content"][0]["text"]
        parsed = _parse_verdict(text)
        parsed["model_id"] = BEDROCK_REASONING_MODEL
        parsed["offline"] = False
        return parsed
    except _MalformedVerdict as exc:
        # Reached Bedrock, could not trust the answer. Hold, loudly.
        log.error("Bedrock returned an unusable verdict, holding the lot: %s", exc)
        return {
            "verdict": "hold",
            "rationale": (
                "The reasoning model returned a response that could not be parsed "
                "into a verdict. Holding the lot for human review."
            ),
            "model_id": BEDROCK_REASONING_MODEL,
            "offline": False,
        }
    except Exception as exc:  # noqa: BLE001
        _warn_offline("reasoning", f"Bedrock call failed: {type(exc).__name__}: {exc}")
        result = offline_reasoning(question, supporting)
        result["model_id"] = "offline-deterministic"
        result["offline"] = True
        return result


class _MalformedVerdict(ValueError):
    pass


def _parse_verdict(text: str) -> dict:
    """Extract {verdict, rationale} from a model response, strictly."""
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        raise _MalformedVerdict("no JSON object in response")
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise _MalformedVerdict(f"invalid JSON: {exc}") from exc

    verdict = str(payload.get("verdict", "")).strip().lower()
    if verdict not in {"release", "hold"}:
        raise _MalformedVerdict(f"verdict must be release or hold, got {verdict!r}")
    rationale = str(payload.get("rationale", "")).strip()
    if not rationale:
        raise _MalformedVerdict("empty rationale")
    return {"verdict": verdict, "rationale": rationale}


def _runtime():
    import boto3  # imported lazily so the package works with no AWS SDK present

    return boto3.client(
        "bedrock-runtime",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )
