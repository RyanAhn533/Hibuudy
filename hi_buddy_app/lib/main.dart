import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';
import 'models/recipe.dart';
import 'services/api_service.dart';
import 'services/database_service.dart';
import 'services/ui_mode_service.dart';
import 'services/session_service.dart';
import 'services/error_reporter.dart';
import 'services/notification_service.dart';

void main() async {
  // v1.3: 전역 에러 핸들러 먼저 설치 (이후 크래시 자동 캡처)
  ErrorReporter.install();

  WidgetsFlutterBinding.ensureInitialized();
  await RecipeData.load();
  await DatabaseService.db; // DB 초기화
  await UiModeService.loadMode(); // UI 모드 로드
  // 서버 미리 깨우기 (Render 콜드 스타트 대응)
  ApiService.isOnline();
  // 이전 세션 에러 로그 서버로 전송 (백그라운드)
  ErrorReporter.flush();
  // 푸시 알림 초기화 + 오늘 일정 스케줄 (백그라운드)
  NotificationService.init().then((_) => NotificationService.rescheduleAll());

  final onboarded = await SessionService.isOnboarded();
  runApp(HaruMateApp(onboarded: onboarded));
}

class HaruMateApp extends StatelessWidget {
  final bool onboarded;
  const HaruMateApp({super.key, required this.onboarded});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '하루메이트',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: onboarded ? const HomeScreen() : const OnboardingScreen(),
    );
  }
}

// Legacy name alias — 외부 레퍼런스 호환
typedef HiBuddyApp = HaruMateApp;
