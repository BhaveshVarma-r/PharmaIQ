import uuid
from datetime import datetime
from backend.mcp_servers.base_mcp import BaseMCPServer
from backend.database.sqlite_manager import (
    get_connection, get_inventory_by_store, get_near_expiry_inventory
)


class ERPMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("ERP_MCP")

    def get_store_inventory(self, store_id, sku_filter=None):
        inventory = get_inventory_by_store(store_id)
        if sku_filter:
            inventory = [
                i for i in inventory
                if sku_filter.lower() in i["drug_name"].lower()
            ]
        return self._success("get_store_inventory", {
            "store_id": store_id,
            "inventory": inventory,
            "item_count": len(inventory)
        }, store_id)

    def get_near_expiry_report(self, days_threshold=60):
        items = get_near_expiry_inventory(days_threshold)
        by_store = {}
        total_value = 0
        for item in items:
            sid = item["store_id"]
            if sid not in by_store:
                by_store[sid] = []
            by_store[sid].append(item)
            total_value += (item.get("cost_price", 0) or 0) * item["quantity"]
        return self._success("get_near_expiry_report", {
            "threshold_days": days_threshold,
            "total_items": len(items),
            "total_value_inr": round(total_value, 2),
            "by_store": by_store,
            "items": items
        })

    def update_inventory_quantity(self, store_id, sku_id, new_quantity, reason):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE inventory SET quantity = ?, last_updated = ?
            WHERE store_id = ? AND sku_id = ?
        """, (new_quantity, datetime.now().isoformat(), store_id, sku_id))
        rows_affected = c.rowcount
        conn.commit()
        conn.close()
        return self._success("update_inventory_quantity", {
            "store_id": store_id,
            "sku_id": sku_id,
            "new_quantity": new_quantity,
            "reason": reason,
            "rows_affected": rows_affected
        }, store_id)

    def get_cross_store_inventory(self, sku_id, city=None):
        conn = get_connection()
        c = conn.cursor()
        if city:
            c.execute("""
                SELECT i.*, s.store_name, s.city, s.district
                FROM inventory i
                JOIN stores s ON i.store_id = s.store_id
                WHERE i.sku_id = ? AND s.city = ?
                ORDER BY i.quantity DESC
            """, (sku_id, city))
        else:
            c.execute("""
                SELECT i.*, s.store_name, s.city, s.district
                FROM inventory i
                JOIN stores s ON i.store_id = s.store_id
                WHERE i.sku_id = ?
                ORDER BY i.quantity DESC LIMIT 20
            """, (sku_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return self._success("get_cross_store_inventory", {
            "sku_id": sku_id,
            "city_filter": city,
            "stores_with_stock": rows,
            "count": len(rows)
        })