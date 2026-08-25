from __future__ import annotations

from app.agent.evidence import EvidenceBundle
from app.agent.generator import ResponseGenerator
from app.agent.response import AgentResponse
from app.retrieval import ApplicabilityContext
from app.agent.executor import AgentExecutor
from app.agent.handoff import HandoffEvaluator
from app.agent.guardrail import ResponseGuardrail
from app.llm import GroqClient
from app.orchestration import (
    SessionContext,
    orchestrate,
    update_session_context,
)


class SupportAgent:
    def __init__(
        self,
        executor: AgentExecutor,
        llm: GroqClient,
    ) -> None:
        self.executor = executor
        self.llm = llm
        self.generator = ResponseGenerator(llm)
        self.guardrail = ResponseGuardrail()
        self.handoff = HandoffEvaluator()
        self.last_evidence = None
        
    def respond(
        self,
        message: str,
        session: SessionContext,
    ) -> AgentResponse:

        # 1. Context → Intent → Router
        orchestration = orchestrate(
            message,
            session,
            self.llm,
        )

        # 2. Execute the selected capability
        evidence = self.executor.execute(
            route=orchestration.route.route,
            query=orchestration.context.resolved_query,
            intent=orchestration.intent,
            applicability_context=ApplicabilityContext(
                membership_tier=orchestration.intent.membership_tier,
                request_type=orchestration.intent.request_type.value,
            ),
        )
        
        self.last_evidence = evidence
        # print("\n--- DEBUG EVIDENCE ---")

        # for source in evidence.retrieved_sources:
        #     print(
        #         source.filename,
        #         "|",
        #         source.heading,
        #         "|",
        #         source.text[:300],
        #     )

        # print("--- END DEBUG ---\n")
        if (
            orchestration.intent.needs_order_lookup
            and not orchestration.intent.order_id
        ):
            response = AgentResponse(
                answer="Please provide your order ID so I can check the status of your order.",
                sources=[],
                needs_human=False,
            )

            update_session_context(
                session,
                user_message=message,
                resolved_query=orchestration.context.resolved_query,
                topic=orchestration.context.topic,
                order_id=orchestration.context.order_id,
            )

            return response
        
        
        # 3. Generate grounded response
        response = self.generator.generate(
            query=orchestration.context.resolved_query,
            evidence=evidence,
        )
        
        response = self.guardrail.validate(
            response,
            evidence,
        )
        
        response = self.handoff.evaluate(
            query=orchestration.context.resolved_query,
            response=response,
            evidence=evidence,
            needs_retrieval=orchestration.intent.needs_retrieval,
        )

        # 4. Update session for the next turn
        update_session_context(
            session,
            user_message=message,
            resolved_query=orchestration.context.resolved_query,
            topic=orchestration.context.topic,
            order_id=orchestration.context.order_id,
        )

        return response