from pathlib import Path

from app.tools import OrderLookupTool


ORDERS_FILE = Path("data/orders.json")


def test_existing_order_is_found():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-1001")

    assert result.found is True
    assert result.order is not None
    assert result.order["order_id"] == "ORD-1001"
    

def test_order_id_is_normalized():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("  ord-1001. ")

    assert result.found is True
    assert result.order["order_id"] == "ORD-1001"

def test_unknown_order_is_not_guessed():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-9999")

    assert result.found is False
    assert result.order is None
    
def test_internal_fields_never_reach_tool_result():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-1001")

    assert result.found is True
    assert result.order is not None

    assert "customer" not in result.order
    assert "internal" not in result.order
    
def test_sensitive_customer_fields_are_not_exposed():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-1001")

    assert result.order is not None

    serialized = str(result.order)

    assert "maya.reed@example.test" not in serialized
    assert "18 Cedar Lane" not in serialized
    assert "risk_score" not in serialized
    assert "warehouse_note" not in serialized
    assert "support_tags" not in serialized

def test_cancelled_status_overrides_stale_delivery_information():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-1004")

    assert result.found is True
    assert result.order["status"] == "cancelled"
    assert result.order["estimated_delivery"] is None
    

def test_shipped_without_estimate_does_not_invent_date():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-1011")

    assert result.found is True
    assert result.order["status"] == "shipped"
    assert result.order["estimated_delivery"] is None
    assert "estimate" in result.order["customer_safe_message"].lower()
    
    
def test_exception_requires_human_review():
    tool = OrderLookupTool(ORDERS_FILE)

    result = tool.lookup("ORD-1010")

    assert result.found is True
    assert result.order["status"] == "exception"
    assert result.needs_human is True