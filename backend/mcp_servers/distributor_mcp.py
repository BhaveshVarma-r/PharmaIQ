import uuid
import random
from datetime import datetime, date, timedelta
from backend.mcp_servers.base_mcp import BaseMCPServer
from backend.database.sqlite_manager import get_connection

DISTRIBUTORS = [
    {"id": "DIST_001", "name": "MedSupply India Pvt Ltd", "lead_time_days": 2, "premium_rate": 0.0},
    {"id": "DIST_002", "name": "PharmaDirect Wholesale", "lead_time_days": 1, "premium_rate": 0.08},
    {"id": "DIST_003", "name": "NationalMed Distributors", "lead_time_days": 3, "premium_rate": 0.0},
    {"id": "DIST_004", "name": "QuickMed Emergency Supply", "lead_time_days": 1, "premium_rate": 0.15},
]


class DistributorMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("DISTRIBUTOR_MCP")

    def check_stock_availability(self, sku_id, quantity, distributor_id=None):
        available_qty = random.randint(quantity // 2, quantity * 5)
        available = available_qty >= quantity
        distributor = next(
            (d for d in DISTRIBUTORS if d["id"] == distributor_id),
            DISTRIBUTORS[0]
        ) if distributor_id else DISTRIBUTORS[0]
        return self._success("check_stock_availability", {
            "sku_id": sku_id,
            "requested_quantity": quantity,
            "available_quantity": available_qty,
            "available": available,
            "distributor": distributor["name"],
            "lead_time_days": distributor["lead_time_days"],
            "unit_price_inr": round(random.uniform(10, 1000), 2),
        })

    def create_procurement_order(
        self, store_id, sku_id, drug_name, quantity,
        order_type, reason, distributor_id=None, unit_cost=None
    ):
        distributor = next(
            (d for d in DISTRIBUTORS if d["id"] == distributor_id),
            DISTRIBUTORS[0]
        )
        if not unit_cost:
            unit_cost = round(random.uniform(10, 1000), 2)
        premium = distributor["premium_rate"] if order_type == "emergency" else 0.0
        effective_cost = unit_cost * (1 + premium)
        total_cost = round(effective_cost * quantity, 2)
        order_id = "ORD-{}".format(uuid.uuid4().hex[:8].upper())
        expected_delivery = (
            date.today() + timedelta(days=distributor["lead_time_days"])
        ).isoformat()
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO procurement_orders
            (order_id, store_id, distributor_id, sku_id, drug_name,
             quantity_ordered, unit_cost, total_cost, order_type,
             reason, status, expected_delivery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id, store_id, distributor["id"], sku_id, drug_name,
            quantity, effective_cost, total_cost, order_type, reason,
            "confirmed", expected_delivery
        ))
        conn.commit()
        conn.close()
        return self._success("create_procurement_order", {
            "order_id": order_id,
            "store_id": store_id,
            "sku_id": sku_id,
            "drug_name": drug_name,
            "quantity": quantity,
            "unit_cost": effective_cost,
            "total_cost": total_cost,
            "distributor": distributor["name"],
            "order_type": order_type,
            "expected_delivery": expected_delivery,
            "premium_applied": "{}%".format(int(premium * 100)),
            "reason": reason,
        }, store_id)

    def get_pending_orders(self, store_id=None):
        conn = get_connection()
        c = conn.cursor()
        if store_id:
            c.execute("""
                SELECT * FROM procurement_orders
                WHERE store_id = ? AND status IN ('pending','confirmed')
                ORDER BY created_at DESC
            """, (store_id,))
        else:
            c.execute("""
                SELECT * FROM procurement_orders
                WHERE status IN ('pending','confirmed')
                ORDER BY created_at DESC LIMIT 50
            """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return self._success(
            "get_pending_orders", {"orders": rows, "count": len(rows)}, store_id
        )