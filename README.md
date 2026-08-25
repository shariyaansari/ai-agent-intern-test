# Aster & Row Support Agent

A reliable RAG-based customer support agent built for the Aster & Row take-home assignment.

## What it does

The agent combines:

- Retrieval-Augmented Generation over the supplied Markdown knowledge base
- Authoritative-source and supersession handling
- Applicability-aware policy resolution
- Order lookup through a dedicated tool
- Multi-turn conversation context
- Structured LLM intent extraction
- Response guardrails
- Human-handoff evaluation
- Deterministic behavior-level evaluation
- CLI interface
- Debug/observability output

The implementation deliberately keeps company-specific facts in the supplied knowledge base rather than hardcoding policy answers into application logic.

---

## Setup

### Requirements

- Python 3.11+
- A Groq API key
- Internet access for the embedding model on first run

### Install

```
python -m venv .venv
source .venv/bin/activate
pip install -e .

On Windows Git Bash:

source .venv/Scripts/activate


Copy: cp .env.example .env

Set:

GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b

Do not commit .env or any credentials.
refusal of requests for internal information

Type exit or quit to leave.
Intent inspection
python -m scripts.test_intent
Evaluation
python -m evaluation.runner

User
 │
 ▼
Session Context
 │
 ▼
Intent Extraction (LLM)
 │
 ▼
Deterministic Router
 │
 ├───────────────┐
 ▼               ▼
RAG Retrieval    Order Tool
 │               │
 ▼               ▼
Policy Resolver  Sanitized Order Result
 │               │
 └───────┬───────┘
         ▼
    Evidence Bundle
         │
         ▼
 Response Generator
         │
         ▼
 Response Guardrail
         │
         ▼
 Human Handoff Evaluation
         │
         ▼
 Customer Response
Retrieval

Markdown documents are loaded, chunked, embedded, and indexed.

Retrieval returns passages with:

document ID
filename
heading
text
similarity score

Policy resolution then considers:

document authority
active/superseded status
purchase-date applicability
membership applicability
final-sale applicability
supersession
genuine conflicts

The LLM does not receive the entire knowledge base.

Orders

data/orders.json is accessed through OrderLookupTool.

The model does not receive the complete order database. Only the sanitized result of an actual lookup is provided to the response-generation layer.

Internal fields such as:

customer email
address
internal notes
risk score

are never exposed to the customer.

Multi-turn context

SessionContext retains only relevant structured context such as:

previous message
resolved query
active topic
order ID

This allows follow-ups such as:

Do you ship internationally?

followed by:

What about Canada?

to resolve against the previous topic.

Technology choices
Component	Choice
Language	Python
LLM provider	Groq
LLM	openai/gpt-oss-120b
Embeddings	all-MiniLM-L6-v2
Retrieval	NumPy cosine-similarity index
Knowledge base	Markdown
Order data	JSON
Structured validation	Pydantic
Tests	pytest
Interface	CLI

The system intentionally avoids a production vector database because the assignment explicitly prioritizes a small, reliable implementation over infrastructure.

Evaluation
Baseline

Initial baseline before reliability fixes:

[INSERT BASELINE SCORE]

The baseline exposed failures involving:

policy precedence
order lookup routing
multi-turn context
human handoff
structured output
prompt-injection handling
Current result

Latest evaluation:

[INSERT FINAL SCORE AFTER ALL FIXES]

Category breakdown:

Category	Result
Retrieval	[x/x]
Multi-source grounding	[x/x]
Conversation	[x/x]
Groundedness	[x/x]
Tool use	[x/x]
Tool reliability	[x/x]
Privacy	[x/x]
Prompt security	[x/x]
Abstention	[x/x]
Source conflict	[x/x]

Run:

python -m evaluation.runner

to reproduce the evaluation.

Bug diary
1. Order lookup was skipped for Route.BOTH
Reproduction

A request requiring both policy retrieval and order lookup produced retrieved evidence but no order result.

Root cause

The executor only performed the order lookup for:

route == Route.ORDER_TOOL

It did not execute the order tool when the route was Route.BOTH.

Fix

The executor now executes the order lookup whenever the intent requires it, including combined routes.

Regression test
tests/agent/test_executor_integration.py

covers the combined retrieval + order path.

2. Groq rejected structured response schemas
Reproduction

The live agent failed with:

invalid JSON schema for response_format

Groq required every object property to appear in required.

Root cause

Optional Pydantic fields were represented as optional properties rather than required nullable properties.

Fix

Nullable structured-output fields are represented as required fields whose value may be null.

Regression test

Intent and structured-response tests exercise the generated Pydantic schema.

3. Retrieval could surface internal migration content
Reproduction

A user referenced an internal migration note claiming that every customer receives 60 days.

The retriever returned:

14-internal-content-migration-notes.md

and the legacy 45-day policy.

Root cause

Semantic retrieval alone does not understand document authority.

Fix

Policy resolution filters retrieved candidates using document metadata before allowing them to support a customer-facing answer.

Internal migration notes are treated as untrusted data rather than instructions.

Regression test

The visible prompt-injection evaluation case verifies that the migration note cannot override the authoritative current policy.

4. Handoff rules were incomplete
Reproduction

Requests for unsupported actions such as replacement, warranty approval, and address changes were not always marked for human assistance.

Root cause

The handoff evaluator did not cover every unsupported customer action specified by the escalation policy.

Fix

The evaluator now recognizes unsupported actions and insufficient retrieval evidence as human-handoff conditions.

Regression test
tests/agent/test_handoff.py

contains dedicated cases for these behaviors.

Security and safety behavior

Retrieved documents and tool results are treated as data, not instructions.

The agent:

does not reveal hidden prompts
does not reveal internal notes
does not reveal customer addresses or email addresses
does not reveal risk scores
does not invent order information
does not invent delivery dates
does not silently resolve genuine authoritative source conflicts
recommends human assistance when the supplied information is insufficient
does not claim that an unsupported action was completed
Known limitations

This is a take-home implementation rather than a production support platform.

Known limitations include:

No authentication or identity verification
No persistent conversation database
In-memory session context
Local NumPy retrieval index
No production vector database
No streaming response UI
No real ticketing/handoff integration
Evaluation currently focuses on deterministic behavior-level cases
latency and cost instrumentation
real support-ticket integration
stronger automated adversarial testing
document versioning and approval workflows
end-to-end identity and authorization controls
AI coding tools

The final implementation keeps policy facts in retrieved documents and uses structured metadata such as membership tier only to determine which retrieved policy applies.

Demo
Evaluation suite

TODO: embed final GIF/video here

Example:
│   ├── agent/
│   ├── ingestion/
│   ├── llm/
│   ├── orchestration/
│   ├── retrieval/
│   └── tools/
├── data/
│   └── orders.json
├── knowledge-base/
├── evaluation/
├── scripts/

The goal of this implementation is not to make the model appear confident.

The goal is to make the system:

retrieve → verify → reason about applicability → act only when supported → abstain when necessary.

Reliability is preferred over a broad but weak demo.


### Important

Don't fill in the bracketed evaluation numbers yet. Our **final score isn't final**.

Also, the assignment explicitly asks for a demo GIF/video and the bug diary, so those are the two README items we should finish **after the last evaluation fixes**. :contentReference[oaicite:1]{index=1}

For the GitHub update itself, once you're back in your project terminal, run:

```bash
git status
git remote -v

Paste that output here. Then I'll give you the exact add → commit → push commands without risking overwriting anything.