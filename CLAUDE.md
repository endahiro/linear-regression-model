# Math for ML — Summative

ALU summative, 4 deliverables: regression notebook, FastAPI service on Render,
one-page Flutter app, 7-min video demo (Swagger + app within first 2 minutes).

## Use case
Predicting retail food prices (RWF per KG) across Rwandan markets, so
cooperatives and agri-traders can decide where and when to sell. Serves my
mission: digitalizing Africa's physical sectors.

Dataset: WFP Food Prices for Rwanda (HDX), CC-BY-IGO, 157k rows, 2000–2026.
https://data.humdata.org/dataset/wfp-food-prices-for-rwanda
summative/linear_regression/wfp_food_prices_rwa.csv

## Data facts (verified)
- No HXL tag row in this copy; header is row 1, data starts row 2.
- unit is KG / L / Sack / Unit -> keep KG only so the target is comparable.
- pricetype: ~99.5% Retail -> keep Retail only, then the column is constant.
- currency is always RWF (constant). usdprice = price / FX rate -> leakage, drop.
- market_id / commodity_id duplicate market / commodity names -> drop.
- date is a string -> split to year/month.

## Model inputs (API + Flutter must match exactly)
commodity, category, market, admin2 (district), admin1 (province),
latitude, longitude, year, month.  Target: price (RWF/KG).

## Layout is graded literally — do not reorganize
linear-regression-model/
  README.md
  summative/
    pyproject.toml, uv.lock
    linear_regression/multivariate.ipynb
    API/  prediction.py, retrain.py, pyproject.toml, uv.lock,
          requirements.txt, best_model.pkl  (Render root dir)
    FlutterApp/

Repo: https://github.com/endahiro/linear-regression-model
API:  https://rwanda-food-price-api-6r6r.onrender.com/docs

## Conventions
- uv for deps. Two separate envs: summative/ and summative/API/.
- scikit-learn version must be identical in both envs (pickle compatibility).
- Never commit .venv/. Always commit best_model.pkl — Render's free tier
  loses local file writes on restart, so the model loads from the repo.
- API requirements: cd summative/API && uv export --format requirements.txt --no-hashes -o requirements.txt
- Flutter is run from Windows (Android emulator), not WSL.

## How I want you to work
Just do the work end to end; no step-by-step explanations needed. Give a short
summary at the end of each task. Ask only when blocked on a real decision.
