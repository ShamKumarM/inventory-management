"""
COOKD INVENTORY AI
Risk Engine

Calculates:
    1. Stockout Risk
    2. Overstock Risk
    3. Expiry Risk

Consumes inventory decisions from InventoryEngine.
"""

from pathlib import Path
import pandas as pd
import numpy as np

from src.inventory.inventory_engine import InventoryEngine


class RiskEngine:

    def __init__(self):

        print("Initializing Risk Engine...")

        self.inventory_engine = InventoryEngine()

        self.base_dir = Path(__file__).resolve().parents[2]

        self.batches_path = (
            self.base_dir
            / "data"
            / "synthetic"
            / "inventory_batches.csv"
        )

        self.batches = pd.read_csv(
            self.batches_path
        )

        self.batches["expiry_date"] = pd.to_datetime(
            self.batches["expiry_date"]
        )

        print(
            f"Inventory batches loaded: "
            f"{len(self.batches):,}"
        )

    # =========================================================
    # STOCKOUT RISK
    # =========================================================

    def calculate_stockout_risk(
        self,
        decision: dict,
    ):

        current_stock = float(
            decision["current_stock"]
        )

        reorder_point = float(
            decision["reorder_point"]
        )

        daily_demand = max(
            float(decision["daily_demand"]),
            0.01,
        )

        demand_std = float(
            decision["demand_std"]
        )

        lead_time = float(
            decision["lead_time_days"]
        )

        supplier_reliability = float(
            decision["supplier_reliability"]
        )

        # -----------------------------------------------------
        # 1. Stock coverage
        # -----------------------------------------------------

        days_of_inventory = (
            current_stock
            / daily_demand
        )

        # -----------------------------------------------------
        # 2. Coverage risk
        # -----------------------------------------------------

        if days_of_inventory <= lead_time:
            coverage_score = 100

        elif days_of_inventory <= lead_time * 1.5:
            coverage_score = 80

        elif days_of_inventory <= lead_time * 2:
            coverage_score = 55

        elif days_of_inventory <= lead_time * 3:
            coverage_score = 30

        else:
            coverage_score = 10

        # -----------------------------------------------------
        # 3. Reorder-point risk
        # -----------------------------------------------------

        if current_stock <= reorder_point:
            reorder_score = 100

        elif current_stock <= reorder_point * 1.5:
            reorder_score = 70

        elif current_stock <= reorder_point * 2:
            reorder_score = 40

        else:
            reorder_score = 10

        # -----------------------------------------------------
        # 4. Demand volatility
        # -----------------------------------------------------

        volatility_ratio = (
            demand_std
            / daily_demand
        )

        if volatility_ratio >= 1:
            volatility_score = 100

        elif volatility_ratio >= 0.75:
            volatility_score = 75

        elif volatility_ratio >= 0.5:
            volatility_score = 50

        elif volatility_ratio >= 0.25:
            volatility_score = 25

        else:
            volatility_score = 10

        # -----------------------------------------------------
        # 5. Supplier risk
        # -----------------------------------------------------

        supplier_score = (
            1 - supplier_reliability
        ) * 100

        # -----------------------------------------------------
        # Final weighted score
        # -----------------------------------------------------

        score = (
            coverage_score * 0.40
            + reorder_score * 0.30
            + volatility_score * 0.15
            + supplier_score * 0.15
        )

        score = round(
            min(max(score, 0), 100),
            2,
        )

        level = self._risk_level(score)

        return {
            "score": score,
            "level": level,
            "days_of_inventory": round(
                days_of_inventory,
                2,
            ),
        }

    # =========================================================
    # OVERSTOCK RISK
    # =========================================================

    def calculate_overstock_risk(
        self,
        decision: dict,
    ):

        current_stock = float(
            decision["current_stock"]
        )

        maximum_stock = float(
            decision["maximum_stock"]
        )

        forecast_7d = float(
            decision["forecast_7d"]
        )

        daily_demand = max(
            float(decision["daily_demand"]),
            0.01,
        )

        # -----------------------------------------------------
        # 1. Capacity utilization
        # -----------------------------------------------------

        stock_utilization = (
            current_stock
            / max(maximum_stock, 1)
        )

        if stock_utilization >= 1:
            capacity_score = 100

        elif stock_utilization >= 0.9:
            capacity_score = 90

        elif stock_utilization >= 0.75:
            capacity_score = 70

        elif stock_utilization >= 0.6:
            capacity_score = 40

        else:
            capacity_score = 10

        # -----------------------------------------------------
        # 2. Days of inventory
        # -----------------------------------------------------

        days_inventory = (
            current_stock
            / daily_demand
        )

        if days_inventory >= 180:
            days_score = 100

        elif days_inventory >= 120:
            days_score = 85

        elif days_inventory >= 90:
            days_score = 70

        elif days_inventory >= 60:
            days_score = 45

        elif days_inventory >= 30:
            days_score = 20

        else:
            days_score = 5

        # -----------------------------------------------------
        # 3. Demand coverage
        # -----------------------------------------------------

        expected_30d_demand = (
            daily_demand * 30
        )

        coverage_ratio = (
            current_stock
            / max(
                expected_30d_demand,
                1,
            )
        )

        if coverage_ratio >= 6:
            demand_score = 100

        elif coverage_ratio >= 4:
            demand_score = 80

        elif coverage_ratio >= 3:
            demand_score = 60

        elif coverage_ratio >= 2:
            demand_score = 35

        else:
            demand_score = 10

        # -----------------------------------------------------
        # Final score
        # -----------------------------------------------------

        score = (
            capacity_score * 0.40
            + days_score * 0.40
            + demand_score * 0.20
        )

        score = round(
            min(max(score, 0), 100),
            2,
        )

        level = self._risk_level(score)

        return {
            "score": score,
            "level": level,
            "stock_utilization": round(
                stock_utilization * 100,
                2,
            ),
            "days_of_inventory": round(
                days_inventory,
                2,
            ),
        }

    # =========================================================
    # EXPIRY RISK
    # =========================================================

    def calculate_expiry_risk(
        self,
        product_id: str,
        daily_demand: float,
    ):

        product_batches = self.batches[
            self.batches["product_id"]
            == product_id
        ].copy()

        if product_batches.empty:

            return {
                "score": 0,
                "level": "LOW",
                "expiring_quantity": 0,
                "nearest_expiry_days": None,
            }

        today = pd.Timestamp(
            "2026-09-30"
        )

        product_batches[
            "days_to_expiry"
        ] = (
            product_batches[
                "expiry_date"
            ]
            - today
        ).dt.days

        # Only active/future batches
        active_batches = product_batches[
            (product_batches["days_to_expiry"] >= 0)
            & (product_batches["batch_status"] == "active")
        ].copy()

        if active_batches.empty:

            return {
                "score": 100,
                "level": "CRITICAL",
                "expiring_quantity": 0,
                "nearest_expiry_days": 0,
            }

        # -----------------------------------------------------
        # Expiry windows
        # -----------------------------------------------------

        expiring_30 = active_batches[
            active_batches[
                "days_to_expiry"
            ] <= 30
        ]

        expiring_60 = active_batches[
            active_batches[
                "days_to_expiry"
            ] <= 60
        ]

        expiring_90 = active_batches[
            active_batches[
                "days_to_expiry"
            ] <= 90
        ]

        qty_30 = float(
            expiring_30[
                "available_quantity"
            ].sum()
        )

        qty_60 = float(
            expiring_60[
                "available_quantity"
            ].sum()
        )

        qty_90 = float(
            expiring_90[
                "available_quantity"
            ].sum()
        )

        nearest_expiry = int(
            active_batches[
                "days_to_expiry"
            ].min()
        )

        # -----------------------------------------------------
        # Compare expiring stock with demand
        # -----------------------------------------------------

        demand_30 = max(
            daily_demand * 30,
            1,
        )

        expiry_pressure = (
            qty_30 / demand_30
        )

        if nearest_expiry <= 7:
            score = 100

        elif nearest_expiry <= 14:
            score = 90

        elif nearest_expiry <= 30:
            score = 75

        elif nearest_expiry <= 60:
            score = 50

        elif nearest_expiry <= 90:
            score = 30

        else:
            score = 10

        # Increase risk when a lot of stock
        # is approaching expiry.

        if expiry_pressure >= 3:
            score += 20

        elif expiry_pressure >= 2:
            score += 10

        score = round(
            min(score, 100),
            2,
        )

        level = self._risk_level(score)

        return {
            "score": score,
            "level": level,
            "expiring_quantity": round(
                qty_30,
                2,
            ),
            "expiring_quantity_60d": round(
                qty_60,
                2,
            ),
            "expiring_quantity_90d": round(
                qty_90,
                2,
            ),
            "nearest_expiry_days":
                nearest_expiry,
        }

    # =========================================================
    # COMPLETE PRODUCT RISK
    # =========================================================

    def analyze_product(
        self,
        product_id: str,
    ):

        decision = (
            self.inventory_engine
            .analyze_product(
                product_id
            )
        )

        stockout = (
            self.calculate_stockout_risk(
                decision
            )
        )

        overstock = (
            self.calculate_overstock_risk(
                decision
            )
        )

        expiry = (
            self.calculate_expiry_risk(
                product_id,
                decision["daily_demand"],
            )
        )

        # -----------------------------------------------------
        # Overall risk
        # -----------------------------------------------------

        overall_score = max(
            stockout["score"],
            overstock["score"],
            expiry["score"],
        )

        if overall_score >= 80:
            overall_level = "CRITICAL"

        elif overall_score >= 60:
            overall_level = "HIGH"

        elif overall_score >= 30:
            overall_level = "MEDIUM"

        else:
            overall_level = "LOW"

        # -----------------------------------------------------
        # Primary risk
        # -----------------------------------------------------

        risks = {
            "STOCKOUT": stockout["score"],
            "OVERSTOCK": overstock["score"],
            "EXPIRY": expiry["score"],
        }

        primary_risk = max(
            risks,
            key=risks.get,
        )

        return {
            "product_id": product_id,

            "stockout": stockout,

            "overstock": overstock,

            "expiry": expiry,

            "overall_score": round(
                overall_score,
                2,
            ),

            "overall_level":
                overall_level,

            "primary_risk":
                primary_risk,
        }

    # =========================================================
    # ALL PRODUCTS
    # =========================================================

    def analyze_all_products(self):

        products = (
            self.inventory_engine
            .products["product_id"]
            .tolist()
        )

        results = []

        for product_id in products:

            try:

                result = (
                    self.analyze_product(
                        product_id
                    )
                )

                results.append(result)

            except Exception as e:

                print(
                    f"Error analyzing "
                    f"{product_id}: {e}"
                )

        return results

    # =========================================================
    # RISK LEVEL
    # =========================================================

    @staticmethod
    def _risk_level(score):

        if score >= 80:
            return "CRITICAL"

        if score >= 60:
            return "HIGH"

        if score >= 30:
            return "MEDIUM"

        return "LOW"


# =============================================================
# DEMO
# =============================================================

if __name__ == "__main__":

    engine = RiskEngine()

    product_id = "PRD0044"

    result = engine.analyze_product(
        product_id
    )

    print()
    print("=" * 70)
    print(
        f"AI RISK ANALYSIS — {product_id}"
    )
    print("=" * 70)

    print()
    print("STOCKOUT RISK")
    print("-" * 40)

    print(
        f"Score       : "
        f"{result['stockout']['score']}"
    )

    print(
        f"Level       : "
        f"{result['stockout']['level']}"
    )

    print(
        f"Inventory   : "
        f"{result['stockout']['days_of_inventory']} days"
    )

    print()
    print("OVERSTOCK RISK")
    print("-" * 40)

    print(
        f"Score       : "
        f"{result['overstock']['score']}"
    )

    print(
        f"Level       : "
        f"{result['overstock']['level']}"
    )

    print(
        f"Utilization : "
        f"{result['overstock']['stock_utilization']}%"
    )

    print()
    print("EXPIRY RISK")
    print("-" * 40)

    print(
        f"Score       : "
        f"{result['expiry']['score']}"
    )

    print(
        f"Level       : "
        f"{result['expiry']['level']}"
    )

    print(
        f"30d Qty     : "
        f"{result['expiry']['expiring_quantity']}"
    )

    print(
        f"Nearest     : "
        f"{result['expiry']['nearest_expiry_days']} days"
    )

    print()
    print("=" * 70)

    print(
        f"OVERALL RISK : "
        f"{result['overall_level']}"
    )

    print(
        f"RISK SCORE   : "
        f"{result['overall_score']}"
    )

    print(
        f"PRIMARY RISK : "
        f"{result['primary_risk']}"
    )

    print("=" * 70)