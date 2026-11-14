
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:research_submission_tracker/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'Week 15 - Login interface integration smoke test',
    (WidgetTester tester) async {
      await tester.pumpWidget(const TrackerApp());

      expect(find.byType(MaterialApp), findsOneWidget);
      expect(find.text('Log in'), findsOneWidget);
      expect(find.byType(TextField), findsWidgets);
    },
  );

  testWidgets(
    'Week 15 - Empty password login rejection',
    (WidgetTester tester) async {
      await tester.pumpWidget(const TrackerApp());

      await tester.tap(find.text('Log in'));
      await tester.pump();

      expect(find.text('Log in'), findsOneWidget);
    },
  );
}
