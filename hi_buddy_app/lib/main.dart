import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'models/recipe.dart';
import 'services/api_service.dart';
import 'services/database_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await RecipeData.load();
  await DatabaseService.db; // DB 초기화
  // 서버 미리 깨우기 (Render 콜드 스타트 대응, 응답 안 기다림)
  ApiService.isOnline();
  runApp(const HiBuddyApp());
}

class HiBuddyApp extends StatelessWidget {
  const HiBuddyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '하루메이트',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: const HomeScreen(),
    );
  }
}
