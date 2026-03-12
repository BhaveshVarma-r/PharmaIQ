import uuid
import random
from datetime import datetime
from backend.mcp_servers.base_mcp import BaseMCPServer
from backend.database.sqlite_manager import (
    get_connection, insert_cold_chain_event,
    get_fridge_history, insert_fridge_reading
)
from backend.data.simulators.cold_chain_simulator import (
    generate_fridge_reading, generate_store_fridges
)


class ColdChainMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("COLD_CHAIN_MCP")

    def get_live_reading(self, fridge_id, store_id, force_breach=None):
        reading = generate_fridge_reading(fridge_id, store_id, force_breach)
        insert_fridge_reading(reading)
        if reading["status"] == "BREACH":
            insert_cold_chain_event(reading)
        return self._success("get_live_reading", reading, store_id)

    def get_fridge_history(self, fridge_id, hours=24):
        history = get_fridge_history(fridge_id, hours)
        return self._success("get_fridge_history", {
            "fridge_id": fridge_id,
            "readings": history,
            "count": len(history)
        })

    def get_store_fridges(self, store_id):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT fridge_id,
                   MAX(temperature) as latest_temp,
                   MAX(timestamp) as last_reading
            FROM fridge_readings
            WHERE store_id = ?
            GROUP BY fridge_id
        """, (store_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        if not rows:
            s_conn = get_connection()
            s_c = s_conn.cursor()
            s_c.execute(
                "SELECT fridge_count FROM stores WHERE store_id = ?", (store_id,)
            )
            store = s_c.fetchone()
            s_conn.close()
            fridge_count = store[0] if store else 3
            fridge_ids = generate_store_fridges(store_id, fridge_count)
            rows = [
                {"fridge_id": fid, "latest_temp": None, "last_reading": None}
                for fid in fridge_ids
            ]
        return self._success(
            "get_store_fridges", {"store_id": store_id, "fridges": rows}, store_id
        )

    def quarantine_batch(self, store_id, fridge_id, batch_number, drug_name, reason):
        quarantine_id = "QRN-{}".format(uuid.uuid4().hex[:8].upper())
        result = {
            "quarantine_id": quarantine_id,
            "store_id": store_id,
            "fridge_id": fridge_id,
            "batch_number": batch_number,
            "drug_name": drug_name,
            "reason": reason,
            "status": "QUARANTINED",
            "quarantined_at": datetime.now().isoformat(),
            "erp_reference": "ERP-QRN-{}".format(random.randint(100000, 999999)),
        }
        return self._success("quarantine_batch", result, store_id)

    def get_all_store_statuses(self, limit=20):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT store_id, fridge_id, temperature, timestamp
            FROM fridge_readings
            WHERE timestamp = (
                SELECT MAX(timestamp) FROM fridge_readings fr2
                WHERE fr2.fridge_id = fridge_readings.fridge_id
            )
            LIMIT ?
        """, (limit * 4,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        store_summary = {}
        for row in rows:
            sid = row["store_id"]
            temp = row["temperature"]
            if sid not in store_summary:
                store_summary[sid] = {
                    "fridges": [], "breach_count": 0, "max_temp": temp
                }
            store_summary[sid]["fridges"].append(row)
            if temp > 8.0 or temp < 2.0:
                store_summary[sid]["breach_count"] += 1
            if temp > store_summary[sid]["max_temp"]:
                store_summary[sid]["max_temp"] = temp
        return self._success("get_all_store_statuses", {"stores": store_summary})