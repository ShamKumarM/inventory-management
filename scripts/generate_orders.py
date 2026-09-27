import random

import numpy as np
import pandas as pd

from src.config import (
    SYNTHETIC_DIR,
    START_DATE,
    END_DATE,
    ORDER_CHANNELS,
    ORDER_STATUSES,
    NUM_ORDERS,
    RANDOM_SEED,
)

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def weighted_choice(options):
    return random.choices(
        list(options.keys()),
        weights=list(options.values()),
        k=1,
    )[0]


def generate_orders():

    customers = pd.read_csv(
        SYNTHETIC_DIR / "customers.csv"
    )

    # -----------------------------------------
    # Load customer IDs once
    # -----------------------------------------

    customer_ids_pool = customers[
        "customer_id"
    ].to_numpy()

    # -----------------------------------------
    # Generate dates
    # -----------------------------------------

    dates = pd.date_range(
        START_DATE,
        END_DATE,
    ).to_numpy()

    # -----------------------------------------
    # Generate customers efficiently
    # -----------------------------------------

    selected_customers = np.random.choice(
        customer_ids_pool,
        size=NUM_ORDERS,
        replace=True,
    )

    selected_dates = np.random.choice(
        dates,
        size=NUM_ORDERS,
        replace=True,
    )

    # -----------------------------------------
    # Generate statuses
    # -----------------------------------------

    statuses = random.choices(
        list(ORDER_STATUSES.keys()),
        weights=list(ORDER_STATUSES.values()),
        k=NUM_ORDERS,
    )

    # -----------------------------------------
    # Generate channels
    # -----------------------------------------

    channels = random.choices(
        list(ORDER_CHANNELS.keys()),
        weights=list(ORDER_CHANNELS.values()),
        k=NUM_ORDERS,
    )

    # -----------------------------------------
    # Generate discounts
    # -----------------------------------------

    discounts = np.random.choice(
        [0, 5, 10, 15, 20],
        size=NUM_ORDERS,
        p=[0.50, 0.15, 0.20, 0.10, 0.05],
    )

    # -----------------------------------------
    # Build dataframe
    # -----------------------------------------

    orders = pd.DataFrame(
        {
            "order_id": [
                f"ORD{i:08d}"
                for i in range(1, NUM_ORDERS + 1)
            ],
            "customer_id": selected_customers,
            "order_date": pd.to_datetime(
                selected_dates
            ),
            "order_status": statuses,
            "channel": channels,
            "discount_percentage": discounts,
        }
    )

    # Sort chronologically
    orders = orders.sort_values(
        "order_date"
    ).reset_index(drop=True)

    # -----------------------------------------
    # Save
    # -----------------------------------------

    output = (
        SYNTHETIC_DIR / "orders.csv"
    )

    orders.to_csv(
        output,
        index=False,
    )

    print(
        f"Generated {len(orders):,} orders"
    )

    print(
        f"Saved → {output}"
    )

    print("\nChannel distribution:")

    print(
        orders["channel"]
        .value_counts(normalize=True)
        .round(3)
    )

    print("\nStatus distribution:")

    print(
        orders["order_status"]
        .value_counts(normalize=True)
        .round(3)
    )

    print("\nDate range:")

    print(
        orders["order_date"].min(),
        "→",
        orders["order_date"].max(),
    )

    return orders


if __name__ == "__main__":
    generate_orders()