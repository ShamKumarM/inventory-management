import random

import numpy as np
import pandas as pd

from src.config import (
    SYNTHETIC_DIR,
    RANDOM_SEED,
)

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# -----------------------------------------
# Product popularity weights
# -----------------------------------------

POPULARITY_WEIGHTS = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.8,
    "very_high": 3.0,
}


# -----------------------------------------
# Customer segment behavior
# -----------------------------------------

SEGMENT_MULTIPLIER = {
    "new": 0.8,
    "regular": 1.0,
    "loyal": 1.3,
    "high_value": 1.8,
}


def generate_order_items():

    print("Loading datasets...")

    orders = pd.read_csv(
        SYNTHETIC_DIR / "orders.csv"
    )

    customers = pd.read_csv(
        SYNTHETIC_DIR / "customers.csv"
    )

    products = pd.read_csv(
        SYNTHETIC_DIR / "products.csv"
    )

    # -----------------------------------------
    # Merge customer information
    # -----------------------------------------

    orders = orders.merge(
        customers[
            [
                "customer_id",
                "customer_segment",
            ]
        ],
        on="customer_id",
        how="left",
    )

    # -----------------------------------------
    # Prepare product weights
    # -----------------------------------------

    products["popularity_weight"] = (
        products["popularity"]
        .map(POPULARITY_WEIGHTS)
    )

    product_ids = products[
        "product_id"
    ].to_numpy()

    product_weights = products[
        "popularity_weight"
    ].to_numpy()

    product_weights = (
        product_weights
        / product_weights.sum()
    )

    # -----------------------------------------
    # Generate items
    # -----------------------------------------

    order_items = []

    item_id = 1

    for _, order in orders.iterrows():

        # Number of different products
        # in this order

        segment = order[
            "customer_segment"
        ]

        multiplier = SEGMENT_MULTIPLIER[
            segment
        ]

        # High-value customers tend to
        # purchase more products

        base_items = np.random.choice(
            [1, 2, 3, 4, 5],
            p=[
                0.45,
                0.30,
                0.15,
                0.07,
                0.03,
            ],
        )

        num_items = max(
            1,
            round(
                base_items * multiplier
            ),
        )

        num_items = min(
            num_items,
            6,
        )

        # Select unique products

        selected_products = np.random.choice(
            product_ids,
            size=num_items,
            replace=False,
            p=product_weights,
        )

        for product_id in selected_products:

            product = products[
                products["product_id"]
                == product_id
            ].iloc[0]

            # ---------------------------------
            # Quantity
            # ---------------------------------

            quantity = np.random.choice(
                [1, 2, 3, 4, 5],
                p=[
                    0.55,
                    0.25,
                    0.12,
                    0.06,
                    0.02,
                ],
            )

            # High-value customers sometimes
            # buy larger quantities

            if segment == "high_value":

                if random.random() < 0.30:
                    quantity += 1

            # ---------------------------------
            # Price
            # ---------------------------------

            unit_price = float(
                product["selling_price"]
            )

            discount = float(
                order["discount_percentage"]
            )

            discounted_price = round(
                unit_price
                * (1 - discount / 100),
                2,
            )

            # ---------------------------------
            # Create item
            # ---------------------------------

            order_items.append(
                {
                    "order_item_id":
                        f"ITEM{item_id:09d}",

                    "order_id":
                        order["order_id"],

                    "product_id":
                        product_id,

                    "quantity":
                        quantity,

                    "unit_price":
                        unit_price,

                    "discount_percentage":
                        discount,

                    "final_unit_price":
                        discounted_price,

                    "line_total":
                        round(
                            quantity
                            * discounted_price,
                            2,
                        ),
                }
            )

            item_id += 1

    # -----------------------------------------
    # Create dataframe
    # -----------------------------------------

    df = pd.DataFrame(
        order_items
    )

    # -----------------------------------------
    # Save
    # -----------------------------------------

    output = (
        SYNTHETIC_DIR
        / "order_items.csv"
    )

    df.to_csv(
        output,
        index=False,
    )

    print(
        f"\nGenerated "
        f"{len(df):,} order items"
    )

    print(
        f"Saved → {output}"
    )

    # -----------------------------------------
    # Statistics
    # -----------------------------------------

    print("\nTop products:")

    print(
        df.groupby("product_id")[
            "quantity"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
    )

    print("\nAverage items per order:")

    print(
        round(
            len(df)
            / orders["order_id"].nunique(),
            2,
        )
    )

    print("\nTotal units sold:")

    print(
        df["quantity"].sum()
    )

    print("\nRevenue generated:")

    print(
        round(
            df["line_total"].sum(),
            2,
        )
    )

    return df


if __name__ == "__main__":
    generate_order_items()