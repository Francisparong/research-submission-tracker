
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_submission_tracker/main.dart';

void main() {
  testWidgets(
    'Research Submission Tracker renders login interface',
    (WidgetTester tester) async {
      await tester.pumpWidget(const TrackerApp());

      // Verify the main application is displayed.
      expect(find.byType(MaterialApp), findsOneWidget);

      // Verify the login button is displayed.
      expect(find.text('Log in'), findsOneWidget);

      // Verify the password input is displayed.
      expect(find.byType(TextField), findsWidgets);
    },
  );
}
