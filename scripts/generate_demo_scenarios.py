from pathlib import Path
import pandas as pd


OUTPUT_DIR = Path("data/demo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


SCENARIOS = [

    {
        "scenario_id": "SCN001",
        "product_id": "PRD0044",
        "scenario": "HEALTHY",
        "risk_level": "LOW",
        "primary_risk": "NONE",
        "current_stock": 538,
        "forecast_7d": 15,
        "days_of_inventory": 244,
        "expiry_quantity": 0,
        "days_to_expiry": None,
        "recommended_action": "NO ACTION",
        "recommended_quantity": 0,
        "explanation": "Inventory is sufficient for forecasted demand with no immediate stock or expiry concern."
    },

    {
        "scenario_id": "SCN002",
        "product_id": "PRD0021",
        "scenario": "STOCKOUT",
        "risk_level": "CRITICAL",
        "primary_risk": "STOCKOUT",
        "current_stock": 8,
        "forecast_7d": 42,
        "days_of_inventory": 1.3,
        "expiry_quantity": 0,
        "days_to_expiry": None,
        "recommended_action": "EMERGENCY REORDER",
        "recommended_quantity": 100,
        "explanation": "Current stock is insufficient to cover near-term demand. Immediate replenishment is required."
    },

    {
        "scenario_id": "SCN003",
        "product_id": "PRD0017",
        "scenario": "REORDER",
        "risk_level": "HIGH",
        "primary_risk": "STOCKOUT",
        "current_stock": 35,
        "forecast_7d": 70,
        "days_of_inventory": 3.5,
        "expiry_quantity": 0,
        "days_to_expiry": None,
        "recommended_action": "REORDER SKU",
        "recommended_quantity": 120,
        "explanation": "Forecasted demand is approaching available inventory and replenishment should be initiated."
    },

    {
        "scenario_id": "SCN004",
        "product_id": "PRD0035",
        "scenario": "OVERSTOCK",
        "risk_level": "HIGH",
        "primary_risk": "OVERSTOCK",
        "current_stock": 8500,
        "forecast_7d": 80,
        "days_of_inventory": 743,
        "expiry_quantity": 0,
        "days_to_expiry": 180,
        "recommended_action": "REDUCE PROCUREMENT",
        "recommended_quantity": 0,
        "explanation": "Inventory is significantly higher than expected demand. New procurement should be reduced."
    },

    {
        "scenario_id": "SCN005",
        "product_id": "PRD0058",
        "scenario": "EXPIRY",
        "risk_level": "CRITICAL",
        "primary_risk": "EXPIRY",
        "current_stock": 4200,
        "forecast_7d": 25,
        "days_of_inventory": 1176,
        "expiry_quantity": 3500,
        "days_to_expiry": 5,
        "recommended_action": "IMMEDIATE CLEARANCE",
        "recommended_quantity": 0,
        "explanation": "A large quantity is approaching expiry within five days and should be cleared immediately."
    },

    {
        "scenario_id": "SCN006",
        "product_id": "PRD0072",
        "scenario": "EXPIRY_OVERSTOCK",
        "risk_level": "CRITICAL",
        "primary_risk": "EXPIRY",
        "current_stock": 7800,
        "forecast_7d": 30,
        "days_of_inventory": 1820,
        "expiry_quantity": 6800,
        "days_to_expiry": 10,
        "recommended_action": "PROMOTION / BUNDLE",
        "recommended_quantity": 0,
        "explanation": "Excess inventory combined with approaching expiry makes promotion or bundle campaigns appropriate."
    },

    {
        "scenario_id": "SCN007",
        "product_id": "PRD0047",
        "scenario": "HIGH_DEMAND",
        "risk_level": "MEDIUM",
        "primary_risk": "DEMAND",
        "current_stock": 250,
        "forecast_7d": 180,
        "days_of_inventory": 9.7,
        "expiry_quantity": 0,
        "days_to_expiry": 200,
        "recommended_action": "INCREASE PROCUREMENT",
        "recommended_quantity": 500,
        "explanation": "Demand forecast is elevated and inventory coverage is relatively low. Procurement should be increased."
    },

    {
        "scenario_id": "SCN008",
        "product_id": "PRD0090",
        "scenario": "LOW_DEMAND_OVERSTOCK",
        "risk_level": "MEDIUM",
        "primary_risk": "OVERSTOCK",
        "current_stock": 5000,
        "forecast_7d": 20,
        "days_of_inventory": 1750,
        "expiry_quantity": 500,
        "days_to_expiry": 90,
        "recommended_action": "PROMOTION",
        "recommended_quantity": 0,
        "explanation": "Demand is low relative to available inventory. A targeted promotion can reduce excess stock."
    },

    {
        "scenario_id": "SCN009",
        "product_id": "PRD0062",
        "scenario": "SUPPLIER_RISK",
        "risk_level": "HIGH",
        "primary_risk": "SUPPLIER",
        "current_stock": 90,
        "forecast_7d": 70,
        "days_of_inventory": 9,
        "expiry_quantity": 0,
        "days_to_expiry": 150,
        "recommended_action": "SUPPLIER PLANNING",
        "recommended_quantity": 250,
        "explanation": "Inventory coverage is limited while supplier lead time creates additional replenishment risk."
    },

    {
        "scenario_id": "SCN010",
        "product_id": "PRD0010",
        "scenario": "CRITICAL_COMBINED",
        "risk_level": "CRITICAL",
        "primary_risk": "STOCKOUT + EXPIRY",
        "current_stock": 40,
        "forecast_7d": 100,
        "days_of_inventory": 2.8,
        "expiry_quantity": 25,
        "days_to_expiry": 4,
        "recommended_action": "IMMEDIATE INTERVENTION",
        "recommended_quantity": 150,
        "explanation": "Demand pressure and near-term expiry require simultaneous replenishment and inventory clearance."
    }
]


def main():

    df = pd.DataFrame(SCENARIOS)

    output_file = OUTPUT_DIR / "demo_cases.csv"

    df.to_csv(output_file, index=False)

    print("=" * 70)
    print("COOKD INVENTORY AI — DEMO SCENARIOS")
    print("=" * 70)

    print(f"\nGenerated scenarios: {len(df)}")
    print(f"Saved → {output_file}")

    print("\nScenario distribution:")
    print(df["scenario"].value_counts())

    print("\nRisk distribution:")
    print(df["risk_level"].value_counts())

    print("\nAction distribution:")
    print(df["recommended_action"].value_counts())


if __name__ == "__main__":
    main()