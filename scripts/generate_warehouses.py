import pandas as pd

from src.config import SYNTHETIC_DIR


def generate_warehouses():

    warehouses = [
        {
            "warehouse_id": "WH001",
            "warehouse_name": "Chennai Central Warehouse",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "capacity_units": 100000,
        },
        {
            "warehouse_id": "WH002",
            "warehouse_name": "Bengaluru Distribution Center",
            "city": "Bengaluru",
            "state": "Karnataka",
            "capacity_units": 75000,
        },
        {
            "warehouse_id": "WH003",
            "warehouse_name": "Hyderabad Distribution Center",
            "city": "Hyderabad",
            "state": "Telangana",
            "capacity_units": 75000,
        },
    ]

    df = pd.DataFrame(warehouses)

    output = (
        SYNTHETIC_DIR / "warehouses.csv"
    )

    df.to_csv(
        output,
        index=False,
    )

    print(
        f"Generated {len(df)} warehouses"
    )

    print(
        f"Saved → {output}"
    )

    return df


if __name__ == "__main__":
    generate_warehouses()