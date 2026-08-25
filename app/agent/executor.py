# from __future__ import annotations

# from pathlib import Path

# from app.agent.evidence import (
#     EvidenceBundle,
#     RetrievedEvidence,
# )
# from app.ingestion import EmbeddingIndex
# from app.tools.orders import OrderLookupTool
# from app.orchestration.router import (
#     Intent,
#     Route,
# )


# class AgentExecutor:
#     """
#     Executes the capabilities selected by the router.

#     It does not generate the final customer answer.
#     """

#     def __init__(
#         self,
#         retrieval_index: EmbeddingIndex,
#         embedding_model,
#         order_tool: OrderLookupTool,
#     ) -> None:
#         self.retrieval_index = retrieval_index
#         self.embedding_model = embedding_model
#         self.order_tool = order_tool

#     def execute(
#         self,
#         *,
#         route: Route,
#         query: str,
#         intent: Intent,
#     ) -> EvidenceBundle:

#         bundle = EvidenceBundle()

#         if route in {
#             Route.RETRIEVAL,
#             Route.BOTH,
#         }:
#             bundle.retrieved_sources = self._retrieve(
#                 query
#             )

#         if (
#             route == Route.ORDER_TOOL
#             and intent.order_id
#         ):
#             if not intent.order_id:
#                 return bundle

#             bundle.order_result = self.order_tool.lookup(
#                 intent.order_id
#             )

#         return bundle
    
#     def _retrieve(
#         self,
#         query: str,
#     ) -> list[RetrievedEvidence]:

#         results = self.retrieval_index.search_text(
#             query=query,
#             model=self.embedding_model,
#             top_k=5,
#         )

#         return [
#             RetrievedEvidence(
#                 document_id=result.chunk.document_id,
#                 filename=result.chunk.filename,
#                 heading=result.chunk.heading,
#                 text=result.chunk.text,
#                 score=result.score,
#             )
#             for result in results
#         ]

from __future__ import annotations

from app.agent.evidence import (
    EvidenceBundle,
    RetrievedEvidence,
)
from app.ingestion import EmbeddingIndex
from app.retrieval import (
    ApplicabilityContext,
    ResolutionStatus,
    resolve_policy,
)
from app.tools.orders import OrderLookupTool
from app.orchestration.router import (
    Intent,
    Route,
)


class AgentExecutor:
    """
    Executes the capabilities selected by the router.

    It does not generate the final customer answer.
    """

    def __init__(
        self,
        retrieval_index: EmbeddingIndex,
        embedding_model,
        order_tool: OrderLookupTool,
    ) -> None:
        self.retrieval_index = retrieval_index
        self.embedding_model = embedding_model
        self.order_tool = order_tool

    def execute(
        self,
        *,
        route: Route,
        query: str,
        intent: Intent,
        applicability_context: ApplicabilityContext | None = None,
    ) -> EvidenceBundle:

        bundle = EvidenceBundle()

        if route in {
            Route.RETRIEVAL,
            Route.BOTH,
        }:
            bundle.retrieved_sources = self._retrieve(
                query,
                applicability_context=applicability_context,
            )

        if (
            route in {
                Route.ORDER_TOOL,
                Route.BOTH,
            }
            and intent.order_id
        ):
            bundle.order_result = self.order_tool.lookup(
                intent.order_id
            )

        return bundle

    def _retrieve(
        self,
        query: str,
        *,
        applicability_context: ApplicabilityContext | None = None,
    ) -> list[RetrievedEvidence]:

        results = self.retrieval_index.search_text(
            query=query,
            model=self.embedding_model,
            top_k=10,
        )

        resolution = resolve_policy(
            results,
            context=applicability_context,
        )

        if resolution.status == ResolutionStatus.INSUFFICIENT:
            return []

        return [
            RetrievedEvidence(
                document_id=source.chunk.document_id,
                filename=source.chunk.filename,
                heading=source.chunk.heading,
                text=source.chunk.text,
                score=next(
                    (
                        result.score
                        for result in results
                        if result.chunk.chunk_id == source.chunk.chunk_id
                    ),
                    0.0,
                ),
            )
            for source in resolution.sources
        ]