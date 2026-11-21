"""Retraining logic for the food price model.

The saved model is a scikit-learn Pipeline (preprocessing + regressor).
- If the regressor is an SGDRegressor, it continues training on the new rows with partial_fit.
- Otherwise (our best model is a RandomForestRegressor) it is refit on the original data plus the new rows.

The retrained model and the grown dataset live in memory: the committed best_model.pkl and training data are
never overwritten (Render's free tier would lose disk writes on restart anyway).
"""
from io import BytesIO
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best_model.pkl"
DATA_PATH = BASE_DIR / "training_data.csv.gz"

CATEGORICAL = ["commodity", "category", "market", "admin2", "admin1"]
NUMERIC = ["latitude", "longitude", "year", "month"]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "price"
PRICE_CAP = 6000  # same 99.9th percentile cap used in the notebook


def load_model():
    return joblib.load(MODEL_PATH)


_training_data = None  # original data + every uploaded batch, kept in memory


def load_training_data() -> pd.DataFrame:
    global _training_data
    if _training_data is None:
        _training_data = pd.read_csv(DATA_PATH)
    return _training_data


def clean_new_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Apply the notebook's cleaning steps to an uploaded CSV.

    Accepts either the cleaned training columns (9 features + price) or the raw WFP
    format (with date, unit, pricetype...), which is filtered and split the same way.
    """
    df = raw.copy()
    if "unit" in df.columns:
        df = df[df["unit"] == "KG"]
    if "pricetype" in df.columns:
        df = df[df["pricetype"] == "Retail"]
    if "date" in df.columns and not {"year", "month"} <= set(df.columns):
        dates = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = dates.dt.year
        df["month"] = dates.dt.month

    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df = df[FEATURES + [TARGET]].dropna()
    for col in NUMERIC + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    df = df[(df[TARGET] > 0) & (df[TARGET] <= PRICE_CAP)]
    df[["year", "month"]] = df[["year", "month"]].astype(int)

    if df.empty:
        raise ValueError("No valid rows left after cleaning (need KG retail prices between 0 and 6000 RWF).")
    return df


def retrain(csv_bytes: bytes, current_model):
    """Retrain the model on an uploaded CSV. Returns (new_model, report dict, cleaned new rows)."""
    new_rows = clean_new_data(pd.read_csv(BytesIO(csv_bytes)))
    X_new, y_new = new_rows[FEATURES], new_rows[TARGET]
    mse_before = mean_squared_error(y_new, current_model.predict(X_new))

    global _training_data
    regressor = current_model.named_steps["model"]
    if isinstance(regressor, SGDRegressor):
        # gradient descent model: keep the learned weights and continue training on the new rows
        X_new_p = current_model.named_steps["preprocess"].transform(X_new)
        regressor.partial_fit(X_new_p, y_new)
        new_model = current_model
        method = "partial_fit on new rows (SGDRegressor)"
        total_rows = len(new_rows)
    else:
        # tree / closed-form model: refit from scratch on original data + new rows
        combined = pd.concat([load_training_data(), new_rows], ignore_index=True)
        new_model = clone(current_model)
        new_model.fit(combined[FEATURES], combined[TARGET])
        _training_data = combined
        method = f"refit on original + new rows ({type(regressor).__name__})"
        total_rows = len(combined)

    mse_after = mean_squared_error(y_new, new_model.predict(X_new))

    report = {
        "method": method,
        "new_rows_used": len(new_rows),
        "rows_trained_on": total_rows,
        "mse_on_new_rows_before": round(float(mse_before), 2),
        "mse_on_new_rows_after": round(float(mse_after), 2),
    }
    return new_model, report, new_rows
