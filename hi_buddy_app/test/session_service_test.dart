import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:harumate/services/session_service.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('SessionService', () {
    test('초기엔 온보딩 미완료', () async {
      expect(await SessionService.isOnboarded(), false);
    });

    test('온보딩 완료 후 isOnboarded == true', () async {
      await SessionService.completeOnboarding();
      expect(await SessionService.isOnboarded(), true);
    });

    test('기본 역할은 self', () async {
      expect(await SessionService.getRole(), UserRole.self);
    });

    test('역할 설정 후 재조회 일치', () async {
      await SessionService.setRole(UserRole.coordinator);
      expect(await SessionService.getRole(), UserRole.coordinator);
    });

    test('기본 세그먼트는 dd (발달장애)', () async {
      expect(await SessionService.getSegment(), UserSegment.dd);
    });

    test('페어 코드 6자리 숫자', () {
      final code = SessionService.generatePairCode();
      expect(code.length, 6);
      expect(int.tryParse(code), isNotNull);
    });

    test('이름 빈 값은 "사용자"로 저장', () async {
      await SessionService.setUserName('');
      expect(await SessionService.getUserName(), '사용자');
    });

    test('reset() 후 초기 상태로 돌아감', () async {
      await SessionService.completeOnboarding();
      await SessionService.setRole(UserRole.coordinator);
      await SessionService.reset();
      expect(await SessionService.isOnboarded(), false);
      expect(await SessionService.getRole(), UserRole.self);
    });

    test('FontSizeMode fontScale 값 확인', () {
      expect(SessionService.fontScale(FontSizeMode.normal), 1.0);
      expect(SessionService.fontScale(FontSizeMode.large), greaterThan(1.0));
      expect(SessionService.fontScale(FontSizeMode.xlarge), greaterThan(1.1));
    });
  });
}
