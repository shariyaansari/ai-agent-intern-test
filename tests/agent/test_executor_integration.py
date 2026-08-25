from pathlib import Path

from app.agent.executor import AgentExecutor
from app.orchestration.router import (
    Intent,
    RequestType,
    Route,
)
from app.tools import OrderLookupTool


ORDERS_FILE = Path("data/orders.json")

def test_executor_returns_retrieved_evidence(
    retrieval_index,
    embedding_model,
):
    order_tool = OrderLookupTool(ORDERS_FILE)

    executor = AgentExecutor(
        retrieval_index=retrieval_index,
        embedding_model=embedding_model,
        order_tool=order_tool,
    )

    intent = Intent(
        request_type=RequestType.POLICY,
        needs_retrieval=True,
        needs_order_lookup=False,
    )

    bundle = executor.execute(
        route=Route.RETRIEVAL,
        query="What is the return policy?",
        intent=intent,
    )

    assert bundle.order_result is None
    assert bundle.retrieved_sources

    assert all(
        source.document_id
        for source in bundle.retrieved_sources
    )
    
def test_executor_runs_both_paths(
    retrieval_index,
    embedding_model,
):
    order_tool = OrderLookupTool(ORDERS_FILE)

    executor = AgentExecutor(
        retrieval_index=retrieval_index,
        embedding_model=embedding_model,
        order_tool=order_tool,
    )

    intent = Intent(
        request_type=RequestType.POLICY,
        needs_retrieval=True,
        needs_order_lookup=True,
        order_id="ORD-1007",
    )

    bundle = executor.execute(
        route=Route.BOTH,
        query="Can I return ORD-1007?",
        intent=intent,
    )

    assert bundle.retrieved_sources
    assert bundle.order_result is not None
    assert bundle.order_result.found is True
    assert bundle.order_result.order["order_id"] == "ORD-1007"