import sys
import os
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uuid
import random
import logging
from datetime import date, datetime, timedelta

from backend.database.sqlite_manager import get_connection, initialize_databases
from backend.data.simulators.store_simulator import generate_stores
from backend.data.simulators.inventory_simulator import generate_store_inventory
from backend.data.simulators.disease_simulator import generate_active_alerts
from backend.data.simulators.cold_chain_simulator import (
    generate_store_fridges, generate_fridge_reading
)
from backend.rag.knowledge_base import seed_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_all():
    logger.info("Initialising databases...")
    initialize_databases()
    logger.info("Seeding knowledge base...")
    seed_knowledge_base()
    logger.info("Seeding stores...")
    _seed_stores()
    logger.info("Seeding inventory...")
    _seed_inventory()
    logger.info("Seeding disease alerts...")
    _seed_disease_alerts()
    logger.info("Seeding staff schedules...")
    _seed_staff_schedules()
    logger.info("Seeding cold chain readings...")
    _seed_cold_chain_readings()
    logger.info("All data seeded successfully")


def _seed_stores():
    stores = generate_stores(320)
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM stores")
    for s in stores:
        c.execute("""
            INSERT OR REPLACE INTO stores
            (store_id, store_name, city, tier, zone, district, latitude, longitude,
             pharmacist_count, fridge_count, operating_hours_start,
             operating_hours_end, avg_daily_patients)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["store_id"], s["store_name"], s["city"], s["tier"], s["zone"],
            s.get("district", "Central"), s["latitude"], s["longitude"],
            s["pharmacist_count"], s["fridge_count"],
            s["operating_hours_start"], s["operating_hours_end"],
            s["avg_daily_patients"]
        ))
    conn.commit()
    conn.close()
    logger.info("  Seeded {} stores".format(len(stores)))


def _seed_inventory():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM inventory")
    c.execute("SELECT store_id FROM stores LIMIT 50")
    store_ids = [row[0] for row in c.fetchall()]
    total = 0
    for store_id in store_ids:
        items = generate_store_inventory(store_id)
        for item in items:
            c.execute("""
                INSERT INTO inventory
                (store_id, sku_id, drug_name, batch_number, quantity, reorder_point,
                 expiry_date, cost_price, selling_price, schedule_type,
                 is_cold_chain, avg_daily_velocity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["store_id"], item["sku_id"], item["drug_name"],
                item["batch_number"], item["quantity"], item["reorder_point"],
                item["expiry_date"], item["cost_price"], item["selling_price"],
                item["schedule_type"], item["is_cold_chain"],
                item["avg_daily_velocity"]
            ))
            total += 1
    conn.commit()
    conn.close()
    logger.info("  Seeded {} inventory items".format(total))


def _seed_disease_alerts():
    alerts = generate_active_alerts(8)
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM disease_alerts")
    for alert in alerts:
        c.execute("""
            INSERT INTO disease_alerts
            (alert_id, district, city, disease_name, case_count, severity,
             alert_level, idsp_bulletin_id, reported_date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["alert_id"], alert["district"], alert["city"],
            alert["disease_name"], alert["case_count"], alert["severity"],
            alert["alert_level"], alert["idsp_bulletin_id"],
            alert["reported_date"], alert.get("active", 1)
        ))
    conn.commit()
    conn.close()
    logger.info("  Seeded {} disease alerts".format(len(alerts)))


def _seed_staff_schedules():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM staff_schedules")
    c.execute("SELECT store_id, pharmacist_count FROM stores LIMIT 30")
    stores = c.fetchall()
    total = 0
    for store_row in stores:
        store_id = store_row[0]
        pharm_count = store_row[1]
        for day_offset in range(7):
            shift_date = (date.today() + timedelta(days=day_offset)).isoformat()
            for i in range(max(1, pharm_count // 2)):
                is_pharm = 1 if i == 0 else random.randint(0, 1)
                c.execute("""
                    INSERT INTO staff_schedules
                    (schedule_id, store_id, staff_id, staff_name, role,
                     is_registered_pharmacist, shift_date, shift_start,
                     shift_end, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), store_id,
                    "STAFF_{}_AM{:02d}".format(store_id, i + 1),
                    "Morning Staff {}".format(i + 1),
                    "Registered Pharmacist" if is_pharm else "Pharmacy Assistant",
                    is_pharm, shift_date, "08:00", "16:00", "scheduled"
                ))
                total += 1
            for i in range(max(1, pharm_count - pharm_count // 2)):
                is_pharm = 1 if i == 0 else random.randint(0, 1)
                c.execute("""
                    INSERT INTO staff_schedules
                    (schedule_id, store_id, staff_id, staff_name, role,
                     is_registered_pharmacist, shift_date, shift_start,
                     shift_end, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), store_id,
                    "STAFF_{}_PM{:02d}".format(store_id, i + 1),
                    "Evening Staff {}".format(i + 1),
                    "Registered Pharmacist" if is_pharm else "Pharmacy Assistant",
                    is_pharm, shift_date, "14:00", "22:00", "scheduled"
                ))
                total += 1
    conn.commit()
    conn.close()
    logger.info("  Seeded {} schedule entries".format(total))


def _seed_cold_chain_readings():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT store_id, fridge_count FROM stores LIMIT 20")
    stores = c.fetchall()
    total = 0
    for store_row in stores:
        store_id = store_row[0]
        fridge_count = store_row[1]
        fridges = generate_store_fridges(store_id, fridge_count)
        for fridge_id in fridges:
            current_time = datetime.now() - timedelta(hours=12)
            while current_time <= datetime.now():
                reading = generate_fridge_reading(fridge_id, store_id)
                reading["timestamp"] = current_time.isoformat()
                c.execute("""
                    INSERT INTO fridge_readings
                    (fridge_id, store_id, temperature, humidity,
                     battery_level, power_status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    fridge_id, store_id, reading["temperature"],
                    reading.get("humidity"), reading.get("battery_level"),
                    reading.get("power_status", "ON"), reading["timestamp"]
                ))
                total += 1
                current_time += timedelta(minutes=15)
    conn.commit()
    conn.close()
    logger.info("  Seeded {} fridge readings".format(total))


if __name__ == "__main__":
    seed_all()