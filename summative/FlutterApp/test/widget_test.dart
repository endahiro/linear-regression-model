import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:food_price_app/main.dart';

void main() {
  testWidgets('Prediction page shows the inputs, a Predict button and a result area', (tester) async {
    await tester.pumpWidget(const FoodPriceApp());
    expect(find.text('Commodity'), findsOneWidget);

    // the form is longer than the test screen: scroll down to the result area
    await tester.scrollUntilVisible(find.text('Fill in all fields and press Predict.'), 200, scrollable: find.byType(Scrollable).first);
    expect(find.text('Month'), findsOneWidget);
    expect(find.text('Predict'), findsOneWidget);
    expect(find.text('Fill in all fields and press Predict.'), findsOneWidget);
  });
}
