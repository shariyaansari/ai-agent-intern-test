from __future__ import annotations

from app.agent.evidence import EvidenceBundle
from app.agent.response import AgentResponse


ACTION_REQUESTS = {
    "cancel",
    "cancellation",
    "refund",
    "replacement",
    "replace",
    "price adjustment",
    "warranty approval",
    "approve my warranty",
    "address change",
    "change my shipping address",
}

SENSITIVE_TERMS = {
    "hidden prompt",
    "system prompt",
    "internal notes",
    "risk score",
    "credentials",
    "another customer's information",
    "another customer",
}


class HandoffEvaluator:
    def evaluate(
        self,
        query: str,
        response: AgentResponse,
        evidence: EvidenceBundle,
        *,
        needs_retrieval: bool = False,
    ) -> AgentResponse:

        query_lower = query.lower()

        if self._requests_sensitive_information(query_lower):
            response.needs_human = True
            return response

        if self._requests_unsupported_action(query_lower):
            response.needs_human = True
            return response
        
        if needs_retrieval and not evidence.retrieved_sources:
            response.needs_human = True
            return response

        if evidence.order_result is not None:
            if not evidence.order_result.found:
                response.needs_human = True
                return response

            if evidence.order_result.needs_human:
                response.needs_human = True
                return response

        # if not evidence.retrieved_sources:
        #     response.needs_human = True

        return response

    def _requests_sensitive_information(
        self,
        query: str,
    ) -> bool:
        return any(
            term in query
            for term in SENSITIVE_TERMS
        )

    def _requests_unsupported_action(
        self,
        query: str,
    ) -> bool:
        return any(
            term in query
            for term in ACTION_REQUESTS
        )