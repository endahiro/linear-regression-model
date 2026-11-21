# Rwanda Food Price Predictor

**Mission:** digitalizing Africa's physical sectors, starting with agriculture.
**Problem:** Rwandan farmer cooperatives and agri-traders sell without knowing what a commodity will fetch in each market.
This project predicts the retail price (RWF per KG) of a food commodity in a given Rwandan market and month,
so they can decide where and when to sell.

## Dataset
[WFP Food Prices for Rwanda](https://data.humdata.org/dataset/wfp-food-prices-for-rwanda) - World Food Programme, via the
Humanitarian Data Exchange (HDX), licence CC-BY-IGO. 157,793 monthly price records (2000-2026) from 109 markets
and 65 commodities, with province, district, market coordinates, commodity category, unit and price in RWF.
After keeping retail prices per KG: 137,790 rows, 9 features (5 categorical, 4 numeric).

## API (Swagger UI)
https://rwanda-food-price-api.onrender.com/docs

The free Render service sleeps after 15 minutes of inactivity; the first request can take up to a minute.

## Video demo
YouTube: <!-- TODO: paste YouTube link -->

## Run the mobile app
1. Install [Flutter](https://docs.flutter.dev/get-started/install) and Android Studio, and create an Android emulator
   (Android Studio > Device Manager), or connect an Android phone with USB debugging on.
2. Clone the repository and open the app folder:
   ```bash
   git clone https://github.com/endahiro/linear-regression-model.git
   cd linear-regression-model/summative/FlutterApp
   ```
3. Generate the platform folders (only the first time; existing files such as `lib/main.dart` are kept):
   ```bash
   flutter create --project-name food_price_app --platforms android,ios .
   ```
4. Install dependencies: `flutter pub get`
5. Start the emulator, then run: `flutter run`
6. Fill in the 9 fields (example: Beans (dry), pulses and nuts, Munini, Kirehe, Eastern Province, -2.31, 30.82, 2025, 6)
   and press **Predict**. Valid names for the text fields are listed at
   https://rwanda-food-price-api.onrender.com/options

## Repository layout
```
linear_regression_model/
├── README.md
└── summative/
    ├── pyproject.toml, uv.lock          # notebook environment (uv)
    ├── linear_regression/
    │   ├── multivariate.ipynb           # EDA, 4 models, loss curve, best model
    │   └── wfp_food_prices_rwa.csv
    ├── API/                             # Render root directory
    │   ├── prediction.py                # FastAPI app: /predict, /retrain, /options, /docs
    │   ├── retrain.py                   # retraining logic
    │   ├── best_model.pkl               # saved Pipeline (preprocessing + random forest)
    │   ├── training_data.csv.gz         # cleaned data used when retraining
    │   ├── sample_new_data.csv          # example upload for /retrain
    │   ├── requirements.txt, pyproject.toml, uv.lock
    └── FlutterApp/                      # one-page Flutter app
```

## Run the notebook / API locally
```bash
cd summative && uv sync && uv run jupyter lab           # notebook
cd summative/API && uv sync && uv run uvicorn prediction:app --reload   # API at http://127.0.0.1:8000/docs
```
