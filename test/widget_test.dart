import 'package:flutter_test/flutter_test.dart';
import 'package:sign_bridge/main.dart';

void main() {
  testWidgets(
    'SignBridge application starts',
    (WidgetTester tester) async {
      await tester.pumpWidget(
        const SignBridgeApp(),
      );

      expect(
        find.byType(SignBridgeApp),
        findsOneWidget,
      );
    },
  );
}