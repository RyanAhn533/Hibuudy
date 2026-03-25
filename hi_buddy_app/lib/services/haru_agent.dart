import 'database_service.dart';
import '../models/recipe.dart';

enum Intent {
  hungry, weather, transit, youtube, timer, call, bored, medicine, schedule, unknown
}

class AgentResponse {
  final String text;
  final List<AgentAction> actions;
  final String? youtubeQuery;

  AgentResponse({required this.text, this.actions = const [], this.youtubeQuery});
}

class AgentAction {
  final String label;
  final String actionType; // 'recipe', 'youtube', 'call', 'navigate'
  final Map<String, dynamic> data;

  AgentAction({required this.label, required this.actionType, this.data = const {}});
}

class HaruAgent {
  /// Process user input and return response
  static Future<AgentResponse> handle(String input) async {
    final intent = classifyIntent(input);
    final profile = await DatabaseService.getProfile();

    switch (intent) {
      case Intent.hungry:
        return await _handleHungry(profile);
      case Intent.medicine:
        return await _handleMedicine();
      case Intent.call:
        return await _handleCall(input);
      case Intent.bored:
        return _handleBored();
      case Intent.youtube:
        return _handleYouTube(input);
      case Intent.timer:
        return _handleTimer(input);
      case Intent.schedule:
        return _handleSchedule();
      case Intent.weather:
        return AgentResponse(text: '날씨 확인 중이에요...', actions: []);
      case Intent.transit:
        return AgentResponse(text: '교통 정보 확인 중이에요...', actions: []);
      case Intent.unknown:
        return AgentResponse(text: '잘 이해하지 못했어요. 다시 말해주세요.');
    }
  }

  static Intent classifyIntent(String input) {
    final t = input.toLowerCase().replaceAll(' ', '');
    if (_matchAny(t, ['배고', '먹', '밥', '요리', '간식', '점심', '저녁', '아침밥', '뭐먹'])) return Intent.hungry;
    if (_matchAny(t, ['날씨', '비와', '우산', '온도', '추워', '더워', '기온'])) return Intent.weather;
    if (_matchAny(t, ['버스', '지하철', '가는법', '교통', '몇분', '출발', '길'])) return Intent.transit;
    if (_matchAny(t, ['유튜브', '영상', '보여줘', '틀어줘', '동영상'])) return Intent.youtube;
    if (_matchAny(t, ['타이머', '분후', '초후', '알려줘', '알람'])) return Intent.timer;
    if (_matchAny(t, ['전화', '엄마', '아빠', '선생님', '도와줘', '119'])) return Intent.call;
    if (_matchAny(t, ['심심', '놀자', '뭐하', '지루', '재미'])) return Intent.bored;
    if (_matchAny(t, ['약', '먹어야', '복용'])) return Intent.medicine;
    if (_matchAny(t, ['일정', '오늘', '스케줄', '할일'])) return Intent.schedule;
    return Intent.unknown;
  }

  static bool _matchAny(String text, List<String> keywords) {
    return keywords.any((kw) => text.contains(kw));
  }

  static Future<AgentResponse> _handleHungry(Map<String, dynamic> profile) async {
    final ingredients = await DatabaseService.getIngredients();
    final ingredientNames = ingredients.map((i) => i['name'] as String).toList();

    // 식재료 기반 레시피 매칭
    final allRecipes = getAllRecipeNames();
    String? matched;
    for (final recipe in allRecipes) {
      final r = getRecipe(recipe);
      if (r != null) {
        final hasIngredient = r.ingredients.any(
          (ing) => ingredientNames.any((n) => ing.contains(n) || n.contains(recipe)),
        );
        if (hasIngredient) {
          matched = recipe;
          break;
        }
      }
    }

    if (matched != null) {
      return AgentResponse(
        text: '집에 있는 재료로 $matched 어때요?',
        actions: [
          AgentAction(label: '레시피 보기', actionType: 'recipe', data: {'name': matched}),
          AgentAction(label: '유튜브로 보기', actionType: 'youtube', data: {'query': '$matched 쉽게 만드는 법'}),
          AgentAction(label: '다른 거 추천', actionType: 'navigate', data: {'screen': 'recipes'}),
        ],
        youtubeQuery: '$matched 쉬운 요리 따라하기',
      );
    }

    if (allRecipes.isNotEmpty) {
      final suggestion = allRecipes.first;
      return AgentResponse(
        text: '$suggestion 어때요?',
        actions: [
          AgentAction(label: '레시피 보기', actionType: 'recipe', data: {'name': suggestion}),
          AgentAction(label: '유튜브로 보기', actionType: 'youtube', data: {'query': '$suggestion 쉽게 만드는 법'}),
        ],
      );
    }

    return AgentResponse(text: '뭐 먹고 싶어요? 알려주세요.');
  }

  static Future<AgentResponse> _handleMedicine() async {
    final meds = await DatabaseService.getMedicineSchedules();
    if (meds.isEmpty) {
      return AgentResponse(text: '등록된 약이 없어요. 설정에서 추가할 수 있어요.');
    }
    final medList = meds.map((m) => '${m['name']} (${m['time']})').join(', ');
    return AgentResponse(text: '오늘 먹을 약: $medList');
  }

  static Future<AgentResponse> _handleCall(String input) async {
    final contacts = await DatabaseService.getEmergencyContacts();
    if (contacts.isEmpty) {
      return AgentResponse(text: '등록된 연락처가 없어요. 설정에서 추가해주세요.');
    }

    // 이름 매칭
    for (final c in contacts) {
      if (input.contains(c['name'] as String)) {
        return AgentResponse(
          text: '${c['name']}에게 전화할까요?',
          actions: [
            AgentAction(label: '전화하기', actionType: 'call', data: {'phone': c['phone'], 'name': c['name']}),
          ],
        );
      }
    }

    // 매칭 안 되면 목록 보여주기
    final names = contacts.map((c) => c['name']).join(', ');
    return AgentResponse(text: '누구에게 전화할까요? $names');
  }

  static AgentResponse _handleBored() {
    return AgentResponse(
      text: '뭐 하고 싶어요?',
      actions: [
        AgentAction(label: '유튜브 보기', actionType: 'youtube', data: {'query': '재미있는 영상'}),
        AgentAction(label: '요리 해보기', actionType: 'navigate', data: {'screen': 'recipes'}),
        AgentAction(label: '운동 하기', actionType: 'navigate', data: {'screen': 'exercise'}),
      ],
    );
  }

  static AgentResponse _handleYouTube(String input) {
    // "유튜브" 키워드 제거하고 나머지를 검색어로
    final query = input.replaceAll(RegExp(r'유튜브|영상|보여줘|틀어줘|동영상'), '').trim();
    final searchQuery = query.isNotEmpty ? query : '재미있는 영상';
    return AgentResponse(
      text: '"$searchQuery" 영상을 찾아볼게요.',
      youtubeQuery: searchQuery,
    );
  }

  static AgentResponse _handleTimer(String input) {
    final match = RegExp(r'(\d+)\s*(분|초)').firstMatch(input);
    if (match != null) {
      final amount = match.group(1)!;
      final unit = match.group(2)!;
      return AgentResponse(text: '$amount$unit 타이머를 설정할게요.');
    }
    return AgentResponse(text: '몇 분 타이머를 설정할까요?');
  }

  static AgentResponse _handleSchedule() {
    return AgentResponse(
      text: '오늘 일정을 보여드릴게요.',
      actions: [
        AgentAction(label: '오늘 하루 보기', actionType: 'navigate', data: {'screen': 'today'}),
      ],
    );
  }
}
