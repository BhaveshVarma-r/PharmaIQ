import os
import json
import uuid
import asyncio
import random
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from backend.database.sqlite_manager import (
    initialize_databases, get_all_stores, get_store_by_id,
    get_active_disease_alerts, get_near_expiry_inventory,
    get_audit_log, get_critique_log, get_pending_approvals,
    get_connection, write_audit_log
)
from backend.graph.pharmaiq_graph import run_pharmaiq
from backend.mcp_servers.cold_chain_mcp import ColdChainMCPServer
from backend.mcp_servers.disease_surveillance_mcp import DiseaseSurveillanceMCPServer
from backend.mcp_servers.erp_mcp import ERPMCPServer
from backend.mcp_servers.hrms_mcp import HRMSMCPServer
from backend.mcp_servers.distributor_mcp import DistributorMCPServer
from backend.data.simulators.cold_chain_simulator import (
    generate_fridge_reading, generate_store_fridges
)
from backend.data.simulators.disease_simulator import (
    generate_disease_alert, CITY_DISTRICTS, DISEASE_PROFILES
)
from prompts.registry import registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PharmaIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()

cold_chain_mcp = ColdChainMCPServer()
disease_mcp = DiseaseSurveillanceMCPServer()
erp_mcp = ERPMCPServer()
hrms_mcp = HRMSMCPServer()
distributor_mcp = DistributorMCPServer()


class RunEventRequest(BaseModel):
    event_type: str
    store_id: Optional[str] = None
    fridge_id: Optional[str] = None
    disease_alert: Optional[Dict[str, Any]] = None
    sensor_data: Optional[Dict[str, Any]] = None
    force_breach: Optional[str] = None


class PromptVersionUpdate(BaseModel):
    agent: str
    version: str


class ApprovalAction(BaseModel):
    approval_id: str
    action: str
    reviewer: str
    notes: Optional[str] = None


class InjectAlertRequest(BaseModel):
    city: str
    disease: str
    alert_level: str = "ALERT"


@app.on_event("startup")
async def startup():
    logger.info("PharmaIQ API starting...")
    initialize_databases()
    asyncio.create_task(background_scheduler())
    logger.info("PharmaIQ API ready - background scheduler started")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/stores")
def get_stores(city: Optional[str] = None, tier: Optional[str] = None):
    stores = get_all_stores()
    if city:
        stores = [s for s in stores if s["city"] == city]
    if tier:
        stores = [s for s in stores if s["tier"] == tier]
    return {"stores": stores[:50], "total": len(stores)}


@app.get("/api/stores/{store_id}")
def get_store(store_id: str):
    store = get_store_by_id(store_id)
    if not store:
        raise HTTPException(404, "Store {} not found".format(store_id))
    return store


@app.get("/api/cold-chain/status")
def get_cold_chain_status():
    result = cold_chain_mcp.get_all_store_statuses(limit=20)
    return result.get("data", {})


@app.get("/api/cold-chain/store/{store_id}")
def get_store_cold_chain(store_id: str):
    fridges_result = cold_chain_mcp.get_store_fridges(store_id)
    fridges = fridges_result.get("data", {}).get("fridges", [])
    detailed = []
    for fridge in fridges:
        fridge_id = fridge["fridge_id"]
        reading = cold_chain_mcp.get_live_reading(fridge_id, store_id)
        history = cold_chain_mcp.get_fridge_history(fridge_id, hours=6)
        detailed.append({
            "fridge_id": fridge_id,
            "latest_reading": reading.get("data", {}),
            "history": history.get("data", {}).get("readings", [])[:24],
        })
    return {"store_id": store_id, "fridges": detailed}


@app.get("/api/cold-chain/fridge/{store_id}/{fridge_id}")
def get_fridge_detail(
    store_id: str, fridge_id: str, force_breach: Optional[str] = None
):
    reading = cold_chain_mcp.get_live_reading(fridge_id, store_id, force_breach)
    history = cold_chain_mcp.get_fridge_history(fridge_id, hours=24)
    return {
        "fridge_id": fridge_id,
        "store_id": store_id,
        "current_reading": reading.get("data", {}),
        "history": history.get("data", {}).get("readings", []),
    }


@app.get("/api/disease-alerts")
def get_disease_alerts(city: Optional[str] = None):
    alerts = get_active_disease_alerts(city)
    return {"alerts": alerts, "count": len(alerts)}


@app.post("/api/disease-alerts/inject")
def inject_disease_alert(req: InjectAlertRequest):
    result = disease_mcp.inject_test_alert(req.city, req.disease, req.alert_level)
    return result.get("data", {})


@app.get("/api/inventory/near-expiry")
def get_near_expiry(days: int = 60, store_id: Optional[str] = None):
    items = get_near_expiry_inventory(days)
    if store_id:
        items = [i for i in items if i["store_id"] == store_id]
    total_value = sum(
        (i.get("cost_price", 0) or 0) * i["quantity"] for i in items
    )
    return {
        "items": items[:100],
        "count": len(items),
        "total_value_inr": round(total_value, 2)
    }


@app.get("/api/inventory/store/{store_id}")
def get_store_inventory(store_id: str):
    result = erp_mcp.get_store_inventory(store_id)
    return result.get("data", {})


@app.get("/api/staff/schedule/{store_id}")
def get_staff_schedule(store_id: str, date_str: Optional[str] = None):
    result = hrms_mcp.get_store_schedule(store_id, date_str)
    return result.get("data", {})


@app.get("/api/procurement/orders")
def get_orders(store_id: Optional[str] = None):
    result = distributor_mcp.get_pending_orders(store_id)
    return result.get("data", {})


@app.post("/api/agent/run")
async def run_agent_event(
    req: RunEventRequest, background_tasks: BackgroundTasks
):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": req.event_type,
        "store_id": req.store_id,
        "fridge_id": req.fridge_id,
        "timestamp": datetime.now().isoformat(),
    }

    if req.event_type == "cold_chain_breach":
        if req.sensor_data:
            event["sensor_data"] = req.sensor_data
        else:
            store_id = req.store_id or "MC0001"
            fridge_id = req.fridge_id or "{}_FRIDGE_01".format(store_id)
            reading = generate_fridge_reading(
                fridge_id, store_id,
                req.force_breach or "power_fluctuation"
            )
            event["sensor_data"] = reading
            event["fridge_id"] = fridge_id
    elif req.event_type == "epidemic_alert":
        if req.disease_alert:
            event["disease_alert"] = req.disease_alert
        else:
            alerts = get_active_disease_alerts()
            if alerts:
                event["disease_alert"] = alerts[0]

    background_tasks.add_task(_run_and_broadcast, event)
    return {
        "status": "processing",
        "event_id": event["event_id"],
        "message": "Agent pipeline started"
    }


async def _run_and_broadcast(event):
    event_id = event["event_id"]
    await manager.broadcast({
        "type": "agent_progress",
        "event_id": event_id,
        "status": "started",
        "message": "Planner decomposing event...",
        "timestamp": datetime.now().isoformat(),
    })
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_pharmaiq, event)
        await manager.broadcast({
            "type": "agent_complete",
            "event_id": event_id,
            "status": "complete",
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error("Agent pipeline error: {}".format(e))
        await manager.broadcast({
            "type": "agent_error",
            "event_id": event_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })


@app.get("/api/agent/decisions")
def get_agent_decisions(agent: Optional[str] = None, limit: int = 20):
    conn = get_connection()
    c = conn.cursor()
    if agent:
        c.execute(
            "SELECT * FROM agent_decisions WHERE agent_name = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (agent, limit)
        )
    else:
        c.execute(
            "SELECT * FROM agent_decisions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"decisions": rows, "count": len(rows)}


@app.get("/api/audit/log")
def get_audit(limit: int = 100, event_type: Optional[str] = None):
    logs = get_audit_log(limit, event_type)
    return {"logs": logs, "count": len(logs)}


@app.get("/api/audit/critiques")
def get_critiques(limit: int = 50):
    logs = get_critique_log(limit)
    return {"critiques": logs, "count": len(logs)}


@app.get("/api/audit/approvals")
def get_approvals():
    approvals = get_pending_approvals()
    return {"approvals": approvals, "count": len(approvals)}


@app.post("/api/audit/approvals/action")
def process_approval(req: ApprovalAction):
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute("""
        UPDATE human_approval_queue
        SET status = ?, reviewed_by = ?, reviewed_at = ?, review_notes = ?
        WHERE approval_id = ?
    """, (
        req.action, req.reviewer, datetime.now().isoformat(),
        req.notes, req.approval_id
    ))
    conn.commit()
    conn.close()
    write_audit_log({
        "event_type": "HUMAN_APPROVAL_ACTION",
        "agent_name": req.reviewer,
        "action_description": "Approval {}: {} by {}".format(
            req.approval_id, req.action.upper(), req.reviewer
        ),
        "after_state": {"action": req.action, "notes": req.notes},
    })
    return {
        "status": "ok",
        "approval_id": req.approval_id,
        "action": req.action
    }


@app.get("/api/prompts/registry")
def get_prompt_registry():
    return {
        "active_versions": registry.active_versions,
        "agents": registry.list_agents(),
        "metadata": registry.get_all_active_metadata(),
    }


@app.get("/api/prompts/validate")
def validate_prompts():
    return registry.validate_all_prompts()


@app.post("/api/prompts/version")
def update_prompt_version(req: PromptVersionUpdate):
    try:
        registry.set_active_version(req.agent, req.version)
        write_audit_log({
            "event_type": "PROMPT_VERSION_CHANGE",
            "agent_name": "SYSTEM",
            "action_description": "Prompt version changed: {} to {}".format(
                req.agent, req.version
            ),
            "after_state": {"agent": req.agent, "version": req.version},
        })
        return {"status": "ok", "agent": req.agent, "version": req.version}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/prompts/{agent}/versions")
def get_agent_versions(agent: str):
    versions = registry.list_versions(agent)
    metadata = {}
    for v in versions:
        try:
            metadata[v] = registry.get_metadata(agent, v)
        except Exception:
            metadata[v] = {}
    return {"agent": agent, "versions": versions, "metadata": metadata}


@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    stores = get_all_stores()
    alerts = get_active_disease_alerts()
    near_expiry = get_near_expiry_inventory(60)
    approvals = get_pending_approvals()
    audit = get_audit_log(20)

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) as breach_count FROM cold_chain_events
        WHERE status = 'BREACH'
        AND timestamp > datetime('now', '-24 hours')
    """)
    breach_row = c.fetchone()
    breach_count_24h = breach_row[0] if breach_row else 0

    c.execute("""
        SELECT COUNT(*) FROM agent_decisions
        WHERE created_at > datetime('now', '-24 hours')
    """)
    decision_row = c.fetchone()
    decisions_24h = decision_row[0] if decision_row else 0
    conn.close()

    near_expiry_value = sum(
        (i.get("cost_price", 0) or 0) * i["quantity"] for i in near_expiry
    )

    return {
        "stores": {
            "total": len(stores),
            "tier1": sum(1 for s in stores if s["tier"] == "Tier1"),
            "tier2": sum(1 for s in stores if s["tier"] == "Tier2")
        },
        "cold_chain": {
            "breaches_24h": breach_count_24h,
            "total_fridges": sum(
                s.get("fridge_count", 3) for s in stores[:50]
            )
        },
        "disease_alerts": {
            "active": len(alerts),
            "cities_affected": len(set(a["city"] for a in alerts))
        },
        "inventory": {
            "near_expiry_items": len(near_expiry),
            "near_expiry_value_inr": round(near_expiry_value, 0)
        },
        "agent_activity": {
            "decisions_24h": decisions_24h,
            "pending_approvals": len(approvals)
        },
        "recent_activity": audit[:5],
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def background_scheduler():
    tick = 0
    while True:
        await asyncio.sleep(15)
        tick += 1
        await _tick_sensor_readings()
        if tick % 4 == 0:
            await _tick_inventory_updates()
            await _tick_disease_alert_updates()
        if tick % 20 == 0:
            await _tick_procurement_activity()
            await _tick_expiry_drift()
        if tick % 40 == 0:
            await _tick_random_alert()
        if tick >= 480:
            tick = 0


async def _tick_sensor_readings():
    sample_stores = _get_sample_store_ids(10)
    for store_id in sample_stores:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT fridge_count FROM stores WHERE store_id = ?", (store_id,)
        )
        row = c.fetchone()
        conn.close()
        fridge_count = row[0] if row else 3
        fridges = generate_store_fridges(store_id, fridge_count)
        for fridge_id in fridges:
            reading = generate_fridge_reading(fridge_id, store_id)
            from backend.database.sqlite_manager import (
                insert_fridge_reading, insert_cold_chain_event
            )
            insert_fridge_reading(reading)
            if reading["status"] == "BREACH":
                insert_cold_chain_event(reading)
            await manager.broadcast({
                "type": "sensor_reading",
                "store_id": store_id,
                "fridge_id": fridge_id,
                "temperature": reading["temperature"],
                "humidity": reading.get("humidity"),
                "battery_level": reading.get("battery_level"),
                "status": reading["status"],
                "timestamp": reading["timestamp"],
            })
            if reading["status"] == "BREACH":
                await manager.broadcast({
                    "type": "breach_alert",
                    "store_id": store_id,
                    "fridge_id": fridge_id,
                    "temperature": reading["temperature"],
                    "breach_type": reading.get("breach_type"),
                    "timestamp": reading["timestamp"],
                    "message": "Temperature breach at {}: {}C - {}".format(
                        store_id,
                        reading["temperature"],
                        reading.get("breach_type", "unknown")
                    ),
                })


async def _tick_inventory_updates():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, store_id, sku_id, drug_name, quantity,
               avg_daily_velocity, reorder_point
        FROM inventory
        WHERE quantity > 0
        ORDER BY RANDOM() LIMIT 100
    """)
    items = [dict(r) for r in c.fetchall()]
    updates = []
    low_stock_alerts = []
    for item in items:
        velocity = item.get("avg_daily_velocity", 5.0) or 5.0
        hourly = velocity / 24.0
        consumed = max(0, int(hourly + random.uniform(-0.5, 0.5)))
        if consumed > 0 and item["quantity"] > consumed:
            new_qty = item["quantity"] - consumed
            updates.append((new_qty, item["id"]))
            if (
                new_qty <= item["reorder_point"]
                and item["quantity"] > item["reorder_point"]
            ):
                low_stock_alerts.append({
                    "store_id": item["store_id"],
                    "sku_id": item["sku_id"],
                    "drug_name": item["drug_name"],
                    "quantity": new_qty,
                    "reorder_point": item["reorder_point"],
                })
    if updates:
        c.executemany(
            "UPDATE inventory SET quantity = ?, "
            "last_updated = datetime('now') WHERE id = ?",
            updates
        )
        conn.commit()
    conn.close()
    for alert in low_stock_alerts:
        await manager.broadcast({
            "type": "low_stock_alert",
            "store_id": alert["store_id"],
            "sku_id": alert["sku_id"],
            "drug_name": alert["drug_name"],
            "quantity": alert["quantity"],
            "reorder_point": alert["reorder_point"],
            "message": "Low stock at {}: {} has {} units (reorder at {})".format(
                alert["store_id"], alert["drug_name"],
                alert["quantity"], alert["reorder_point"]
            ),
            "timestamp": datetime.now().isoformat(),
        })
    await manager.broadcast({
        "type": "inventory_update",
        "items_updated": len(updates),
        "low_stock_count": len(low_stock_alerts),
        "timestamp": datetime.now().isoformat(),
    })


async def _tick_disease_alert_updates():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM disease_alerts WHERE active = 1")
    alerts = [dict(r) for r in c.fetchall()]
    conn.close()
    for alert in alerts:
        increment = random.randint(1, 15)
        new_count = alert["case_count"] + increment
        new_level = alert["alert_level"]
        if (
            alert["alert_level"] == "WATCH"
            and new_count > 100
            and random.random() < 0.1
        ):
            new_level = "ALERT"
        elif (
            alert["alert_level"] == "ALERT"
            and new_count > 300
            and random.random() < 0.05
        ):
            new_level = "OUTBREAK"
        should_resolve = random.random() < 0.01
        conn = get_connection()
        c = conn.cursor()
        if should_resolve:
            c.execute(
                "UPDATE disease_alerts SET active = 0 WHERE alert_id = ?",
                (alert["alert_id"],)
            )
            await manager.broadcast({
                "type": "alert_resolved",
                "alert_id": alert["alert_id"],
                "disease": alert["disease_name"],
                "city": alert["city"],
                "message": "Disease alert resolved: {} in {}".format(
                    alert["disease_name"], alert["city"]
                ),
                "timestamp": datetime.now().isoformat(),
            })
        else:
            c.execute("""
                UPDATE disease_alerts
                SET case_count = ?, alert_level = ?, severity = ?
                WHERE alert_id = ?
            """, (new_count, new_level, new_level, alert["alert_id"]))
            if new_level != alert["alert_level"]:
                await manager.broadcast({
                    "type": "alert_escalated",
                    "alert_id": alert["alert_id"],
                    "disease": alert["disease_name"],
                    "city": alert["city"],
                    "old_level": alert["alert_level"],
                    "new_level": new_level,
                    "case_count": new_count,
                    "message": "Alert escalated: {} in {} from {} to {}".format(
                        alert["disease_name"], alert["city"],
                        alert["alert_level"], new_level
                    ),
                    "timestamp": datetime.now().isoformat(),
                })
        conn.commit()
        conn.close()
    await manager.broadcast({
        "type": "disease_update",
        "active_alert_count": len(alerts),
        "timestamp": datetime.now().isoformat(),
    })


async def _tick_procurement_activity():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT order_id, store_id, sku_id, drug_name, quantity_ordered
        FROM procurement_orders
        WHERE status = 'confirmed'
        AND expected_delivery <= date('now')
        LIMIT 5
    """)
    orders_to_deliver = [dict(r) for r in c.fetchall()]
    for order in orders_to_deliver:
        c.execute(
            "UPDATE procurement_orders SET status = 'delivered' "
            "WHERE order_id = ?",
            (order["order_id"],)
        )
        c.execute("""
            UPDATE inventory
            SET quantity = quantity + ?, last_updated = datetime('now')
            WHERE store_id = ? AND sku_id = ?
        """, (
            order["quantity_ordered"], order["store_id"], order["sku_id"]
        ))
        await manager.broadcast({
            "type": "order_delivered",
            "order_id": order["order_id"],
            "store_id": order["store_id"],
            "drug_name": order["drug_name"],
            "quantity": order["quantity_ordered"],
            "message": "Order delivered: {} units of {} to {}".format(
                order["quantity_ordered"],
                order["drug_name"],
                order["store_id"]
            ),
            "timestamp": datetime.now().isoformat(),
        })
    conn.commit()
    conn.close()


async def _tick_expiry_drift():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT store_id, sku_id, drug_name, quantity, expiry_date, cost_price,
               julianday(expiry_date) - julianday('now') as days_remaining
        FROM inventory
        WHERE julianday(expiry_date) - julianday('now') BETWEEN 0 AND 45
        AND quantity > 0 LIMIT 20
    """)
    near_expiry = [dict(r) for r in c.fetchall()]
    c.execute("""
        UPDATE inventory SET quantity = 0, last_updated = datetime('now')
        WHERE expiry_date < date('now') AND quantity > 0
    """)
    expired_count = c.rowcount
    conn.commit()
    conn.close()
    if near_expiry or expired_count > 0:
        await manager.broadcast({
            "type": "expiry_alert",
            "near_expiry_count": len(near_expiry),
            "expired_zeroed": expired_count,
            "sample_items": near_expiry[:3],
            "timestamp": datetime.now().isoformat(),
        })


async def _tick_random_alert():
    city = random.choice(list(CITY_DISTRICTS.keys()))
    disease = random.choice(list(DISEASE_PROFILES.keys()))
    alert = generate_disease_alert(city=city, disease=disease)
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
    await manager.broadcast({
        "type": "new_disease_alert",
        "alert": alert,
        "message": "New IDSP alert: {} cases of {} reported in {}, {}".format(
            alert["case_count"], alert["disease_name"],
            alert["district"], alert["city"]
        ),
        "timestamp": datetime.now().isoformat(),
    })
    logger.info("Auto-injected {} alert in {}".format(disease, city))


def _get_sample_store_ids(count):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT store_id FROM stores ORDER BY RANDOM() LIMIT ?", (count,)
    )
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids if ids else ["MC0001", "MC0002", "MC0003"]


if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app", host="0.0.0.0", port=8000, reload=True
    )