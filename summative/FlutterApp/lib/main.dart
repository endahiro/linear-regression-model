import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// Public Render URL of the API (POST /predict).
const String apiUrl = 'https://rwanda-food-price-api-6r6r.onrender.com/predict';

void main() => runApp(const FoodPriceApp());

class FoodPriceApp extends StatelessWidget {
  const FoodPriceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rwanda Food Price Predictor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.green, useMaterial3: true),
      home: const PredictionPage(),
    );
  }
}

/// One input variable of the model: the JSON key the API expects, its label, a hint and its type.
class InputField {
  final String key;
  final String label;
  final String hint;
  final String type; // 'text', 'int' or 'double'
  final TextEditingController controller = TextEditingController();

  InputField(this.key, this.label, this.hint, this.type);
}

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  // One text field per model input (9 inputs).
  final List<InputField> fields = [
    InputField('commodity', 'Commodity', 'e.g. Beans (dry)', 'text'),
    InputField('category', 'Category', 'e.g. pulses and nuts', 'text'),
    InputField('market', 'Market', 'e.g. Munini', 'text'),
    InputField('admin2', 'District', 'e.g. Kirehe', 'text'),
    InputField('admin1', 'Province', 'e.g. Eastern Province', 'text'),
    InputField('latitude', 'Latitude', '-2.9 to -1.0, e.g. -2.31', 'double'),
    InputField('longitude', 'Longitude', '28.8 to 31.0, e.g. 30.82', 'double'),
    InputField('year', 'Year', '2000 to 2035, e.g. 2025', 'int'),
    InputField('month', 'Month', '1 to 12, e.g. 6', 'int'),
  ];

  String result = 'Fill in all fields and press Predict.';
  bool isError = false;
  bool loading = false;

  @override
  void dispose() {
    for (final f in fields) {
      f.controller.dispose();
    }
    super.dispose();
  }

  void showMessage(String message, {required bool error}) {
    setState(() {
      result = message;
      isError = error;
      loading = false;
    });
  }

  /// Builds the JSON body; returns null (and shows an error) if a value is missing or has the wrong type.
  Map<String, dynamic>? buildBody() {
    final body = <String, dynamic>{};
    for (final f in fields) {
      final text = f.controller.text.trim();
      if (text.isEmpty) {
        showMessage('${f.label} is missing.', error: true);
        return null;
      }
      if (f.type == 'int') {
        final value = int.tryParse(text);
        if (value == null) {
          showMessage('${f.label} must be a whole number.', error: true);
          return null;
        }
        body[f.key] = value;
      } else if (f.type == 'double') {
        final value = double.tryParse(text);
        if (value == null) {
          showMessage('${f.label} must be a number.', error: true);
          return null;
        }
        body[f.key] = value;
      } else {
        body[f.key] = text;
      }
    }
    return body;
  }

  /// Turns FastAPI's 422 validation error list into readable lines, e.g. "Year: Input should be ... 2035".
  String readableErrors(dynamic detail) {
    if (detail is! List) return detail.toString();
    return detail.map((e) {
      final loc = (e['loc'] as List).last.toString();
      final label = fields.firstWhere((f) => f.key == loc, orElse: () => InputField(loc, loc, '', '')).label;
      final msg = e['msg'].toString().replaceFirst('Value error, ', '');
      return '$label: $msg';
    }).join('\n');
  }

  Future<void> predict() async {
    FocusScope.of(context).unfocus();
    final body = buildBody();
    if (body == null) return;

    setState(() => loading = true);
    try {
      final response = await http
          .post(Uri.parse(apiUrl), headers: {'Content-Type': 'application/json'}, body: jsonEncode(body))
          .timeout(const Duration(seconds: 90)); // free Render service can take ~1 min to wake up
      final data = jsonDecode(response.body);
      if (response.statusCode == 200) {
        final price = (data['predicted_price_rwf_per_kg'] as num).toDouble();
        showMessage('Predicted price: ${price.toStringAsFixed(0)} RWF per KG', error: false);
      } else {
        showMessage(readableErrors(data['detail']), error: true);
      }
    } catch (e) {
      showMessage('Could not reach the API. Check your internet connection and try again.', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Rwanda Food Price Predictor'),
        backgroundColor: colors.primaryContainer,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Predict the retail price of a food commodity in a Rwandan market.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            for (final f in fields) ...[
              TextField(
                controller: f.controller,
                keyboardType: f.type == 'text'
                    ? TextInputType.text
                    : const TextInputType.numberWithOptions(decimal: true, signed: true),
                decoration: InputDecoration(
                  labelText: f.label,
                  hintText: f.hint,
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
            ],
            const SizedBox(height: 4),
            SizedBox(
              height: 48,
              child: FilledButton(
                onPressed: loading ? null : predict,
                child: loading
                    ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Predict', style: TextStyle(fontSize: 16)),
              ),
            ),
            const SizedBox(height: 16),
            // Display area: shows the prediction, or a readable error message.
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isError ? colors.errorContainer : colors.secondaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                result,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: isError ? colors.onErrorContainer : colors.onSecondaryContainer,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
