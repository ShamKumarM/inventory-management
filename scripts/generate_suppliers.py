import random
import pandas as pd
from faker import Faker

from src.config import (
    SYNTHETIC_DIR,
    NUM_SUPPLIERS,
    CITIES,
    RANDOM_SEED,
    SUPPLIER_LEAD_TIME_RANGE,
)

random.seed(RANDOM_SEED)

fake = Faker("en_IN")
fake.seed_instance(RANDOM_SEED)


def generate_suppliers():

    suppliers = []

    for i in range(1, NUM_SUPPLIERS + 1):

        city = random.choice(CITIES)

        supplier = {
            "supplier_id": f"SUP{i:04d}",
            "supplier_name": f"{fake.company()} Foods",
            "city": city,
            "state": {
                "Chennai": "Tamil Nadu",
                "Coimbatore": "Tamil Nadu",
                "Madurai": "Tamil Nadu",
                "Trichy": "Tamil Nadu",
                "Bengaluru": "Karnataka",
                "Hyderabad": "Telangana",
                "Mumbai": "Maharashtra",
                "Pune": "Maharashtra",
                "Delhi": "Delhi",
                "Kochi": "Kerala",
            }[city],
            "contact_email": fake.company_email(),
            "contact_phone": fake.phone_number(),
            "lead_time_days": random.randint(
                *SUPPLIER_LEAD_TIME_RANGE
            ),
            "minimum_order_quantity": random.choice(
                [50, 100, 200, 500]
            ),
            "reliability_score": round(
                random.uniform(0.75, 0.99), 2
            ),
        }

        suppliers.append(supplier)

    df = pd.DataFrame(suppliers)

    output = SYNTHETIC_DIR / "suppliers.csv"

    df.to_csv(output, index=False)

    print(f"Generated {len(df):,} suppliers")
    print(f"Saved → {output}")

    return df


if __name__ == "__main__":
    generate_suppliers()