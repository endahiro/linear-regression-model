"""FastAPI service: predicts the retail price (RWF per KG) of a food commodity in a Rwandan market.

Run locally:  uv run uvicorn prediction:app --reload
Swagger UI:   http://127.0.0.1:8000/docs
"""
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

import retrain as rt

app = FastAPI(
    title="Rwanda Food Price Prediction API",
    description="Predicts the retail price (RWF/KG) of a food commodity in a Rwandan market for a given month, "
    "so cooperatives and agri-traders can decide where and when to sell.",
    version="1.0.0",
)

# CORS: only these browser origins may call the API from a web page:
#   - the deployed Render service itself (so Swagger UI at /docs works),
#   - local development: uvicorn (port 8000) and Flutter web debug (run with --web-port 8080).
# Restricted: no wildcard "*" - any other website is blocked by the browser from reading responses.
# Methods are limited to GET (docs, options) and POST (predict, retrain); headers to the ones a JSON or
# file-upload request needs. Credentials are disabled because the API uses no cookies or auth sessions.
# The Flutter mobile app is not a browser, so CORS does not apply to it.
ALLOWED_ORIGINS = [
    "https://rwanda-food-price-api.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
    allow_credentials=False,
)

# Loaded once at startup from the file committed in the repo (Render's disk is not persistent).
model = rt.load_model()
_train = rt.load_training_data()
KNOWN_VALUES = {col: sorted(_train[col].unique().tolist()) for col in rt.CATEGORICAL}
del _train


class PriceInput(BaseModel):
    """One row of input. strict=True: "2024" (a string) is rejected for year, 5 (a number) for commodity, etc."""

    model_config = ConfigDict(
        strict=True,
        json_schema_extra={
            "example": {
                "commodity": "Beans (dry)",
                "category": "pulses and nuts",
                "market": "Munini",
                "admin2": "Kirehe",
                "admin1": "Eastern Province",
                "latitude": -2.31,
                "longitude": 30.82,
                "year": 2025,
                "month": 6,
            }
        },
    )

    commodity: str = Field(min_length=1, max_length=60, description="Commodity name, e.g. 'Maize'")
    category: str = Field(min_length=1, max_length=40, description="Commodity category, e.g. 'cereals and tubers'")
    market: str = Field(min_length=1, max_length=40, description="Market name, e.g. 'Kimironko'")
    admin2: str = Field(min_length=1, max_length=40, description="District, e.g. 'Gasabo'")
    admin1: str = Field(min_length=1, max_length=40, description="Province, e.g. 'Kigali City'")
    latitude: float = Field(ge=-2.9, le=-1.0, description="Market latitude (Rwanda spans about -2.9 to -1.0)")
    longitude: float = Field(ge=28.8, le=31.0, description="Market longitude (Rwanda spans about 28.8 to 31.0)")
    year: int = Field(ge=2000, le=2035, description="Year of the price")
    month: int = Field(ge=1, le=12, description="Month of the price (1-12)")

    @field_validator("commodity", "category", "market", "admin2", "admin1")
    @classmethod
    def must_be_known(cls, value, info):
        if value not in KNOWN_VALUES[info.field_name]:
            raise ValueError(f"unknown {info.field_name} '{value}'. See GET /options for valid values.")
        return value


class PricePrediction(BaseModel):
    predicted_price_rwf_per_kg: float


def predict_price(row: pd.DataFrame) -> float:
    """Same function as in the notebook: predict the price for one row of raw features."""
    return float(model.predict(row[rt.FEATURES])[0])


@app.get("/")
def root():
    return {"message": "Rwanda Food Price API. Open /docs for the Swagger UI."}


@app.get("/options")
def options():
    """Valid values for the text (categorical) inputs."""
    return KNOWN_VALUES


@app.post("/predict", response_model=PricePrediction)
def predict(data: PriceInput):
    row = pd.DataFrame([data.model_dump()])
    return {"predicted_price_rwf_per_kg": round(predict_price(row), 2)}


@app.post("/retrain")
def retrain_endpoint(file: UploadFile = File(..., description="CSV with the training columns + price")):
    """Upload a CSV of new price records; the model is retrained immediately and /predict uses it right away."""
    global model
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")
    try:
        new_model, report, new_rows = rt.retrain(file.file.read(), model)
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as err:
        raise HTTPException(status_code=400, detail=str(err))

    model = new_model
    # new categories (e.g. a new market) in the upload become valid inputs
    for col in rt.CATEGORICAL:
        KNOWN_VALUES[col] = sorted(set(KNOWN_VALUES[col]) | set(new_rows[col].unique()))
    return {"status": "model retrained and now in use", **report}
