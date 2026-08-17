"""Tunables for Rescind.

The refusal threshold is a deterministic numeric rule, NOT a model judgement.
It must behave identically on every run so CI can assert on it, and so a
quality director can be told exactly when the agent will decline to answer.
"""

# An answer requires at least this many live supporting facts within
# MAX_SUPPORTING_DISTANCE. Below this, the agent refuses rather than guessing.
MIN_SUPPORTING_FACTS = 2

# L2 distance ceiling for a fact to count as support.
#
# Titan embeddings are unit-normalised, so L2 and cosine are monotonically
# related: L2 = sqrt(2 - 2*cos). 0.55 therefore corresponds to cosine ~= 0.85.
# Only L2 (<->) is index-accelerated in CockroachDB, so L2 is what we use.
MAX_SUPPORTING_DISTANCE = 0.55

# Titan amazon.titan-embed-text-v2:0 with normalize=true.
EMBED_DIM = 1024

# How many candidates to pull from the vector index before threshold filtering.
RETRIEVE_LIMIT = 8

BEDROCK_EMBED_MODEL = "amazon.titan-embed-text-v2:0"
BEDROCK_REASONING_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0"
