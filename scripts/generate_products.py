import random
import pandas as pd

from src.config import (
    SYNTHETIC_DIR,
    NUM_PRODUCTS,
    PRODUCT_CATEGORIES,
    PACK_SIZES,
    PRICE_RANGES,
    SHELF_LIFE_RANGE,
    RANDOM_SEED,
)

random.seed(RANDOM_SEED)


def generate_products():

    products = []

    categories = list(PRODUCT_CATEGORIES.keys())

    for i in range(1, NUM_PRODUCTS + 1):

        category = random.choice(categories)

        base_name = random.choice(
            PRODUCT_CATEGORIES[category]
        )

        pack_size = random.choice(PACK_SIZES)

        min_price, max_price = PRICE_RANGES[category]

        selling_price = round(
            random.uniform(min_price, max_price), 2
        )

        cost_price = round(
            selling_price * random.uniform(0.45, 0.70),
            2,
        )

        shelf_life = random.randint(
            *SHELF_LIFE_RANGE
        )

        lead_time = random.randint(2, 14)

        minimum_stock = random.randint(50, 300)

        maximum_stock = minimum_stock * random.randint(
            3, 8
        )

        # Popularity influences future synthetic demand
        popularity = random.choice(
            ["low", "medium", "high", "very_high"]
        )

        products.append(
            {
                "product_id": f"PRD{i:04d}",
                "sku": f"CKD-{category[:3].upper()}-{i:04d}",
                "product_name": f"{base_name} {pack_size}g",
                "category": category,
                "pack_size_grams": pack_size,
                "selling_price": selling_price,
                "cost_price": cost_price,
                "shelf_life_days": shelf_life,
                "supplier_lead_time_days": lead_time,
                "minimum_stock": minimum_stock,
                "maximum_stock": maximum_stock,
                "popularity": popularity,
                "is_active": True,
            }
        )

    df = pd.DataFrame(products)

    output = SYNTHETIC_DIR / "products.csv"

    df.to_csv(output, index=False)

    print(f"Generated {len(df):,} products")
    print(f"Saved → {output}")

    print("\nCategory distribution:")
    print(df["category"].value_counts())

    print("\nPopularity distribution:")
    print(df["popularity"].value_counts())

    return df


if __name__ == "__main__":
    generate_products()