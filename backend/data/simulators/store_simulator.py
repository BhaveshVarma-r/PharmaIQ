import random

CITIES_TIER1 = [
    ("Delhi", "North"), ("Mumbai", "West"), ("Bangalore", "South"),
    ("Chennai", "South"), ("Kolkata", "East"), ("Hyderabad", "South"),
]
CITIES_TIER2 = [
    ("Pune", "West"), ("Ahmedabad", "West"), ("Jaipur", "North"),
    ("Lucknow", "North"), ("Bhopal", "Central"), ("Indore", "Central"),
    ("Nagpur", "Central"), ("Patna", "East"), ("Chandigarh", "North"),
    ("Coimbatore", "South"), ("Surat", "West"), ("Vadodara", "West"),
]
DISTRICTS = {
    "Delhi": ["East Delhi", "West Delhi", "South Delhi", "North Delhi", "Central Delhi"],
    "Mumbai": ["Andheri", "Bandra", "Dadar", "Borivali", "Thane"],
    "Bangalore": ["Koramangala", "Whitefield", "HSR Layout", "Jayanagar", "Indiranagar"],
    "Chennai": ["T.Nagar", "Anna Nagar", "Velachery", "Adyar", "Tambaram"],
    "Kolkata": ["Salt Lake", "New Town", "Jadavpur", "Howrah", "Dhakuria"],
    "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Madhapur", "Secunderabad", "Kukatpally"],
    "Pune": ["Koregaon Park", "Kothrud", "Hadapsar", "Viman Nagar", "Pimpri"],
    "Ahmedabad": ["Navrangpura", "Satellite", "Bopal", "Maninagar", "Vejalpur"],
    "Jaipur": ["Malviya Nagar", "Vaishali Nagar", "Raja Park", "Mansarovar", "Jagatpura"],
    "Lucknow": ["Gomti Nagar", "Hazratganj", "Aliganj", "Indiranagar", "Alambagh"],
}


def generate_stores(count=320):
    stores = []
    store_num = 1
    tier1_count = int(count * 0.6)
    tier2_count = count - tier1_count
    for i in range(tier1_count):
        city, zone = random.choice(CITIES_TIER1)
        district = random.choice(DISTRICTS.get(city, ["Central"]))
        stores.append(_make_store(store_num, city, "Tier1", zone, district))
        store_num += 1
    for i in range(tier2_count):
        city, zone = random.choice(CITIES_TIER2)
        district = random.choice(DISTRICTS.get(city, ["Central"]))
        stores.append(_make_store(store_num, city, "Tier2", zone, district))
        store_num += 1
    return stores


def _make_store(num, city, tier, zone, district):
    return {
        "store_id": "MC{:04d}".format(num),
        "store_name": "MedChain {} {:04d}".format(city, num),
        "city": city,
        "tier": tier,
        "zone": zone,
        "district": district,
        "latitude": round(random.uniform(8.0, 35.0), 6),
        "longitude": round(random.uniform(68.0, 97.0), 6),
        "pharmacist_count": random.randint(2, 5),
        "fridge_count": random.randint(2, 4),
        "operating_hours_start": "08:00",
        "operating_hours_end": "22:00",
        "avg_daily_patients": random.randint(80, 300),
    }