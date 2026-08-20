# ADR-0016: Retrieval eval ground truth is a pipeline-independent document span, validated against the filing store, never against Qdrant (2026-08-20)

**Decision**: A retrieval eval dataset's ground truth (`answer_span` / `answer_snippet`,
located by ticker + fiscal year + Item, exact substring of filing text) is defined against
the **filing store** (`sec_text_pipeline`'s `ParsedFiling` JSON), never against a Qdrant
collection produced by either ingest pipeline. The dataset-level validator reads the filing
store only; it has no Qdrant dependency. Ground truth is never a chunk id or a `header_path`
scoped below the Item level.

**Context**: DEV-162 curates a 50-row `sec_retrieval` dataset consumed by two things that
must both trust it equally — the DEV-138 A/B comparison between the frozen HTML pipeline and
the new text pipeline, and the DEV-164 promotion to the standing `sec_retrieval` regression
gate. The existing `validate_sec_eval_dataset.py` script validates the opposite way: it reads
live Qdrant and checks that a chunk with a matching `header_path` exists in whichever
collection is configured. That couples dataset validity to one pipeline's ingest output — if
ground truth were calibrated by querying one arm's Qdrant collection, that arm would start
from a measurement advantage, and the dataset would have no defined meaning once the losing
arm's collection is deleted at sunset (DEV-139).

**Rejected — validate against Qdrant (either or both collections)**: this is what the
existing validator does, and it is the thing DEV-162 exists to stop doing. It cannot produce
an A/B-fair dataset by construction, and it does not survive the HTML pipeline's sunset.

**Rejected — ground truth as a chunk id**: the LlamaIndex-style pattern (`generate_question_context_pairs`,
ground truth = a specific node id) ties the dataset to one chunking policy; a chunker change
invalidates the whole dataset, defeating the entire point of an SSOT shared across pipeline
generations. External retrieval-eval practice that supports genuine A/B (Chroma's chunking
evaluation methodology, FinanceBench's evidence strings) defines ground truth as a
document-level span instead, precisely to stay valid across chunking policies.

**Why**: the filing store (`data/sec_text/{TICKER}/10-K/{YEAR}.json`) is the one artifact
both pipelines' downstream chunkers read from but neither pipeline produces as *output* —
it is parse-stage, upstream of chunking. Anchoring ground truth there is the only anchor
point equidistant from both arms.

**Consequence**: the scorer's *hit* definition (chunk-vs-ground-truth matching) is free to
evolve independently of the dataset — DEV-162's `answer_span` (a full contiguous evidence
region, ≤ ~300 tokens) exists specifically so a future scorer can move from strict
`answer_snippet` substring-containment to span/chunk token-overlap without re-curating the
dataset. See DEV-164.

**Re-evaluate if**: the filing store's schema changes in a way that breaks the (ticker,
fiscal year, Item) → text lookup this validator depends on, or a future dataset needs ground
truth at a granularity the filing store cannot express (e.g., below Item level in a way
`Block` doesn't capture).
