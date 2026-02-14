"""Generate deterministic synthetic banking transactions with injected anomalies."""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path


CANADIAN_CITIES = [
    "Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa",
    "Edmonton", "Winnipeg", "Quebec City", "Hamilton", "Halifax",
]

INTERNATIONAL_CITIES = [
    "New York", "London", "Tokyo", "Dubai", "Mumbai",
    "Paris", "Singapore", "Hong Kong", "Sydney", "Berlin",
]

MERCHANT_CATEGORIES = [
    "Grocery", "Restaurant", "Gas Station", "Online Shopping", "Entertainment",
    "Travel", "Healthcare", "Utilities", "Electronics", "Clothing",
]

MERCHANT_NAMES = {
    "Grocery": ["FreshMart", "SuperSave", "GreenGrocer", "Metro Plus", "FoodLand"],
    "Restaurant": ["Golden Wok", "Pasta Palace", "Burger Hub", "Sushi Zen", "Cafe Latte"],
    "Gas Station": ["PetroGo", "FuelUp", "QuickGas", "EnergyStop", "GasMax"],
    "Online Shopping": ["ShopNow", "ClickBuy", "WebMart", "eStore", "NetShop"],
    "Entertainment": ["CinePlex", "GameZone", "MusicHall", "FunPark", "StreamFlix"],
    "Travel": ["FlyAway", "BookTrip", "TravelEase", "JetSet", "WanderLux"],
    "Healthcare": ["MediCare", "HealthPlus", "PharmaSave", "WellClinic", "CareFirst"],
    "Utilities": ["HydroPower", "TelcoNet", "WaterWorks", "GasLine", "PowerGrid"],
    "Electronics": ["TechByte", "GadgetWorld", "CircuitHub", "DigiMart", "ElectroZone"],
    "Clothing": ["StyleHub", "FashionFit", "TrendWear", "UrbanThreads", "ChicBoutique"],
}

CHANNELS = ["online", "POS", "ATM"]

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "transactions.csv"

FIELDNAMES = [
    "transaction_id", "customer_id", "merchant_id", "merchant_name",
    "merchant_category", "amount", "timestamp", "currency", "channel",
    "city", "is_international",
]


def _make_customer_profiles(rng: random.Random, n_customers: int) -> list[dict]:
    """Create customer profiles with spending habits."""
    profiles = []
    for i in range(n_customers):
        avg_amount = rng.uniform(20, 500)
        usual_hour_start = rng.randint(7, 12)
        usual_hour_end = rng.randint(17, 22)
        has_international = rng.random() < 0.15
        profiles.append({
            "customer_id": f"C-{i + 1:04d}",
            "avg_amount": avg_amount,
            "std_amount": avg_amount * rng.uniform(0.2, 0.6),
            "usual_hour_start": usual_hour_start,
            "usual_hour_end": usual_hour_end,
            "has_international": has_international,
            "preferred_merchants": rng.sample(range(200), k=rng.randint(3, 10)),
        })
    return profiles


def _make_merchant_profiles(rng: random.Random, n_merchants: int) -> list[dict]:
    """Create merchant profiles."""
    profiles = []
    for i in range(n_merchants):
        category = rng.choice(MERCHANT_CATEGORIES)
        name = rng.choice(MERCHANT_NAMES[category])
        profiles.append({
            "merchant_id": f"M-{i + 1:04d}",
            "merchant_name": f"{name} #{i + 1}",
            "merchant_category": category,
        })
    return profiles


def _generate_normal_transaction(
    rng: random.Random,
    txn_id: int,
    customer: dict,
    merchants: list[dict],
    base_date: datetime,
    day_offset: int,
) -> dict:
    """Generate a single normal transaction."""
    hour = rng.randint(customer["usual_hour_start"], customer["usual_hour_end"])
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)

    amount = max(0.50, rng.gauss(customer["avg_amount"], customer["std_amount"]))
    amount = round(amount, 2)

    merchant_idx = rng.choice(customer["preferred_merchants"])
    merchant = merchants[merchant_idx % len(merchants)]

    is_international = False
    city = rng.choice(CANADIAN_CITIES)
    currency = "CAD"

    if customer["has_international"] and rng.random() < 0.05:
        is_international = True
        city = rng.choice(INTERNATIONAL_CITIES)
        currency = "USD"

    channel = rng.choices(CHANNELS, weights=[0.4, 0.5, 0.1])[0]

    return {
        "transaction_id": f"TXN-{txn_id:06d}",
        "customer_id": customer["customer_id"],
        "merchant_id": merchant["merchant_id"],
        "merchant_name": merchant["merchant_name"],
        "merchant_category": merchant["merchant_category"],
        "amount": amount,
        "timestamp": ts.isoformat(),
        "currency": currency,
        "channel": channel,
        "city": city,
        "is_international": is_international,
    }


def generate_dataset(n_rows: int = 50000, seed: int = 42) -> dict:
    """Generate the full dataset and return anomaly injection stats."""
    rng = random.Random(seed)

    n_customers = 500
    n_merchants = 200
    customers = _make_customer_profiles(rng, n_customers)
    merchants = _make_merchant_profiles(rng, n_merchants)

    base_date = datetime(2024, 1, 1)
    n_days = 90

    # Generate normal transactions
    transactions: list[dict] = []
    txn_id = 1
    normal_count = int(n_rows * 0.97)

    for _ in range(normal_count):
        customer = rng.choice(customers)
        day_offset = rng.randint(0, n_days - 1)
        txn = _generate_normal_transaction(rng, txn_id, customer, merchants, base_date, day_offset)
        transactions.append(txn)
        txn_id += 1

    # Inject anomalies
    anomaly_count = n_rows - normal_count
    anomaly_stats = {
        "late_night_high_amount": 0,
        "international_no_history": 0,
        "amount_spike_10x": 0,
        "rapid_fire_burst": 0,
    }

    anomaly_types = ["late_night", "international", "spike", "rapid_fire"]
    i = 0
    while i < anomaly_count:
        atype = rng.choice(anomaly_types)
        customer = rng.choice(customers)
        day_offset = rng.randint(0, n_days - 1)
        merchant = merchants[rng.randint(0, len(merchants) - 1)]

        if atype == "late_night":
            # 3-5 AM transaction > $5,000
            hour = rng.randint(3, 5)
            ts = base_date + timedelta(
                days=day_offset, hours=hour,
                minutes=rng.randint(0, 59), seconds=rng.randint(0, 59),
            )
            amount = round(rng.uniform(5000, 15000), 2)
            transactions.append({
                "transaction_id": f"TXN-{txn_id:06d}",
                "customer_id": customer["customer_id"],
                "merchant_id": merchant["merchant_id"],
                "merchant_name": merchant["merchant_name"],
                "merchant_category": merchant["merchant_category"],
                "amount": amount,
                "timestamp": ts.isoformat(),
                "currency": "CAD",
                "channel": rng.choice(["online", "ATM"]),
                "city": rng.choice(CANADIAN_CITIES),
                "is_international": False,
            })
            anomaly_stats["late_night_high_amount"] += 1
            txn_id += 1
            i += 1

        elif atype == "international":
            # International for customer with no international history
            non_intl_customers = [c for c in customers if not c["has_international"]]
            if not non_intl_customers:
                continue
            customer = rng.choice(non_intl_customers)
            hour = rng.randint(customer["usual_hour_start"], customer["usual_hour_end"])
            ts = base_date + timedelta(
                days=day_offset, hours=hour,
                minutes=rng.randint(0, 59), seconds=rng.randint(0, 59),
            )
            amount = round(rng.gauss(customer["avg_amount"], customer["std_amount"]) * 1.5, 2)
            amount = max(10.0, amount)
            transactions.append({
                "transaction_id": f"TXN-{txn_id:06d}",
                "customer_id": customer["customer_id"],
                "merchant_id": merchant["merchant_id"],
                "merchant_name": merchant["merchant_name"],
                "merchant_category": merchant["merchant_category"],
                "amount": amount,
                "timestamp": ts.isoformat(),
                "currency": "USD",
                "channel": "online",
                "city": rng.choice(INTERNATIONAL_CITIES),
                "is_international": True,
            })
            anomaly_stats["international_no_history"] += 1
            txn_id += 1
            i += 1

        elif atype == "spike":
            # 10x customer average spike
            hour = rng.randint(customer["usual_hour_start"], customer["usual_hour_end"])
            ts = base_date + timedelta(
                days=day_offset, hours=hour,
                minutes=rng.randint(0, 59), seconds=rng.randint(0, 59),
            )
            amount = round(customer["avg_amount"] * rng.uniform(8, 12), 2)
            transactions.append({
                "transaction_id": f"TXN-{txn_id:06d}",
                "customer_id": customer["customer_id"],
                "merchant_id": merchant["merchant_id"],
                "merchant_name": merchant["merchant_name"],
                "merchant_category": merchant["merchant_category"],
                "amount": amount,
                "timestamp": ts.isoformat(),
                "currency": "CAD",
                "channel": rng.choice(CHANNELS),
                "city": rng.choice(CANADIAN_CITIES),
                "is_international": False,
            })
            anomaly_stats["amount_spike_10x"] += 1
            txn_id += 1
            i += 1

        elif atype == "rapid_fire":
            # 5+ transactions within 10 minutes
            burst_size = rng.randint(5, 8)
            if i + burst_size > anomaly_count:
                burst_size = anomaly_count - i
            hour = rng.randint(0, 23)
            base_ts = base_date + timedelta(
                days=day_offset, hours=hour,
                minutes=rng.randint(0, 50),
            )
            for b in range(burst_size):
                ts = base_ts + timedelta(seconds=rng.randint(0, 600))
                amount = round(rng.uniform(10, 200), 2)
                transactions.append({
                    "transaction_id": f"TXN-{txn_id:06d}",
                    "customer_id": customer["customer_id"],
                    "merchant_id": merchant["merchant_id"],
                    "merchant_name": merchant["merchant_name"],
                    "merchant_category": merchant["merchant_category"],
                    "amount": amount,
                    "timestamp": ts.isoformat(),
                    "currency": "CAD",
                    "channel": rng.choice(CHANNELS),
                    "city": rng.choice(CANADIAN_CITIES),
                    "is_international": False,
                })
                txn_id += 1
                i += 1
            anomaly_stats["rapid_fire_burst"] += 1

    # Sort by timestamp
    transactions.sort(key=lambda t: t["timestamp"])

    # Write CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(transactions)

    return {
        "total_rows": len(transactions),
        "normal_rows": normal_count,
        "anomaly_rows": len(transactions) - normal_count,
        "anomaly_stats": anomaly_stats,
        "output_file": str(OUTPUT_FILE),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transaction data")
    parser.add_argument("--rows", type=int, default=50000, help="Number of transactions")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    result = generate_dataset(n_rows=args.rows, seed=args.seed)

    print(f"Generated {result['total_rows']} transactions -> {result['output_file']}")
    print(f"  Normal: {result['normal_rows']}")
    print(f"  Anomalies injected: {result['anomaly_rows']}")
    print("  Anomaly breakdown:")
    for k, v in result["anomaly_stats"].items():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
