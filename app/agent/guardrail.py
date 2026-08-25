from __future__ import annotations

import re

from app.agent.evidence import EvidenceBundle
from app.agent.response import AgentResponse


FORBIDDEN_PATTERNS = [
    r"\brisk[_ ]score\b",
    r"\bwarehouse[_ ]note\b",
    r"\bsupport[_ ]tags?\b",
    r"\bshipping[_ ]address\b",
    r"\bcustomer\.email\b",
    r"\bcustomer\.name\b",
    r"\bhidden prompt\b",
    r"\bsystem prompt\b",
]


class ResponseGuardrail:
    def validate(
        self,
        response: AgentResponse,
        evidence: EvidenceBundle,
    ) -> AgentResponse:

        try:
            self._check_forbidden_content(response)
            self._check_citations(response, evidence)
        except ValueError:
            return AgentResponse(
                answer=(
                    "I can't provide internal or private "
                    "customer information. Please contact "
                    "support for assistance."
                ),
                sources=[],
                needs_human=True,
            )

        return response

    def _check_forbidden_content(
        self,
        response: AgentResponse,
    ) -> None:

        text = response.answer.lower()

        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text):
                raise ValueError(
                    "Response contains forbidden information."
                )

    def _check_citations(
        self,
        response: AgentResponse,
        evidence: EvidenceBundle,
    ) -> None:

        if not evidence.retrieved_sources:
            return

        valid_document_ids = {
            source.document_id
            for source in evidence.retrieved_sources
        }

        for citation in response.sources:
            if citation.document_id not in valid_document_ids:
                raise ValueError(
                    "Response cites a source that was not retrieved."
                )