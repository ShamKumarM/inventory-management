from pathlib import Path
import math

import numpy as np
import pandas as pd

from src.ml.demand_forecaster import DemandForecaster


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
)

PRODUCTS_PATH = (
    DATA_DIR
    / "products.csv"
)

INVENTORY_PATH = (
    DATA_DIR
    / "inventory_snapshots.csv"
)

SUPPLIERS_PATH = (
    DATA_DIR
    / "suppliers.csv"
)


# ============================================================
# INVENTORY ENGINE
# ============================================================

class InventoryEngine:

    def __init__(self):

        print("Initializing Inventory Engine...")

        # ----------------------------------------------------
        # Load demand forecasting model
        # ----------------------------------------------------

        self.forecaster = (
            DemandForecaster()
        )

        # ----------------------------------------------------
        # Load products
        # ----------------------------------------------------

        self.products = pd.read_csv(
            PRODUCTS_PATH
        )

        # ----------------------------------------------------
        # Load inventory snapshots
        # ----------------------------------------------------

        self.inventory = pd.read_csv(
            INVENTORY_PATH
        )

        self.inventory["date"] = (
            pd.to_datetime(
                self.inventory["date"]
            )
        )

        # ----------------------------------------------------
        # Load suppliers
        # ----------------------------------------------------

        self.suppliers = pd.read_csv(
            SUPPLIERS_PATH
        )

        print(
            f"Products loaded: "
            f"{len(self.products)}"
        )

        print(
            f"Inventory snapshots: "
            f"{len(self.inventory):,}"
        )

        print(
            f"Suppliers loaded: "
            f"{len(self.suppliers)}"
        )

    # ========================================================
    # CURRENT INVENTORY
    # ========================================================


    def _get_current_inventory(
        self,
        product_id: str,
    ):

        product_inventory = (
            self.inventory[
                self.inventory[
                    "product_id"
                ]
                == product_id
            ]
        )
    

        if product_inventory.empty:

            return {
            "current_stock": 0,
            "warehouse_count": 0,
            }

    # ----------------------------------------------------
    # Latest snapshot for each warehouse
    # ----------------------------------------------------

        latest = (
            product_inventory
            .sort_values("date")
            .groupby(
                "warehouse_id",
                as_index=False,
            )
            .tail(1)
        )

        raw_stock = float(
            latest[
                "closing_stock"
            ]
            .sum()
        )

    # ----------------------------------------------------
    # DEMO INVENTORY NORMALIZATION
    #
    # The synthetic inventory generator produces stock
    # values much larger than the product master
    # minimum/maximum stock values.
    #
    # For the demo decision engine we therefore map
    # the raw stock signal into a realistic inventory
    # range.
    # ----------------------------------------------------

        product = self._get_product(
            product_id
        )

        minimum_stock = float(
            product[
                "minimum_stock"
            ]
        )

        maximum_stock = float(
            product[
                "maximum_stock"
            ]
        )

    # Use a deterministic product-specific ratio
    # derived from the raw inventory value.

        if maximum_stock > minimum_stock:

        # Convert raw stock into a stable 0–1
        # utilization signal.

            normalized_signal = (
                raw_stock
                /
                (
                    raw_stock
                    + maximum_stock
                )
            )

            current_stock = (
                minimum_stock
                +
                normalized_signal
                *
                (
                    maximum_stock
                    - minimum_stock
                )
            )

        else:

            current_stock = raw_stock

        return {
            "current_stock":
                float(current_stock),

            "warehouse_count":
                len(latest),
        }


    # ========================================================
    # PRODUCT INFORMATION
    # ========================================================

    def _get_product(
        self,
        product_id: str,
    ):

        product = (
            self.products[
                self.products[
                    "product_id"
                ]
                == product_id
            ]
        )

        if product.empty:

            raise ValueError(
                f"Product not found: "
                f"{product_id}"
            )

        return product.iloc[0]

    # ========================================================
    # DEMAND VARIABILITY
    # ========================================================

    def _get_demand_variability(
        self,
        product_id: str,
    ):

        product_data = (
            self.forecaster.dataset[
                self.forecaster.dataset[
                    "product_id"
                ]
                == product_id
            ]
            .sort_values("date")
        )

        if product_data.empty:

            return 0.0

        # ----------------------------------------------------
        # Use historical daily demand
        # ----------------------------------------------------

        if "lag_1" in product_data.columns:

            demand = (
                product_data[
                    "lag_1"
                ]
                .dropna()
            )

            if len(demand) > 1:

                return float(
                    demand.std()
                )

        return 0.0

    # ========================================================
    # FIND SUPPLIER
    # ========================================================

    def _get_supplier(
        self,
        product,
    ):

        supplier_lead_time = float(
            product[
                "supplier_lead_time_days"
            ]
        )

        # ----------------------------------------------------
        # Product already contains lead time.
        #
        # Supplier table is used to determine
        # MOQ and reliability.
        # ----------------------------------------------------

        supplier = None

        # ----------------------------------------------------
        # Since the synthetic product dataset does
        # not contain supplier_id, use the supplier
        # with the closest lead time.
        # ----------------------------------------------------

        if not self.suppliers.empty:

            supplier = (
                self.suppliers.assign(
                    lead_diff=lambda x:
                    abs(
                        x[
                            "lead_time_days"
                        ]
                        - supplier_lead_time
                    )
                )
                .sort_values(
                    "lead_diff"
                )
                .iloc[0]
            )

        return supplier

    # ========================================================
    # INVENTORY DECISION
    # ========================================================

    def analyze_product(
        self,
        product_id: str,
    ):

        # ----------------------------------------------------
        # Product
        # ----------------------------------------------------

        product = (
            self._get_product(
                product_id
            )
        )

        # ----------------------------------------------------
        # Demand forecast
        # ----------------------------------------------------

        forecast = (
            self.forecaster
            .forecast_product(
                product_id
            )
        )

        predicted_demand = (
            forecast[
                "predicted_demand"
            ]
        )

        daily_demand = (
            forecast[
                "average_daily_demand"
            ]
        )

        # ----------------------------------------------------
        # Current stock
        # ----------------------------------------------------

        inventory = (
            self._get_current_inventory(
                product_id
            )
        )

        current_stock = (
            inventory[
                "current_stock"
            ]
        )

        # ----------------------------------------------------
        # Supplier information
        # ----------------------------------------------------

        supplier = (
            self._get_supplier(
                product
            )
        )

        lead_time = float(
            product[
                "supplier_lead_time_days"
            ]
        )

        if supplier is not None:

            supplier_moq = float(
                supplier[
                    "minimum_order_quantity"
                ]
            )

            reliability = float(
                supplier[
                    "reliability_score"
                ]
            )

            supplier_name = (
                supplier[
                    "supplier_name"
                ]
            )

        else:

            supplier_moq = 1.0

            reliability = 0.0

            supplier_name = (
                "Unknown"
            )

        # ----------------------------------------------------
        # Demand variability
        # ----------------------------------------------------

        demand_std = (
            self._get_demand_variability(
                product_id
            )
        )

        # ----------------------------------------------------
        # Lead-time demand
        # ----------------------------------------------------

        lead_time_demand = (
            daily_demand
            * lead_time
        )

        # ----------------------------------------------------
        # Safety stock
        #
        # Z = 1.65 ≈ 95% service level
        # ----------------------------------------------------

        z_score = 1.65

        safety_stock = (
            z_score
            * demand_std
            * math.sqrt(
                max(
                    lead_time,
                    1,
                )
            )
        )

        # ----------------------------------------------------
        # Reorder point
        # ----------------------------------------------------

        reorder_point = (
            lead_time_demand
            + safety_stock
        )

        # ----------------------------------------------------
        # Days of inventory
        # ----------------------------------------------------

        if daily_demand > 0:

            days_of_inventory = (
                current_stock
                / daily_demand
            )

        else:

            days_of_inventory = (
                float("inf")
            )

        # ----------------------------------------------------
        # Maximum stock from product master
        # ----------------------------------------------------

        maximum_stock = float(
            product[
                "maximum_stock"
            ]
        )

        minimum_stock = float(
            product[
                "minimum_stock"
            ]
        )

        # ----------------------------------------------------
        # Target stock
        #
        # We protect against:
        #
        # 7-day demand
        # +
        # lead-time demand
        # +
        # safety stock
        # ----------------------------------------------------

        target_stock = (
            predicted_demand
            + lead_time_demand
            + safety_stock
        )

        # Never exceed configured maximum
        # stock unnecessarily.

        target_stock = min(
            target_stock,
            maximum_stock,
        )

        # ----------------------------------------------------
        # Recommended order quantity
        # ----------------------------------------------------

        recommended_quantity = max(
            target_stock
            - current_stock,
            0,
        )

        # ----------------------------------------------------
        # Respect supplier MOQ
        # ----------------------------------------------------

        if (
            recommended_quantity > 0
            and recommended_quantity
            < supplier_moq
        ):

            recommended_quantity = (
                supplier_moq
            )

        recommended_quantity = math.ceil(
            recommended_quantity
        )

        # ====================================================
        # STOCKOUT RISK
        # ====================================================

        if current_stock <= 0:

            stockout_risk = "HIGH"

        elif current_stock <= reorder_point:

            stockout_risk = "HIGH"

        elif current_stock <= (
            reorder_point * 1.5
        ):

            stockout_risk = "MEDIUM"

        else:

            stockout_risk = "LOW"

        # ====================================================
        # INVENTORY STATUS
        # ====================================================

        if current_stock <= 0:

            inventory_status = (
                "OUT_OF_STOCK"
            )

        elif current_stock <= reorder_point:

            inventory_status = (
                "REORDER_NOW"
            )

        elif current_stock <= (
            reorder_point * 1.5
        ):

            inventory_status = (
                "REORDER_SOON"
            )

        elif current_stock > maximum_stock:

            inventory_status = (
                "OVERSTOCK"
            )

        else:

            inventory_status = (
                "HEALTHY"
            )

        # ====================================================
        # RETURN DECISION
        # ====================================================

        return {

            "product_id":
                product_id,

            "product_name":
                product[
                    "product_name"
                ],

            "category":
                product[
                    "category"
                ],

            "supplier":
                supplier_name,

            "supplier_reliability":
                round(
                    reliability,
                    2,
                ),

            "current_stock":
                round(
                    current_stock,
                    2,
                ),

            "warehouse_count":
                inventory[
                    "warehouse_count"
                ],

            "forecast_7d":
                round(
                    predicted_demand,
                    2,
                ),

            "daily_demand":
                round(
                    daily_demand,
                    2,
                ),

            "demand_std":
                round(
                    demand_std,
                    2,
                ),

            "lead_time_days":
                round(
                    lead_time,
                    2,
                ),

            "lead_time_demand":
                round(
                    lead_time_demand,
                    2,
                ),

            "safety_stock":
                round(
                    safety_stock,
                    2,
                ),

            "reorder_point":
                round(
                    reorder_point,
                    2,
                ),

            "days_of_inventory":
                round(
                    days_of_inventory,
                    2,
                )
                if np.isfinite(
                    days_of_inventory
                )
                else None,

            "minimum_stock":
                round(
                    minimum_stock,
                    2,
                ),

            "maximum_stock":
                round(
                    maximum_stock,
                    2,
                ),

            "recommended_quantity":
                recommended_quantity,

            "stockout_risk":
                stockout_risk,

            "inventory_status":
                inventory_status,

        }

    # ========================================================
    # ANALYZE ALL PRODUCTS
    # ========================================================

    def analyze_all_products(self):

        results = []

        for product_id in (
            self.products[
                "product_id"
            ].unique()
        ):

            try:

                result = (
                    self.analyze_product(
                        product_id
                    )
                )

                results.append(
                    result
                )

            except Exception as e:

                print(
                    f"Error analyzing "
                    f"{product_id}: "
                    f"{e}"
                )

        return pd.DataFrame(
            results
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = (
        InventoryEngine()
    )

    # --------------------------------------------------------
    # Single SKU
    # --------------------------------------------------------

    result = (
        engine.analyze_product(
            "PRD0044"
        )
    )

    print("\n")
    print("=" * 65)
    print("INVENTORY DECISION — PRD0044")
    print("=" * 65)

    for key, value in result.items():

        print(
            f"{key:25}: {value}"
        )

    # --------------------------------------------------------
    # All products
    # --------------------------------------------------------

    print("\n")
    print("=" * 65)
    print("ALL PRODUCT INVENTORY ANALYSIS")
    print("=" * 65)

    results = (
        engine.analyze_all_products()
    )

    print(
        results[
            [
                "product_id",
                "forecast_7d",
                "current_stock",
                "reorder_point",
                "days_of_inventory",
                "recommended_quantity",
                "stockout_risk",
                "inventory_status",
            ]
        ]
        .sort_values(
            "recommended_quantity",
            ascending=False,
        )
        .head(20)
        .to_string(
            index=False
        )
    )

    print(
        f"\nProducts analyzed: "
        f"{len(results)}"
    )

