import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';
import 'models/recipe.dart';
import 'services/api_service.dart';
import 'services/database_service.dart';
import 'services/ui_mode_service.dart';
import 'services/session_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await RecipeData.load();
  await DatabaseService.db; // DB 초기화
  await UiModeService.loadMode(); // UI 모드 로드
  // 서버 미리 깨우기 (Render 콜드 스타트 대응, 응답 안 기다림)
  ApiService.isOnline();

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
