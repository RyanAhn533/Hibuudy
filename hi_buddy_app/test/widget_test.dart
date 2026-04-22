// 스캐폴딩 통합 테스트 — v1.3 업데이트
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:harumate/main.dart';

void main() {
  testWidgets('HaruMateApp 스모크 테스트 — 온보딩 초기 상태', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const HaruMateApp(onboarded: false));
    expect(tester.takeException(), isNull);
  });

  testWidgets('HaruMateApp 온보딩 완료 상태에서 홈 진입', (tester) async {
    SharedPreferences.setMockInitialValues({
      'harumate_onboarded_v1': true,
      'harumate_role': 'coordinator',
      'harumate_user_name': '테스트',
    });
    await tester.pumpWidget(const HaruMateApp(onboarded: true));
    expect(tester.takeException(), isNull);
  });
}
