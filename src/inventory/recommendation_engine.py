"""
COOKD INVENTORY AI
Recommendation Engine

Converts inventory + risk signals into
business recommendations.
"""

from src.inventory.risk_engine import RiskEngine


class RecommendationEngine:

    def __init__(self):

        print("Initializing Recommendation Engine...")

        self.risk_engine = RiskEngine()

    # =========================================================
    # MAIN RECOMMENDATION
    # =========================================================

    def recommend(self, product_id: str):

        risk = self.risk_engine.analyze_product(
            product_id
        )

        inventory = (
            self.risk_engine
            .inventory_engine
            .analyze_product(
                product_id
            )
        )

        stockout = risk["stockout"]
        overstock = risk["overstock"]
        expiry = risk["expiry"]

        # -----------------------------------------------------
        # EXPIRY HAS HIGHEST OPERATIONAL PRIORITY
        # -----------------------------------------------------

        if expiry["score"] >= 80:

            return self._expiry_recommendation(
                product_id,
                risk,
                inventory,
            )

        # -----------------------------------------------------
        # STOCKOUT
        # -----------------------------------------------------

        if stockout["score"] >= 60:

            return self._reorder_recommendation(
                product_id,
                risk,
                inventory,
            )

        # -----------------------------------------------------
        # OVERSTOCK
        # -----------------------------------------------------

        if overstock["score"] >= 60:

            return self._overstock_recommendation(
                product_id,
                risk,
                inventory,
            )

        # -----------------------------------------------------
        # HEALTHY
        # -----------------------------------------------------

        return {
            "product_id": product_id,
            "priority": "LOW",
            "action": "MONITOR",
            "recommendation":
                "Inventory is currently within "
                "acceptable operating levels.",
            "recommended_quantity": 0,
            "supplier": None,
        }

    # =========================================================
    # EXPIRY RECOMMENDATION
    # =========================================================

    def _expiry_recommendation(
        self,
        product_id,
        risk,
        inventory,
    ):

        expiry = risk["expiry"]

        quantity = expiry[
            "expiring_quantity"
        ]

        days = expiry[
            "nearest_expiry_days"
        ]

        if days <= 7:

            priority = "CRITICAL"

            action = (
                "IMMEDIATE CLEARANCE"
            )

        elif days <= 14:

            priority = "HIGH"

            action = (
                "PROMOTION / BUNDLE"
            )

        else:

            priority = "MEDIUM"

            action = (
                "PROMOTIONAL CAMPAIGN"
            )

        recommendation = (
            f"{action}. "
            f"{quantity:.0f} units are "
            f"approaching expiry within "
            f"{days} days."
        )

        return {
            "product_id": product_id,

            "priority": priority,

            "action": action,

            "recommendation":
                recommendation,

            "recommended_quantity": 0,

            "supplier": None,

            "expiry_quantity":
                quantity,

            "days_to_expiry":
                days,

            "risk_score":
                expiry["score"],
        }

    # =========================================================
    # REORDER RECOMMENDATION
    # =========================================================

    def _reorder_recommendation(
        self,
        product_id,
        risk,
        inventory,
    ):

        current_stock = float(
            inventory["current_stock"]
        )

        reorder_point = float(
            inventory["reorder_point"]
        )

        maximum_stock = float(
            inventory["maximum_stock"]
        )

        daily_demand = float(
            inventory["daily_demand"]
        )

        # -----------------------------------------------------
        # Target inventory
        # -----------------------------------------------------

        target_stock = max(
            reorder_point,
            daily_demand * 30,
        )

        target_stock = min(
            target_stock,
            maximum_stock,
        )

        recommended_quantity = max(
            0,
            target_stock - current_stock,
        )

        supplier = inventory[
            "supplier"
        ]

        return {
            "product_id": product_id,

            "priority": risk[
                "stockout"
            ]["level"],

            "action": "REORDER",

            "recommendation":
                f"Reorder approximately "
                f"{recommended_quantity:.0f} "
                f"units from "
                f"{supplier}.",

            "recommended_quantity":
                round(
                    recommended_quantity,
                    0,
                ),

            "supplier":
                supplier,

            "risk_score":
                risk[
                    "stockout"
                ]["score"],
        }

    # =========================================================
    # OVERSTOCK RECOMMENDATION
    # =========================================================

    def _overstock_recommendation(
        self,
        product_id,
        risk,
        inventory,
    ):

        current_stock = float(
            inventory["current_stock"]
        )

        maximum_stock = float(
            inventory["maximum_stock"]
        )

        excess_stock = max(
            0,
            current_stock
            - maximum_stock * 0.75,
        )

        if risk["overstock"]["score"] >= 80:

            action = (
                "PROMOTION / BUNDLE"
            )

            priority = "HIGH"

        else:

            action = (
                "MONITOR INVENTORY"
            )

            priority = "MEDIUM"

        recommendation = (
            f"{action}. "
            f"Approximately "
            f"{excess_stock:.0f} units "
            f"are above the preferred "
            f"inventory level."
        )

        return {
            "product_id": product_id,

            "priority": priority,

            "action": action,

            "recommendation":
                recommendation,

            "recommended_quantity": 0,

            "supplier": None,

            "excess_quantity":
                round(
                    excess_stock,
                    0,
                ),

            "risk_score":
                risk[
                    "overstock"
                ]["score"],
        }

    # =========================================================
    # ALL PRODUCTS
    # =========================================================

    def recommend_all(self):

        results = []

        products = (
            self.risk_engine
            .inventory_engine
            .products["product_id"]
            .tolist()
        )

        for product_id in products:

            try:

                result = self.recommend(
                    product_id
                )

                results.append(result)

            except Exception as e:

                print(
                    f"Error processing "
                    f"{product_id}: {e}"
                )

        return results


# =============================================================
# DEMO
# =============================================================

if __name__ == "__main__":

    engine = RecommendationEngine()

    product_id = "PRD0044"

    result = engine.recommend(
        product_id
    )

    print()
    print("=" * 70)
    print(
        f"AI RECOMMENDATION — {product_id}"
    )
    print("=" * 70)

    for key, value in result.items():

        print(
            f"{key:25}: {value}"
        )

    print("=" * 70)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print()
    print("AI DECISION")
    print("-" * 50)

    print(
        f"Priority     : "
        f"{result['priority']}"
    )

    print(
        f"Action       : "
        f"{result['action']}"
    )

    print(
        f"Recommendation:")
    print(
        f"  {result['recommendation']}"
    )