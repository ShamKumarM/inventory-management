import json
import pickle

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


from src.config import SYNTHETIC_DIR


RANDOM_STATE = 42


def calculate_mape(y_true, y_pred):

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mask = y_true != 0

    if mask.sum() == 0:
        return 0.0

    return (
        np.mean(
            np.abs(
                (
                    y_true[mask]
                    - y_pred[mask]
                )
                / y_true[mask]
            )
        )
        * 100
    )


def evaluate_model(name, y_true, predictions):

    mae = mean_absolute_error(
        y_true,
        predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            predictions,
        )
    )

    mape = calculate_mape(
        y_true,
        predictions,
    )

    print(f"\n{name}")
    print("-" * 45)
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAPE: {mape:.2f}%")

    return {
        "model": name,
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape),
    }


def train():

    print("=" * 65)
    print("COOKD DEMAND FORECASTING MODEL")
    print("=" * 65)

    # =====================================================
    # LOAD DATA
    # =====================================================

    path = (
        SYNTHETIC_DIR
        / "demand_ml_dataset.csv"
    )

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(
        df["date"]
    )

    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    print(
        f"\nDataset: {len(df):,} rows"
    )

    # =====================================================
    # FEATURES
    # =====================================================

    target = "target_7d"

    categorical_features = [
        "product_id",
        "category",
        "popularity",
    ]

    numeric_features = [
        "selling_price",
        "cost_price",
        "shelf_life_days",

        "day_of_week",
        "day_of_month",
        "month",
        "week_of_year",
        "quarter",
        "is_weekend",

        "lag_1",
        "lag_7",
        "lag_14",
        "lag_28",

        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_28",

        "rolling_std_7",
        "rolling_std_28",
    ]

    features = (
        categorical_features
        + numeric_features
    )

    X = df[features]
    y = df[target]

    # =====================================================
    # CHRONOLOGICAL SPLIT
    # =====================================================

    unique_dates = sorted(
        df["date"].unique()
    )

    train_end = int(
        len(unique_dates) * 0.70
    )

    validation_end = int(
        len(unique_dates) * 0.85
    )

    train_dates = unique_dates[
        :train_end
    ]

    validation_dates = unique_dates[
        train_end:validation_end
    ]

    test_dates = unique_dates[
        validation_end:
    ]

    train_mask = df["date"].isin(
        train_dates
    )

    validation_mask = df["date"].isin(
        validation_dates
    )

    test_mask = df["date"].isin(
        test_dates
    )

    X_train = X[train_mask]
    y_train = y[train_mask]

    X_validation = X[
        validation_mask
    ]

    y_validation = y[
        validation_mask
    ]

    X_test = X[test_mask]
    y_test = y[test_mask]

    print(
        f"\nTrain rows:      {len(X_train):,}"
    )

    print(
        f"Validation rows: {len(X_validation):,}"
    )

    print(
        f"Test rows:       {len(X_test):,}"
    )

    print(
        f"\nTrain period:"
        f" {train_dates[0]}"
        f" → {train_dates[-1]}"
    )

    print(
        f"Test period:"
        f" {test_dates[0]}"
        f" → {test_dates[-1]}"
    )

    # =====================================================
    # PREPROCESSING
    # =====================================================

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical_features,
            ),
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
        ]
    )

    # =====================================================
    # BASELINE
    # =====================================================

    print("\n" + "=" * 65)
    print("BASELINE")
    print("=" * 65)

    baseline_predictions = (
        X_test["rolling_mean_7"]
        * 7
    )

    baseline_result = evaluate_model(
        "7-Day Moving Average Baseline",
        y_test,
        baseline_predictions,
    )

    # =====================================================
    # RANDOM FOREST
    # =====================================================

    print("\n" + "=" * 65)
    print("TRAINING RANDOM FOREST")
    print("=" * 65)

    rf_pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=150,
                    max_depth=18,
                    min_samples_leaf=2,
                    max_features="sqrt",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    rf_pipeline.fit(
        X_train,
        y_train,
    )

    rf_predictions = (
        rf_pipeline.predict(X_test)
    )

    rf_result = evaluate_model(
        "Random Forest",
        y_test,
        rf_predictions,
    )

    # =====================================================
    # HISTOGRAM GRADIENT BOOSTING
    # =====================================================

    print("\n" + "=" * 65)
    print(
        "TRAINING HISTOGRAM GRADIENT BOOSTING"
    )
    print("=" * 65)

    # HistGradientBoosting needs numeric
    # features, so use pandas one-hot encoding.

    full_encoded = pd.get_dummies(
        df[features],
        columns=categorical_features,
        dtype=float,
    )

    X_train_encoded = (
        full_encoded[train_mask]
    )

    X_test_encoded = (
        full_encoded[test_mask]
    )

    hgb_model = HistGradientBoostingRegressor(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=RANDOM_STATE,
    )

    hgb_model.fit(
        X_train_encoded,
        y_train,
    )

    hgb_predictions = (
        hgb_model.predict(
            X_test_encoded
        )
    )

    hgb_result = evaluate_model(
        "HistGradientBoosting",
        y_test,
        hgb_predictions,
    )

    # =====================================================
    # MODEL COMPARISON
    # =====================================================

    results = [
        baseline_result,
        rf_result,
        hgb_result,
    ]

    results_df = pd.DataFrame(
        results
    ).sort_values(
        "mae"
    )

    print("\n" + "=" * 65)
    print("MODEL COMPARISON")
    print("=" * 65)

    print(
        results_df.to_string(
            index=False
        )
    )

    # =====================================================
    # SELECT BEST MODEL
    # =====================================================

    best_model_name = (
        results_df.iloc[0]["model"]
    )

    print(
        f"\nBest model by MAE: "
        f"{best_model_name}"
    )

    # =====================================================
    # SAVE RESULTS
    # =====================================================

    reports_dir = (
        SYNTHETIC_DIR.parent.parent
        / "reports"
    )

    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_df.to_csv(
        reports_dir
        / "demand_model_comparison.csv",
        index=False,
    )

    # =====================================================
    # SAVE TEST PREDICTIONS
    # =====================================================

    prediction_df = df[
        test_mask
    ][
        [
            "date",
            "product_id",
            "target_7d",
        ]
    ].copy()

    prediction_df[
        "baseline_prediction"
    ] = baseline_predictions

    prediction_df[
        "random_forest_prediction"
    ] = rf_predictions

    prediction_df[
        "gradient_boosting_prediction"
    ] = hgb_predictions

    prediction_df.to_csv(
        reports_dir
        / "demand_predictions.csv",
        index=False,
    )

    # =====================================================
    # SAVE RF MODEL
    # =====================================================

    models_dir = (
        SYNTHETIC_DIR.parent.parent
        / "models"
    )

    models_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        models_dir
        / "demand_forecast_model.pkl",
        "wb",
    ) as f:

        pickle.dump(
            rf_pipeline,
            f,
        )

    # =====================================================
    # SAVE METADATA
    # =====================================================

    metadata = {
        "target": target,
        "forecast_horizon_days": 7,
        "features": features,
        "categorical_features":
            categorical_features,
        "numeric_features":
            numeric_features,
        "random_state":
            RANDOM_STATE,
        "best_model":
            best_model_name,
        "dataset_rows":
            len(df),
    }

    with open(
        models_dir
        / "demand_model_metadata.json",
        "w",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
        )

    print(
        "\nModel saved → "
        f"{models_dir}"
    )

    print(
        "\nReports saved → "
        f"{reports_dir}"
    )

    print("\nTraining complete.")


if __name__ == "__main__":
    train()