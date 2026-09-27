
from pathlib import Path
import json
import pickle

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

MODEL_PATH = (
    MODEL_DIR
    / "demand_forecast_model.pkl"
)

METADATA_PATH = (
    MODEL_DIR
    / "demand_model_metadata.json"
)

DATASET_PATH = (
    DATA_DIR
    / "demand_ml_dataset.csv"
)


class DemandForecaster:

    def __init__(self):

        print("Loading demand forecasting model...")

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        with open(
            MODEL_PATH,
            "rb",
        ) as f:

            loaded_model = pickle.load(f)

        # ----------------------------------------------------
        # Support BOTH model formats
        #
        # Format 1:
        # {
        #     "model": model,
        #     "feature_columns": [...],
        #     "model_name": "HistGradientBoosting"
        # }
        #
        # Format 2:
        # sklearn Pipeline
        # ----------------------------------------------------

        if isinstance(
            loaded_model,
            dict,
        ):

            self.model = loaded_model[
                "model"
            ]

            self.feature_columns = (
                loaded_model[
                    "feature_columns"
                ]
            )

            self.model_name = (
                loaded_model.get(
                    "model_name",
                    "Unknown",
                )
            )

            self.model_format = (
                "model_package"
            )

        else:

            # Existing sklearn Pipeline
            self.model = loaded_model

            self.feature_columns = None

            self.model_name = (
                type(
                    loaded_model
                ).__name__
            )

            self.model_format = (
                "sklearn_pipeline"
            )

        # ----------------------------------------------------
        # Load metadata
        # ----------------------------------------------------

        if METADATA_PATH.exists():

            with open(
                METADATA_PATH,
                "r",
            ) as f:

                self.metadata = json.load(
                    f
                )

        else:

            self.metadata = {}

        # ----------------------------------------------------
        # Load ML dataset
        # ----------------------------------------------------

        self.dataset = pd.read_csv(
            DATASET_PATH
        )

        self.dataset["date"] = (
            pd.to_datetime(
                self.dataset["date"]
            )
        )

        self.dataset = (
            self.dataset
            .sort_values(
                [
                    "date",
                    "product_id",
                ]
            )
            .reset_index(
                drop=True
            )
        )

        print(
            f"Model loaded: "
            f"{self.model_name}"
        )

        print(
            f"Model format: "
            f"{self.model_format}"
        )

    # ========================================================
    # GET LATEST PRODUCT DATA
    # ========================================================

    def _get_latest_product_data(
        self,
        product_id: str,
    ):

        product_data = (
            self.dataset[
                self.dataset[
                    "product_id"
                ]
                == product_id
            ]
            .sort_values(
                "date"
            )
        )

        if product_data.empty:

            raise ValueError(
                f"Product not found: "
                f"{product_id}"
            )

        return product_data.iloc[-1]

    # ========================================================
    # PREPARE FEATURES
    # ========================================================

    def _prepare_features(
        self,
        row,
    ):

        original_features = (
            self.metadata.get(
                "original_features"
            )
        )

        categorical_features = (
            self.metadata.get(
                "categorical_features",
                [],
            )
        )

        # ----------------------------------------------------
        # If metadata is available
        # ----------------------------------------------------

        if original_features:

            features = pd.DataFrame(
                [
                    row[
                        original_features
                    ]
                ]
            )

        else:

            # Fallback
            features = pd.DataFrame(
                [row]
            )

        # ----------------------------------------------------
        # Existing Pipeline
        #
        # The pipeline already performs
        # preprocessing, so DON'T one-hot
        # encode here.
        # ----------------------------------------------------

        if (
            self.model_format
            == "sklearn_pipeline"
        ):

            return features

        # ----------------------------------------------------
        # Model package format
        # ----------------------------------------------------

        if categorical_features:

            features = pd.get_dummies(
                features,
                columns=
                    categorical_features,
                dtype=float,
            )

        # ----------------------------------------------------
        # Match training feature order
        # ----------------------------------------------------

        features = features.reindex(
            columns=
                self.feature_columns,
            fill_value=0,
        )

        return features

    # ========================================================
    # FORECAST ONE PRODUCT
    # ========================================================

    def forecast_product(
        self,
        product_id: str,
    ):

        row = (
            self._get_latest_product_data(
                product_id
            )
        )

        features = (
            self._prepare_features(
                row
            )
        )

        prediction = (
            self.model.predict(
                features
            )[0]
        )

        prediction = max(
            0,
            float(prediction),
        )

        forecast_days = (
            self.metadata.get(
                "forecast_horizon_days",
                7,
            )
        )

        daily_demand = (
            prediction
            / forecast_days
        )

        return {
            "product_id":
                product_id,

            "forecast_horizon_days":
                forecast_days,

            "predicted_demand":
                round(
                    prediction,
                    2,
                ),

            "average_daily_demand":
                round(
                    daily_demand,
                    2,
                ),

            "model":
                self.model_name,

            "data_date":
                str(
                    row[
                        "date"
                    ].date()
                ),
        }

    # ========================================================
    # FORECAST ALL PRODUCTS
    # ========================================================

    def forecast_all_products(
        self,
    ):

        product_ids = (
            self.dataset[
                "product_id"
            ]
            .unique()
        )

        forecasts = []

        for product_id in product_ids:

            try:

                result = (
                    self.forecast_product(
                        product_id
                    )
                )

                forecasts.append(
                    result
                )

            except Exception as e:

                print(
                    f"Skipping "
                    f"{product_id}: "
                    f"{e}"
                )

        return pd.DataFrame(
            forecasts
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    forecaster = (
        DemandForecaster()
    )

    print("\n")
    print("=" * 60)
    print("SINGLE PRODUCT FORECAST")
    print("=" * 60)

    result = (
        forecaster.forecast_product(
            "PRD0044"
        )
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print("\n")
    print("=" * 60)
    print("ALL PRODUCT FORECASTS")
    print("=" * 60)

    forecasts = (
        forecaster.forecast_all_products()
    )

    print(
        forecasts.head(10).to_string(
            index=False
        )
    )

    print(
        f"\nTotal products forecasted: "
        f"{len(forecasts)}"
    )

