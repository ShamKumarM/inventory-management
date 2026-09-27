import random
import pandas as pd
from faker import Faker

from src.config import (
    SYNTHETIC_DIR,
    NUM_CUSTOMERS,
    CITIES,
    STATES,
    CUSTOMER_SEGMENTS,
    RANDOM_SEED,
)

random.seed(RANDOM_SEED)

fake = Faker("en_IN")
fake.seed_instance(RANDOM_SEED)


def weighted_choice(options):
    return random.choices(
        list(options.keys()),
        weights=list(options.values()),
        k=1,
    )[0]


def generate_customers():

    customers = []

    for i in range(1, NUM_CUSTOMERS + 1):

        city = random.choice(CITIES)

        segment = weighted_choice(
            CUSTOMER_SEGMENTS
        )

        customers.append(
            {
                "customer_id": f"CUS{i:06d}",
                "name": fake.name(),
                "phone": fake.phone_number(),
                "email": fake.email(),
                "city": city,
                "state": STATES[city],
                "customer_segment": segment,
                "created_at": fake.date_between(
                    start_date="-3y",
                    end_date="today",
                ),
            }
        )

    df = pd.DataFrame(customers)

    output = SYNTHETIC_DIR / "customers.csv"

    df.to_csv(output, index=False)

    print(f"Generated {len(df):,} customers")
    print(f"Saved → {output}")

    print("\nCustomer segments:")
    print(df["customer_segment"].value_counts())

    return df


if __name__ == "__main__":
    generate_customers()