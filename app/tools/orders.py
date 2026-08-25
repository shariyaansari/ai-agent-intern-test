from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from enum import Enum





ORDER_ID_PATTERN = re.compile(
    r"^ORD-\d+$",
    re.IGNORECASE,
)

CUSTOMER_SAFE_FIELDS = {
    "order_id",
    "membership_tier",
    "items",
    "placed_at",
    "status",
    "status_updated_at",
    "shipped_at",
    "delivered_at",
    "carrier",
    "tracking_number",
    "estimated_delivery",
    "customer_safe_message",
}

class OrderStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    EXCEPTION = "exception"


@dataclass
class OrderLookupResult:
    found: bool
    order: dict[str, Any] | None = None
    error: str | None = None
    needs_human: bool = False
    
class OrderLookupTool:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.orders, self.snapshot_at = self._load_orders()

    def _load_orders(
        self,
    ) -> tuple[dict[str, dict[str, Any]], str | None]:

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        # Use the branch matching your actual orders.json structure.
        if isinstance(data, list):
            orders = data
            snapshot_at = None

        elif isinstance(data, dict):
            orders = data["orders"]
            snapshot_at = data.get("snapshot_at")

        else:
            raise ValueError(
                "Unsupported orders.json structure."
            )

        return (
            {
                order["order_id"]: order
                for order in orders
            },
            snapshot_at,
        )
    
    def normalize_order_id(
        self,
        order_id: str,
    ) -> str:

        normalized = order_id.strip().upper()

        # Handle ordinary punctuation.
        normalized = normalized.rstrip(
            ".,!?;:"
        )

        if not ORDER_ID_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Invalid order ID format."
            )

        return normalized
    
    def _sanitize_order(
        self,
        order: dict[str, Any],
    ) -> dict[str, Any]:

        sanitized = {
            key: order[key]
            for key in CUSTOMER_SAFE_FIELDS
            if key in order
        }

        if "items" in sanitized:
            sanitized["items"] = [
                {
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "final_sale": item.get("final_sale"),
                }
                for item in sanitized["items"]
            ]

        return apply_status_precedence(sanitized)
    
    def lookup(
        self,
        order_id: str,
    ) -> OrderLookupResult:

        try:
            normalized_id = self.normalize_order_id(order_id)
        except ValueError as exc:
            return OrderLookupResult(
                found=False,
                error=str(exc),
            )

        order = self.orders.get(normalized_id)

        if order is None:
            return OrderLookupResult(
                found=False,
                error="Order not found.",
            )

        sanitized = self._sanitize_order(order)

        return OrderLookupResult(
            found=True,
            order=sanitized,
            needs_human=(
                sanitized.get("status") == "exception"
            ),
        )
        
def apply_status_precedence(
    order: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply the authoritative order status rules.

    The raw operational fields remain hidden from the customer.
    """

    status = order.get("status")

    if status in {
        OrderStatus.CANCELLED.value,
        OrderStatus.RETURNED.value,
    }:
        order["estimated_delivery"] = None
        order["tracking_number"] = None

    elif (
        status == OrderStatus.SHIPPED.value
        and order.get("estimated_delivery") is None
    ):
        order["customer_safe_message"] = (
            "The order has shipped, but an estimated "
            "delivery date is currently unavailable."
        )

    return order
        
