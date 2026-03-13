import 'package:flutter_test/flutter_test.dart';
import 'package:hi_buddy_app/main.dart';

void main() {
  testWidgets('App launches without error', (WidgetTester tester) async {
    await tester.pumpWidget(const HiBuddyApp());
    expect(find.text('Hi-Buddy'), findsOneWidget);
  });
}
