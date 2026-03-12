import random
import uuid
from datetime import date, timedelta

DISEASE_PROFILES = {
    "dengue": {
        "affected_skus": [
            "Paracetamol 650mg", "Dengue NS1 Antigen Test Kit",
            "Papaya Leaf Extract 1100mg", "ORS Sachets", "Platelet Plus Supplement"
        ],
        "demand_multiplier_range": (3.0, 5.0),
        "severity_options": ["WATCH", "ALERT", "OUTBREAK"],
        "case_count_range": (15, 450),
    },
    "malaria": {
        "affected_skus": [
            "Artemether-Lumefantrine 20/120mg", "Chloroquine 250mg",
            "Malaria RDT Kit", "Paracetamol 500mg", "Primaquine 7.5mg"
        ],
        "demand_multiplier_range": (2.0, 4.0),
        "severity_options": ["WATCH", "ALERT"],
        "case_count_range": (10, 200),
    },
    "influenza": {
        "affected_skus": [
            "Oseltamivir 75mg", "Paracetamol 500mg", "Cetirizine 10mg",
            "Azithromycin 500mg", "N95 Mask Pack", "Vitamin C 500mg"
        ],
        "demand_multiplier_range": (2.0, 3.5),
        "severity_options": ["WATCH", "ALERT", "OUTBREAK"],
        "case_count_range": (25, 600),
    },
    "cholera": {
        "affected_skus": [
            "ORS Sachets", "Zinc 20mg Tablets", "Metronidazole 400mg",
            "Norfloxacin 400mg", "Electral Powder"
        ],
        "demand_multiplier_range": (4.0, 8.0),
        "severity_options": ["ALERT", "OUTBREAK", "EPIDEMIC"],
        "case_count_range": (5, 150),
    },
    "typhoid": {
        "affected_skus": [
            "Cefixime 200mg", "Azithromycin 500mg",
            "ORS Sachets", "Electral Powder", "Paracetamol 500mg"
        ],
        "demand_multiplier_range": (2.0, 3.0),
        "severity_options": ["WATCH", "ALERT"],
        "case_count_range": (10, 120),
    },
}

CITY_DISTRICTS = {
    "Delhi": ["East Delhi", "West Delhi", "South Delhi", "North Delhi"],
    "Mumbai": ["Andheri", "Bandra", "Dadar", "Borivali"],
    "Bangalore": ["Koramangala", "Whitefield", "HSR Layout", "Jayanagar"],
    "Chennai": ["T.Nagar", "Anna Nagar", "Velachery", "Adyar"],
    "Kolkata": ["Salt Lake", "New Town", "Jadavpur", "Howrah"],
    "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Madhapur", "Secunderabad"],
    "Pune": ["Koregaon Park", "Kothrud", "Hadapsar", "Viman Nagar"],
}


def generate_disease_alert(city=None, disease=None, alert_level=None):
    if not city:
        city = random.choice(list(CITY_DISTRICTS.keys()))
    districts = CITY_DISTRICTS.get(city, ["Central"])
    district = random.choice(districts)
    if not disease:
        disease = random.choice(list(DISEASE_PROFILES.keys()))
    profile = DISEASE_PROFILES[disease]
    if not alert_level:
        alert_level = random.choice(profile["severity_options"])
    case_count = random.randint(*profile["case_count_range"])
    reported_date = date.today() - timedelta(days=random.randint(0, 7))
    return {
        "alert_id": str(uuid.uuid4()),
        "district": district,
        "city": city,
        "disease_name": disease,
        "case_count": case_count,
        "severity": alert_level,
        "alert_level": alert_level,
        "idsp_bulletin_id": "IDSP-{}-{}-{}".format(
            city[:3].upper(),
            reported_date.strftime("%Y%m%d"),
            random.randint(100, 999)
        ),
        "reported_date": reported_date.isoformat(),
        "affected_skus": profile["affected_skus"],
        "demand_multiplier": round(random.uniform(*profile["demand_multiplier_range"]), 1),
        "active": 1,
    }


def generate_active_alerts(count=5):
    alerts = []
    cities = list(CITY_DISTRICTS.keys())
    diseases = list(DISEASE_PROFILES.keys())
    for _ in range(count):
        city = random.choice(cities)
        disease = random.choice(diseases)
        alerts.append(generate_disease_alert(city=city, disease=disease))
    return alerts