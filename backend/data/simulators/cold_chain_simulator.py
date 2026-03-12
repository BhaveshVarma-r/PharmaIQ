import random
import uuid
from datetime import datetime, timedelta

DRUG_CATALOG_COLD = [
    {"sku_id": "SKU_CC_001", "drug_name": "Insulin Glargine 100U/mL", "schedule": "H"},
    {"sku_id": "SKU_CC_002", "drug_name": "Insulin Aspart 100U/mL", "schedule": "H"},
    {"sku_id": "SKU_CC_003", "drug_name": "Hepatitis B Vaccine 1mL", "schedule": "H"},
    {"sku_id": "SKU_CC_004", "drug_name": "Typhoid Vaccine Vi", "schedule": "H"},
    {"sku_id": "SKU_CC_005", "drug_name": "COVID-19 Vaccine Covishield", "schedule": "H"},
    {"sku_id": "SKU_CC_006", "drug_name": "Adalimumab Injection 40mg", "schedule": "H1"},
    {"sku_id": "SKU_CC_007", "drug_name": "Latanoprost Eye Drops 0.005%", "schedule": "H"},
]

BREACH_SCENARIOS = [
    {"name": "power_fluctuation", "deviation": 3.5, "duration_min": 45, "probability": 0.05},
    {"name": "door_left_open", "deviation": 6.0, "duration_min": 20, "probability": 0.03},
    {"name": "compressor_fault", "deviation": 12.0, "duration_min": 180, "probability": 0.01},
    {"name": "brief_spike", "deviation": 2.0, "duration_min": 10, "probability": 0.08},
    {"name": "summer_overload", "deviation": 4.5, "duration_min": 90, "probability": 0.04},
]


def generate_fridge_reading(fridge_id, store_id, force_breach=None):
    base_temp = 5.0
    battery = round(random.uniform(85.0, 100.0), 1)
    humidity = round(random.uniform(40.0, 60.0), 1)
    breach_scenario = None
    if force_breach:
        breach_scenario = next(
            (s for s in BREACH_SCENARIOS if s["name"] == force_breach), None
        )
    else:
        for scenario in BREACH_SCENARIOS:
            if random.random() < scenario["probability"]:
                breach_scenario = scenario
                break
    if breach_scenario:
        temperature = round(
            base_temp + breach_scenario["deviation"] + random.uniform(-0.5, 0.5), 1
        )
        status = "BREACH"
        breach_type = breach_scenario["name"]
        duration = breach_scenario["duration_min"]
    else:
        temperature = round(base_temp + random.uniform(-1.5, 1.5), 1)
        temperature = max(2.5, min(7.5, temperature))
        status = "NORMAL"
        breach_type = None
        duration = 0
    return {
        "event_id": str(uuid.uuid4()),
        "fridge_id": fridge_id,
        "store_id": store_id,
        "temperature": temperature,
        "humidity": humidity,
        "battery_level": battery,
        "power_status": "ON",
        "status": status,
        "breach_type": breach_type,
        "breach_duration_minutes": duration,
        "drugs_at_risk": _select_drugs_at_risk(3),
        "timestamp": datetime.now().isoformat(),
    }


def generate_store_fridges(store_id, fridge_count):
    return ["{}_FRIDGE_{:02d}".format(store_id, i + 1) for i in range(fridge_count)]


def _select_drugs_at_risk(count):
    selected = random.sample(DRUG_CATALOG_COLD, min(count, len(DRUG_CATALOG_COLD)))
    return [
        {
            "sku_id": d["sku_id"],
            "drug_name": d["drug_name"],
            "batch_number": "BATCH{}".format(random.randint(10000, 99999)),
            "quantity": random.randint(10, 150),
            "schedule": d["schedule"],
        }
        for d in selected
    ]


def generate_temperature_history(fridge_id, store_id, hours=24):
    readings = []
    current_time = datetime.now() - timedelta(hours=hours)
    while current_time <= datetime.now():
        reading = generate_fridge_reading(fridge_id, store_id)
        reading["timestamp"] = current_time.isoformat()
        readings.append(reading)
        current_time += timedelta(minutes=15)
    return readings