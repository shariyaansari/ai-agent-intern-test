from app.agent.executor import AgentExecutor
from app.orchestration.router import (
    Intent,
    RequestType,
    Route,
)


class FakeIndex:
    def search_text(
        self,
        query,
        model,
        top_k=5,
    ):
        return []
    
class FakeOrderTool:
    def __init__(self):
        self.called_with = None

    def lookup(self, order_id):
        self.called_with = order_id

        return type(
            "FakeOrderResult",
            (),
            {
                "found": True,
                "order": {
                    "order_id": order_id,
                    "status": "pending",
                },
                "error": None,
                "needs_human": False,
            },
        )()
        
def test_order_route_calls_only_order_tool():
    order_tool = FakeOrderTool()

    executor = AgentExecutor(
        retrieval_index=FakeIndex(),
        embedding_model=None,
        order_tool=order_tool,
    )

    intent = Intent(
        request_type=RequestType.ORDER,
        needs_retrieval=False,
        needs_order_lookup=True,
        order_id="ORD-1007",
    )

    bundle = executor.execute(
        route=Route.ORDER_TOOL,
        query="Where is ORD-1007?",
        intent=intent,
    )

    assert order_tool.called_with == "ORD-1007"
    assert bundle.order_result is not None
    assert bundle.retrieved_sources == []
    
def test_retrieval_route_does_not_call_order_tool():
    order_tool = FakeOrderTool()

    executor = AgentExecutor(
        retrieval_index=FakeIndex(),
        embedding_model=None,
        order_tool=order_tool,
    )

    intent = Intent(
        request_type=RequestType.POLICY,
        needs_retrieval=True,
        needs_order_lookup=False,
    )

    bundle = executor.execute(
        route=Route.RETRIEVAL,
        query="What is your return policy?",
        intent=intent,
    )

    assert order_tool.called_with is None
    assert bundle.order_result is None