import random
from datetime import date, timedelta

DRUG_CATALOG = [
    {"sku_id": "SKU_CC_001", "drug_name": "Insulin Glargine 100U/mL", "schedule": "H", "is_cold_chain": 1, "cost": 850, "price": 1100},
    {"sku_id": "SKU_CC_002", "drug_name": "Insulin Aspart 100U/mL", "schedule": "H", "is_cold_chain": 1, "cost": 780, "price": 1020},
    {"sku_id": "SKU_CC_003", "drug_name": "Hepatitis B Vaccine 1mL", "schedule": "H", "is_cold_chain": 1, "cost": 180, "price": 250},
    {"sku_id": "SKU_CC_004", "drug_name": "Typhoid Vaccine Vi", "schedule": "H", "is_cold_chain": 1, "cost": 240, "price": 350},
    {"sku_id": "SKU_H_001", "drug_name": "Azithromycin 500mg", "schedule": "H1", "is_cold_chain": 0, "cost": 18, "price": 28},
    {"sku_id": "SKU_H_002", "drug_name": "Amoxicillin 500mg", "schedule": "H", "is_cold_chain": 0, "cost": 8, "price": 14},
    {"sku_id": "SKU_H_003", "drug_name": "Cefixime 200mg", "schedule": "H", "is_cold_chain": 0, "cost": 22, "price": 38},
    {"sku_id": "SKU_H_004", "drug_name": "Metronidazole 400mg", "schedule": "H", "is_cold_chain": 0, "cost": 5, "price": 9},
    {"sku_id": "SKU_H_005", "drug_name": "Ciprofloxacin 500mg", "schedule": "H1", "is_cold_chain": 0, "cost": 12, "price": 22},
    {"sku_id": "SKU_H_006", "drug_name": "Oseltamivir 75mg", "schedule": "H", "is_cold_chain": 0, "cost": 65, "price": 95},
    {"sku_id": "SKU_H_007", "drug_name": "Metformin 500mg", "schedule": "H", "is_cold_chain": 0, "cost": 4, "price": 7},
    {"sku_id": "SKU_H_008", "drug_name": "Atorvastatin 10mg", "schedule": "H", "is_cold_chain": 0, "cost": 6, "price": 11},
    {"sku_id": "SKU_OTC_001", "drug_name": "Paracetamol 650mg", "schedule": "OTC", "is_cold_chain": 0, "cost": 2, "price": 4},
    {"sku_id": "SKU_OTC_002", "drug_name": "Paracetamol 500mg", "schedule": "OTC", "is_cold_chain": 0, "cost": 1.5, "price": 3},
    {"sku_id": "SKU_OTC_003", "drug_name": "ORS Sachets", "schedule": "OTC", "is_cold_chain": 0, "cost": 8, "price": 15},
    {"sku_id": "SKU_OTC_004", "drug_name": "Cetirizine 10mg", "schedule": "OTC", "is_cold_chain": 0, "cost": 2, "price": 4},
    {"sku_id": "SKU_OTC_005", "drug_name": "Dengue NS1 Test Kit", "schedule": "OTC", "is_cold_chain": 0, "cost": 280, "price": 450},
    {"sku_id": "SKU_OTC_006", "drug_name": "Papaya Leaf Extract 1100mg", "schedule": "OTC", "is_cold_chain": 0, "cost": 180, "price": 280},
    {"sku_id": "SKU_OTC_007", "drug_name": "N95 Mask Pack 10", "schedule": "OTC", "is_cold_chain": 0, "cost": 120, "price": 199},
    {"sku_id": "SKU_OTC_008", "drug_name": "Zinc 20mg Tablets", "schedule": "OTC", "is_cold_chain": 0, "cost": 4, "price": 8},
    {"sku_id": "SKU_OTC_009", "drug_name": "Electral Powder", "schedule": "OTC", "is_cold_chain": 0, "cost": 22, "price": 38},
]


def generate_store_inventory(store_id, include_near_expiry=True):
    inventory = []
    for drug in DRUG_CATALOG:
        if random.random() < 0.85:
            quantity = random.randint(20, 500)
            reorder_point = random.randint(15, 50)
            velocity = round(random.uniform(2, 30), 1)
            if include_near_expiry and random.random() < 0.12:
                days_to_expiry = random.randint(10, 55)
                expiry_date = (date.today() + timedelta(days=days_to_expiry)).isoformat()
                quantity = random.randint(50, 300)
                velocity = round(random.uniform(0.5, 3), 1)
            else:
                expiry_date = (
                    date.today() + timedelta(days=random.randint(90, 730))
                ).isoformat()
            inventory.append({
                "store_id": store_id,
                "sku_id": drug["sku_id"],
                "drug_name": drug["drug_name"],
                "batch_number": "B{}".format(random.randint(100000, 999999)),
                "quantity": quantity,
                "reorder_point": reorder_point,
                "expiry_date": expiry_date,
                "cost_price": drug["cost"],
                "selling_price": drug["price"],
                "schedule_type": drug["schedule"],
                "is_cold_chain": drug["is_cold_chain"],
                "avg_daily_velocity": velocity,
            })
    return inventory