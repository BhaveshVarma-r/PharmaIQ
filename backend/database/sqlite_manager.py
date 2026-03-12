import sqlite3
import json
import uuid
from datetime import datetime

DB_PATH = "pharmaiq.db"
AUDIT_DB_PATH = "pharmaiq_audit.db"


def get_connection(audit=False):
    path = AUDIT_DB_PATH if audit else DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_databases():
    _init_operational_db()
    _init_audit_db()


def _init_operational_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            store_id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            tier TEXT NOT NULL,
            zone TEXT,
            district TEXT,
            latitude REAL,
            longitude REAL,
            pharmacist_count INTEGER DEFAULT 2,
            fridge_count INTEGER DEFAULT 3,
            operating_hours_start TEXT DEFAULT '08:00',
            operating_hours_end TEXT DEFAULT '22:00',
            avg_daily_patients INTEGER DEFAULT 150,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cold_chain_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            store_id TEXT NOT NULL,
            fridge_id TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL,
            battery_level REAL,
            status TEXT NOT NULL,
            breach_type TEXT,
            breach_duration_minutes REAL,
            drugs_at_risk TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS fridge_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fridge_id TEXT NOT NULL,
            store_id TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL,
            battery_level REAL,
            power_status TEXT DEFAULT 'ON',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            drug_name TEXT NOT NULL,
            batch_number TEXT,
            quantity INTEGER NOT NULL,
            reorder_point INTEGER NOT NULL,
            expiry_date DATE,
            cost_price REAL,
            selling_price REAL,
            schedule_type TEXT DEFAULT 'OTC',
            is_cold_chain INTEGER DEFAULT 0,
            avg_daily_velocity REAL DEFAULT 5.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS disease_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE NOT NULL,
            district TEXT NOT NULL,
            city TEXT NOT NULL,
            disease_name TEXT NOT NULL,
            case_count INTEGER,
            severity TEXT,
            alert_level TEXT,
            idsp_bulletin_id TEXT,
            reported_date DATE NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS staff_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id TEXT UNIQUE NOT NULL,
            store_id TEXT NOT NULL,
            staff_id TEXT NOT NULL,
            staff_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_registered_pharmacist INTEGER DEFAULT 0,
            shift_date DATE NOT NULL,
            shift_start TEXT NOT NULL,
            shift_end TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS procurement_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            store_id TEXT NOT NULL,
            distributor_id TEXT,
            sku_id TEXT NOT NULL,
            drug_name TEXT NOT NULL,
            quantity_ordered INTEGER NOT NULL,
            unit_cost REAL,
            total_cost REAL,
            order_type TEXT DEFAULT 'standard',
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expected_delivery DATE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT UNIQUE NOT NULL,
            agent_name TEXT NOT NULL,
            decision_type TEXT NOT NULL,
            store_id TEXT,
            details TEXT NOT NULL,
            confidence REAL,
            action_taken TEXT,
            requires_human_approval INTEGER DEFAULT 0,
            human_approved INTEGER,
            approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def _init_audit_db():
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id TEXT UNIQUE NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            agent_name TEXT,
            decision_id TEXT,
            store_id TEXT,
            action_description TEXT NOT NULL,
            before_state TEXT,
            after_state TEXT,
            triggered_by TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS critique_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            critique_id TEXT UNIQUE NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            critique_agent TEXT NOT NULL,
            target_agent TEXT NOT NULL,
            target_decision_id TEXT NOT NULL,
            verdict TEXT NOT NULL,
            overall_score REAL,
            dimension_scores TEXT,
            specific_issues TEXT,
            required_modifications TEXT,
            critique_reasoning TEXT,
            critique_confidence REAL,
            escalated_to_human INTEGER DEFAULT 0,
            revision_count INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS human_approval_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approval_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decision_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            action_description TEXT NOT NULL,
            full_context TEXT NOT NULL,
            authority_required TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            review_notes TEXT,
            store_id TEXT,
            urgency TEXT DEFAULT 'HIGH'
        )
    """)
    conn.commit()
    conn.close()


def insert_cold_chain_event(event):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO cold_chain_events
        (event_id, store_id, fridge_id, temperature, humidity, battery_level,
         status, breach_type, breach_duration_minutes, drugs_at_risk, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event["event_id"], event["store_id"], event["fridge_id"],
        event["temperature"], event.get("humidity"), event.get("battery_level"),
        event["status"], event.get("breach_type"),
        event.get("breach_duration_minutes"),
        json.dumps(event.get("drugs_at_risk", [])),
        event.get("timestamp", datetime.now().isoformat())
    ))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def insert_fridge_reading(reading):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO fridge_readings
        (fridge_id, store_id, temperature, humidity, battery_level, power_status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        reading["fridge_id"], reading["store_id"], reading["temperature"],
        reading.get("humidity"), reading.get("battery_level"),
        reading.get("power_status", "ON"),
        reading.get("timestamp", datetime.now().isoformat())
    ))
    conn.commit()
    conn.close()


def get_fridge_history(fridge_id, hours=24):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM fridge_readings
        WHERE fridge_id = ?
        AND timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC LIMIT 200
    """, (fridge_id, hours))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_recent_cold_chain_events(store_id, hours=24):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM cold_chain_events
        WHERE store_id = ?
        AND timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC
    """, (store_id, hours))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_inventory_by_store(store_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory WHERE store_id = ?", (store_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_near_expiry_inventory(days_threshold=60):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT i.*, s.store_name, s.city
        FROM inventory i
        JOIN stores s ON i.store_id = s.store_id
        WHERE i.expiry_date <= date('now', '+' || ? || ' days')
        AND i.expiry_date >= date('now')
        AND i.quantity > 0
        ORDER BY i.expiry_date ASC
    """, (days_threshold,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_active_disease_alerts(city=None):
    conn = get_connection()
    c = conn.cursor()
    if city:
        c.execute(
            "SELECT * FROM disease_alerts WHERE active = 1 AND city = ? ORDER BY created_at DESC",
            (city,)
        )
    else:
        c.execute(
            "SELECT * FROM disease_alerts WHERE active = 1 ORDER BY created_at DESC"
        )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_store_schedules(store_id, date_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM staff_schedules
        WHERE store_id = ? AND shift_date = ? AND status != 'cancelled'
        ORDER BY shift_start
    """, (store_id, date_str))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def insert_agent_decision(decision):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO agent_decisions
        (decision_id, agent_name, decision_type, store_id, details, confidence,
         action_taken, requires_human_approval, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        decision["decision_id"], decision["agent_name"],
        decision["decision_type"], decision.get("store_id"),
        json.dumps(decision.get("details", {})),
        decision.get("confidence"),
        decision.get("action_taken"),
        int(decision.get("requires_human_approval", False)),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_all_stores():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM stores ORDER BY city, store_name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_store_by_id(store_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM stores WHERE store_id = ?", (store_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def write_audit_log(entry):
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute("""
        INSERT INTO audit_log
        (audit_id, event_type, agent_name, decision_id, store_id,
         action_description, before_state, after_state, triggered_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), entry["event_type"],
        entry.get("agent_name"), entry.get("decision_id"),
        entry.get("store_id"), entry["action_description"],
        json.dumps(entry.get("before_state")),
        json.dumps(entry.get("after_state")),
        entry.get("triggered_by", "system")
    ))
    conn.commit()
    conn.close()


def write_critique_log(critique):
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute("""
        INSERT INTO critique_log
        (critique_id, critique_agent, target_agent, target_decision_id,
         verdict, overall_score, dimension_scores, specific_issues,
         required_modifications, critique_reasoning, critique_confidence,
         escalated_to_human, revision_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), critique["critique_agent"],
        critique["target_agent"], critique["target_decision_id"],
        critique["verdict"], critique.get("overall_score"),
        json.dumps(critique.get("dimension_scores", {})),
        json.dumps(critique.get("specific_issues", [])),
        json.dumps(critique.get("required_modifications", [])),
        critique.get("critique_reasoning"),
        critique.get("critique_confidence"),
        int(critique.get("escalate_to_human", False)),
        critique.get("revision_count", 0)
    ))
    conn.commit()
    conn.close()


def add_to_human_approval_queue(item):
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute("""
        INSERT INTO human_approval_queue
        (approval_id, decision_id, agent_name, action_description,
         full_context, authority_required, store_id, urgency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), item["decision_id"], item["agent_name"],
        item["action_description"],
        json.dumps(item.get("full_context", {})),
        item["authority_required"],
        item.get("store_id"), item.get("urgency", "HIGH")
    ))
    conn.commit()
    conn.close()


def get_pending_approvals():
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM human_approval_queue WHERE status = 'pending' ORDER BY created_at DESC"
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_audit_log(limit=100, event_type=None):
    conn = get_connection(audit=True)
    c = conn.cursor()
    if event_type:
        c.execute(
            "SELECT * FROM audit_log WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
            (event_type, limit)
        )
    else:
        c.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_critique_log(limit=50):
    conn = get_connection(audit=True)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM critique_log ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows