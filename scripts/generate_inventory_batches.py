import random

import pandas as pd

from src.config import (
    SYNTHETIC_DIR,
    RANDOM_SEED,
)

random.seed(RANDOM_SEED)


def generate_inventory_batches():

    products = pd.read_csv(
        SYNTHETIC_DIR / "products.csv"
    )

    warehouses = pd.read_csv(
        SYNTHETIC_DIR / "warehouses.csv"
    )

    transactions = pd.read_csv(
        SYNTHETIC_DIR
        / "inventory_transactions.csv"
    )

    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )

    # -----------------------------------------
    # Only purchases create inventory batches
    # -----------------------------------------

    purchases = transactions[
        transactions["transaction_type"]
        == "PURCHASE"
    ].copy()

    batches = []

    batch_counter = 1

    for _, purchase in purchases.iterrows():

        product = products[
            products["product_id"]
            == purchase["product_id"]
        ].iloc[0]

        production_date = (
            purchase["transaction_date"]
        )

        shelf_life = int(
            product["shelf_life_days"]
        )

        expiry_date = (
            production_date
            + pd.Timedelta(
                days=shelf_life
            )
        )

        batches.append(
            {
                "batch_id":
                    f"BATCH{batch_counter:07d}",

                "product_id":
                    purchase["product_id"],

                "warehouse_id":
                    purchase["warehouse_id"],

                "purchase_transaction_id":
                    purchase["transaction_id"],

                "production_date":
                    production_date,

                "expiry_date":
                    expiry_date,

                "initial_quantity":
                    int(purchase["quantity"]),

                # Initially all purchased
                # inventory is available
                "available_quantity":
                    int(purchase["quantity"]),

                "batch_status":
                    "active",
            }
        )

        batch_counter += 1

    df = pd.DataFrame(batches)

    # -----------------------------------------
    # Save
    # -----------------------------------------

    output = (
        SYNTHETIC_DIR
        / "inventory_batches.csv"
    )

    df.to_csv(
        output,
        index=False,
    )

    print(
        f"Generated "
        f"{len(df):,} inventory batches"
    )

    print(
        f"Saved → {output}"
    )

    print("\nBatch status:")

    print(
        df["batch_status"]
        .value_counts()
    )

    print("\nExpiry range:")

    print(
        df["expiry_date"].min(),
        "→",
        df["expiry_date"].max(),
    )

    return df


if __name__ == "__main__":
    generate_inventory_batches()