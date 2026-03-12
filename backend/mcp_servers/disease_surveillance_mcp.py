from backend.mcp_servers.base_mcp import BaseMCPServer
from backend.database.sqlite_manager import get_connection, get_active_disease_alerts
from backend.data.simulators.disease_simulator import (
    generate_disease_alert, DISEASE_PROFILES
)


class DiseaseSurveillanceMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("DISEASE_SURVEILLANCE_MCP")

    def get_active_alerts(self, city=None, district=None):
        alerts = get_active_disease_alerts(city)
        if district:
            alerts = [a for a in alerts if a.get("district") == district]
        return self._success("get_active_alerts", {
            "alerts": alerts,
            "count": len(alerts),
            "query": {"city": city, "district": district}
        })

    def get_stores_in_alert_zone(self, alert_id):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM disease_alerts WHERE alert_id = ?", (alert_id,))
        alert = c.fetchone()
        if not alert:
            conn.close()
            return self._error(
                "get_stores_in_alert_zone",
                "Alert {} not found".format(alert_id)
            )
        alert_dict = dict(alert)
        city = alert_dict["city"]
        c.execute("SELECT * FROM stores WHERE city = ?", (city,))
        stores = [dict(r) for r in c.fetchall()]
        conn.close()
        return self._success("get_stores_in_alert_zone", {
            "alert": alert_dict,
            "affected_stores": stores,
            "store_count": len(stores)
        })

    def get_disease_sku_mapping(self, disease_name):
        disease_lower = disease_name.lower()
        profile = DISEASE_PROFILES.get(disease_lower)
        if not profile:
            return self._error(
                "get_disease_sku_mapping",
                "Unknown disease: {}".format(disease_name)
            )
        return self._success("get_disease_sku_mapping", {
            "disease": disease_name,
            "affected_skus": profile["affected_skus"],
            "demand_multiplier_range": profile["demand_multiplier_range"],
        })

    def inject_test_alert(self, city, disease, alert_level="ALERT"):
        alert = generate_disease_alert(
            city=city, disease=disease, alert_level=alert_level
        )
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO disease_alerts
            (alert_id, district, city, disease_name, case_count, severity,
             alert_level, idsp_bulletin_id, reported_date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["alert_id"], alert["district"], alert["city"],
            alert["disease_name"], alert["case_count"], alert["severity"],
            alert["alert_level"], alert["idsp_bulletin_id"],
            alert["reported_date"], 1
        ))
        conn.commit()
        conn.close()
        return self._success("inject_test_alert", alert)