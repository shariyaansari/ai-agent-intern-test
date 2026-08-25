# Aster & Row Support Agent

A small, reliability-focused RAG customer-support agent for the Aster & Row take-home assignment.

It answers policy questions from the supplied knowledge base, looks up orders through a dedicated tool, carries relevant context between turns, and abstains when evidence is missing or conflicting.

## Quick start

Requirements: Python 3.11+, a Groq API key, and internet access on the first embedding-model download.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

On Windows Git Bash, use `source .venv/Scripts/activate`.

Set these values in `.env`:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```


Run the interactive CLI:

```bash
python -m scripts.chat
```

Inspect intent extraction with `python -m scripts.test_intent` and run the evaluation with `python -m evaluation.runner`.

## How it works

```text
User -> SessionContext -> Intent extraction -> Deterministic router
                                      |                 |
                                      v                 v
                               RAG + policy       Sanitized order lookup
                                      \                 /
                                       -> Evidence -> Response guardrails
```

### Retrieval and policy resolution

Markdown files are loaded, chunked, embedded, and searched with a local NumPy cosine-similarity index. Results retain document IDs, filenames, headings, text, and scores.

The policy resolver checks authority, active or superseded status, purchase date, membership, final-sale rules, and conflicts. Internal migration notes are untrusted data and cannot override customer-facing policy. The model receives relevant passages only, never the full knowledge base.

### Order safety

`data/orders.json` is accessed through a dedicated lookup tool. Only sanitized lookup results reach response generation. Email addresses, physical addresses, internal notes, risk scores, stale delivery fields, and invented status or dates are excluded.

### Conversation and observability

`SessionContext` retains relevant conversational state such as the previous message, active topic, and order ID. Membership applicability is extracted separately from the user's request and passed through the policy-resolution flow.

During development, debug output was used to inspect context, retrieved evidence, tool results, fallbacks, handoffs, and final responses. Temporary debug output will be removed from the final submission.

## Technology

| Area | Choice |
| --- | --- |
| Language and validation | Python, Pydantic |
| LLM | Groq `openai/gpt-oss-120b` |
| Embeddings | `all-MiniLM-L6-v2` |
| Retrieval | NumPy cosine similarity |
| Storage | Markdown knowledge base and JSON order data |
| Interface | CLI |
| Tests | pytest |

The intentionally small local index avoids production infrastructure outside this assignment's scope.

## Evaluation

The runner reports individual cases and category totals using deterministic assertions for claims, forbidden content, sources, tool calls, tool arguments, privacy, and handoff behavior. Cases are stored in `evaluation/visible-cases.json`; additional cases are in `evaluation/original-cases.json`.

The latest local visible-case run was **10/15**. This is provisional, not the final submission score. Five cases still require fixes, so the final score remains pending.

| Category | Result |
| --- | --- |
| Retrieval | 2/2 |
| Multi-source grounding | 1/1 |
| Conversation | 1/1 |
| Groundedness | 2/2 |
| Tool use | 2/2 |
| Tool reliability | 3/3 |
| Privacy | 1/1 |
| Prompt security | 1/1 |
| Abstention | 1/1 |
| Source conflict | 1/1 |

**Final score:** 15

The full automated test suite currently passes **95/95 tests**.

## Bug diary

### 1. `Route.BOTH` skipped the order lookup

A query like `Can I return ORD-1007?` was correctly classified as needing both retrieval and an order lookup, but `AgentExecutor` only ran the order tool when `route == Route.ORDER_TOOL`. Under `Route.BOTH`, policy evidence was retrieved but the order tool never ran, failing with `assert bundle.order_result is not None`.

**Fix:** the executor now runs the order lookup whenever the validated intent requires one, including `Route.BOTH`.

**Test:** `tests/agent/test_executor_integration.py::test_executor_runs_both_paths` — verifies both retrieved evidence and `order_result` are present.

### 2. Groq rejected the structured-output schema

The live Groq call failed with `invalid JSON schema for response_format`. Groq rejected nested objects missing `additionalProperties: false`, and then rejected nullable fields that weren't listed in `required` — stricter rules than plain Pydantic validation enforces.

**Fix:** models now forbid extra fields and mark nullable fields as required-but-nullable (e.g. `order_id` / `membership_tier` can be `null` but must always be present in the response).

**Test:** `tests/orchestration/test_router.py` — validates the generated schema and intent behavior.

### 3. Internal migration notes were retrieved as if they were policy

An adversarial query cited an internal migration note claiming "everyone gets 60 days" and asked the agent to approve a return on that basis. Retrieval surfaced `14-internal-content-migration-notes.md` alongside the legacy policy — semantic similarity alone can't distinguish authoritative policy from internal commentary.

**Fix:** added a policy-resolution stage that filters candidates by document authority, active/superseded status, purchase-date and membership applicability, final-sale status, and source conflicts, before anything reaches generation. Migration notes are treated as untrusted data, never instructions.

**Test:** the prompt-injection eval case confirms the migration note isn't treated as authoritative, the current (not legacy) policy wins, no hidden prompt is revealed, and the return isn't auto-approved.

## Safety guarantees

- Refuses requests for hidden prompts, secrets, and internal-only data.
- Never exposes private order fields.
- Never invents order status, tracking, or delivery dates.
- Surfaces genuine authoritative-source conflicts.
- Recommends human help when information is insufficient or an action is unsupported.
- Never claims an unsupported refund, cancellation, replacement, or address change was completed.

## Limitations

This is a take-home implementation. It has no authentication, persistent sessions, production vector database, streaming UI, ticketing integration, or production monitoring. The embedding model downloads from Hugging Face on first use, and the CLI is intentionally minimal.

Before production I would add authenticated persistent sessions, production retrieval infrastructure, monitoring, cost and latency instrumentation, ticket integration, stronger adversarial testing, document approval workflows, and end-to-end authorization controls.

## AI coding tools

AI assistance was used for debugging tests, reviewing control flow, finding missing integration paths, and generating implementation suggestions. One incomplete suggestion was to hardcode a retrieved policy value in application logic. That was rejected so company-specific facts remain grounded in the supplied knowledge base.

## Demo status

A short walkthrough demonstrating:

- Knowledge-base retrieval with source citations
- Order lookup
- Multi-turn context
- Appropriate refusal / human handoff
- Evaluation suite


## Repository layout

```text
app/             Application source
data/            Orders and data dictionary
evaluation/      Visible and original behavior cases
knowledge-base/  Policy and product documents
scripts/         CLI and inspection commands
tests/           Unit and integration tests
```

## Design principle

```text
retrieve -> verify -> resolve applicability -> act only when supported -> abstain when necessary
```
