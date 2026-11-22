# Rwanda Food Price Predictor (Flutter app)

One-page app that sends the 9 model inputs (commodity, category, market, district, province,
latitude, longitude, year, month) to the
[Rwanda Food Price API](https://rwanda-food-price-api-6r6r.onrender.com/docs) and shows the predicted
retail price in RWF per KG, or an error message if a value is missing or out of range.

```bash
flutter pub get
flutter run        # with an Android emulator running or a phone connected
flutter test       # widget test
```

See the [main README](../../README.md) for full setup steps and an example input.
