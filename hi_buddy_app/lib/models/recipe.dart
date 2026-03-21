import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;

class Recipe {
  final String name;
  final List<String> tools;
  final List<String> ingredients;
  final List<String> steps;

  const Recipe({
    required this.name,
    required this.tools,
    required this.ingredients,
    required this.steps,
  });

  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      name: json['name'] ?? '',
      tools: List<String>.from(json['tools'] ?? []),
      ingredients: List<String>.from(json['ingredients'] ?? []),
      steps: List<String>.from(json['steps'] ?? []),
    );
  }
}

class HealthRoutine {
  final String id;
  final String title;
  final List<String> steps;

  const HealthRoutine({
    required this.id,
    required this.title,
    required this.steps,
  });

  factory HealthRoutine.fromJson(Map<String, dynamic> json) {
    return HealthRoutine(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      steps: List<String>.from(json['steps'] ?? []),
    );
  }
}

/// JSON 에셋에서 레시피/루틴을 로드하는 서비스.
/// 앱 업데이트 없이 백엔드에서 JSON만 교체하면 콘텐츠 추가 가능.
class RecipeData {
  static Map<String, Recipe>? _recipes;
  static Map<String, HealthRoutine>? _routines;
  static bool _loaded = false;

  /// 에셋에서 데이터 로드 (최초 1회)
  static Future<void> load() async {
    if (_loaded) return;
    try {
      final jsonStr =
          await rootBundle.loadString('assets/data/recipes.json');
      final data = jsonDecode(jsonStr) as Map<String, dynamic>;

      final recipesMap = data['recipes'] as Map<String, dynamic>? ?? {};
      _recipes = recipesMap.map(
        (k, v) => MapEntry(k, Recipe.fromJson(v as Map<String, dynamic>)),
      );

      final routinesMap =
          data['health_routines'] as Map<String, dynamic>? ?? {};
      _routines = routinesMap.map(
        (k, v) =>
            MapEntry(k, HealthRoutine.fromJson(v as Map<String, dynamic>)),
      );

      _loaded = true;
    } catch (_) {
      // 에셋 로드 실패 시 하드코딩 폴백
      _recipes = _fallbackRecipes;
      _routines = _fallbackRoutines;
      _loaded = true;
    }
  }

  /// 강제 리로드 (향후 서버에서 다운로드 후 사용)
  static void invalidate() {
    _loaded = false;
    _recipes = null;
    _routines = null;
  }

  static Recipe? getRecipe(String name) => _recipes?[name];
  static HealthRoutine? getHealthRoutine(String id) => _routines?[id];
  static List<String> getAllRecipeNames() =>
      _recipes?.keys.toList() ?? [];

  // ── 에셋 로드 실패 시 폴백 ──
  static final Map<String, Recipe> _fallbackRecipes = {
    '라면': const Recipe(
      name: '라면',
      tools: ['라면냄비', '가스레인지'],
      ingredients: ['라면 1봉지', '물 550ml', '달걀 1개(선택)'],
      steps: [
        '냄비에 물 550ml를 넣어요.',
        '물이 보글보글 끓으면 면과 스프를 넣어요.',
        '4분 동안 기다려요.',
        '달걀을 넣고 싶으면 넣어요.',
        '불을 꺼요. 조심해서 그릇에 옮겨요.',
      ],
    ),
  };

  static final Map<String, HealthRoutine> _fallbackRoutines = {
    'seated': const HealthRoutine(
      id: 'seated',
      title: '앉아서 하는 운동',
      steps: [
        '의자에 편하게 앉아요.',
        '어깨를 천천히 돌려요. 앞으로 5번, 뒤로 5번.',
        '두 팔을 위로 쭉 뻗어요. 5초 동안 유지해요.',
        '수고했어요! 운동 끝!',
      ],
    ),
    'standing': const HealthRoutine(
      id: 'standing',
      title: '서서 하는 운동',
      steps: [
        '편한 곳에 서요.',
        '두 팔을 올렸다 내려요. 10번.',
        '제자리에서 걸어요. 30초.',
        '깊게 숨쉬기 3번. 수고했어요!',
      ],
    ),
  };
}

// ── 기존 코드 호환용 글로벌 함수 ──
Recipe? getRecipe(String name) => RecipeData.getRecipe(name);
HealthRoutine? getHealthRoutine(String id) => RecipeData.getHealthRoutine(id);
List<String> getAllRecipeNames() => RecipeData.getAllRecipeNames();
