import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'database_service.dart';
import '../models/recipe.dart';
import 'schedule_storage.dart';

/// 하루메이트 에이전트 — 진짜 AI 에이전트.
/// 사용자의 전체 맥락(프로필, 식재료, 일정, 수행기록, 약, 연락처)을
/// Claude에게 넘겨서 개인화된 판단을 받는다.
/// 오프라인 시 키워드 폴백.

class AgentResponse {
  final String text;
  final List<AgentAction> actions;
  final String? youtubeQuery;

  AgentResponse({required this.text, this.actions = const [], this.youtubeQuery});
}

class AgentAction {
  final String label;
  final String actionType; // 'recipe', 'youtube', 'call', 'navigate', 'timer'
  final Map<String, dynamic> data;

  AgentAction({required this.label, required this.actionType, this.data = const {}});
}

class HaruAgent {
  // Claude API (Anthropic)
  static const String _apiKey = String.fromEnvironment(
    'CLAUDE_API_KEY',
    defaultValue: '',
  );

  /// 메인 처리: Claude에 맥락 넘겨서 응답 받기. 실패 시 오프라인 폴백.
  static Future<AgentResponse> handle(String input) async {
    // Claude API 키가 있으면 진짜 에이전트 모드
    if (_apiKey.isNotEmpty) {
      try {
        return await _handleWithClaude(input);
      } catch (_) {
        // API 실패 시 오프라인 폴백
      }
    }

    // 오프라인 폴백 (키워드 매칭)
    return _handleOffline(input);
  }

  /// Claude API로 맥락 기반 응답 생성
  static Future<AgentResponse> _handleWithClaude(String input) async {
    final context = await _buildContext();

    final response = await http.post(
      Uri.parse('https://api.anthropic.com/v1/messages'),
      headers: {
        'x-api-key': _apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: jsonEncode({
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 500,
        'system': _buildSystemPrompt(context),
        'messages': [
          {'role': 'user', 'content': input},
        ],
      }),
    ).timeout(const Duration(seconds: 15));

    if (response.statusCode != 200) {
      throw Exception('Claude API error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);
    final text = data['content'][0]['text'] as String;

    return _parseClaudeResponse(text, input);
  }

  /// 사용자 맥락 조립 — Claude에게 넘길 전체 상황
  static Future<Map<String, dynamic>> _buildContext() async {
    final profile = await DatabaseService.getProfile();
    final ingredients = await DatabaseService.getIngredients();
    final medicines = await DatabaseService.getMedicineSchedules();
    final contacts = await DatabaseService.getEmergencyContacts();
    final recentLogs = await DatabaseService.getCompletionLogs(limit: 10);

    // 오늘 일정
    final schedule = await ScheduleStorage.load();
    final todayItems = schedule?.items.map((i) => {
      'time': i.time,
      'type': i.type,
      'task': i.task,
    }).toList() ?? [];

    // 현재 시간
    final now = DateTime.now();
    final hour = now.hour;
    String timeOfDay;
    if (hour < 12) {
      timeOfDay = '오전';
    } else if (hour < 18) {
      timeOfDay = '오후';
    } else {
      timeOfDay = '저녁';
    }

    return {
      'user_name': profile['name'] ?? '사용자',
      'disability_level': profile['disability_level'] ?? 'mild',
      'current_time': DateFormat('HH:mm').format(now),
      'time_of_day': timeOfDay,
      'day_of_week': ['월', '화', '수', '목', '금', '토', '일'][now.weekday - 1],
      'ingredients': ingredients.map((i) => i['name']).toList(),
      'medicines': medicines.map((m) => '${m['name']} ${m['time']}').toList(),
      'contacts': contacts.map((c) => '${c['name']} (${c['relationship']})').toList(),
      'today_schedule': todayItems,
      'recent_completions': recentLogs.take(5).map((l) =>
        '${l['date']} ${l['task']} ${l['completed'] == 1 ? "완료" : "미완료"}'
      ).toList(),
      'available_recipes': getAllRecipeNames(),
    };
  }

  /// Claude 시스템 프롬프트 — 에이전트 역할 정의
  static String _buildSystemPrompt(Map<String, dynamic> ctx) {
    return '''너는 "하루메이트"라는 발달장애인/노인 생활 도우미 AI야.
사용자의 하루를 도와주는 게 네 역할이야.

## 사용자 정보
- 이름: ${ctx['user_name']}
- 장애 수준: ${ctx['disability_level']}
- 현재 시각: ${ctx['current_time']} (${ctx['time_of_day']})
- 오늘: ${ctx['day_of_week']}요일

## 냉장고 식재료
${(ctx['ingredients'] as List).isEmpty ? '등록된 식재료 없음' : (ctx['ingredients'] as List).join(', ')}

## 만들 수 있는 레시피
${(ctx['available_recipes'] as List).join(', ')}

## 오늘 일정
${(ctx['today_schedule'] as List).isEmpty ? '오늘 일정 없음' : (ctx['today_schedule'] as List).map((i) => '${i['time']} ${i['task']}').join('\n')}

## 약 복용
${(ctx['medicines'] as List).isEmpty ? '등록된 약 없음' : (ctx['medicines'] as List).join(', ')}

## 긴급 연락처
${(ctx['contacts'] as List).isEmpty ? '없음' : (ctx['contacts'] as List).join(', ')}

## 최근 활동
${(ctx['recent_completions'] as List).isEmpty ? '기록 없음' : (ctx['recent_completions'] as List).join('\n')}

## 대화 규칙
1. 존댓말 사용 (해요체)
2. 문장은 짧게 (20~40자)
3. 한 번에 하나만 안내
4. 장애 수준에 맞게:
   - mild: 일반 대화
   - moderate: 더 쉬운 단어, 더 짧은 문장
   - severe: 핵심 단어만, 5단어 이내
5. 식사 추천 시 냉장고 식재료 확인 후 추천
6. 어제 먹은 것과 다른 걸 추천
7. 유튜브 영상이 도움될 것 같으면 [유튜브: 검색어] 형식으로 추천
8. 전화가 필요하면 [전화: 이름] 형식으로 안내
9. 감정적 지원이 필요하면 공감하고 격려해줘
10. 절대 의학적 조언 하지 마. 약은 등록된 것만 알려줘.''';
  }

  /// Claude 응답 파싱 — [유튜브: ...], [전화: ...] 등 액션 추출
  static AgentResponse _parseClaudeResponse(String text, String input) {
    final actions = <AgentAction>[];
    String? youtubeQuery;

    // [유튜브: 검색어] 추출
    final ytMatch = RegExp(r'\[유튜브:\s*(.+?)\]').firstMatch(text);
    if (ytMatch != null) {
      youtubeQuery = ytMatch.group(1)!.trim();
      actions.add(AgentAction(
        label: '유튜브 보기',
        actionType: 'youtube',
        data: {'query': youtubeQuery},
      ));
      text = text.replaceAll(ytMatch.group(0)!, '').trim();
    }

    // [전화: 이름] 추출
    final callMatch = RegExp(r'\[전화:\s*(.+?)\]').firstMatch(text);
    if (callMatch != null) {
      final name = callMatch.group(1)!.trim();
      actions.add(AgentAction(
        label: '$name에게 전화',
        actionType: 'call',
        data: {'name': name},
      ));
      text = text.replaceAll(callMatch.group(0)!, '').trim();
    }

    // [레시피: 이름] 추출
    final recipeMatch = RegExp(r'\[레시피:\s*(.+?)\]').firstMatch(text);
    if (recipeMatch != null) {
      final name = recipeMatch.group(1)!.trim();
      actions.add(AgentAction(
        label: '$name 레시피 보기',
        actionType: 'recipe',
        data: {'name': name},
      ));
      text = text.replaceAll(recipeMatch.group(0)!, '').trim();
    }

    return AgentResponse(
      text: text,
      actions: actions,
      youtubeQuery: youtubeQuery,
    );
  }

  // ══════════════════════════════════════════════
  // 오프라인 폴백 (Claude 못 쓸 때)
  // ══════════════════════════════════════════════

  static Future<AgentResponse> _handleOffline(String input) async {
    final t = input.toLowerCase().replaceAll(' ', '');

    if (_matchAny(t, ['배고', '먹', '밥', '요리', '간식', '점심', '저녁', '뭐먹'])) {
      return await _offlineHungry();
    }
    if (_matchAny(t, ['유튜브', '영상', '보여줘', '틀어줘'])) {
      return _offlineYouTube(input);
    }
    if (_matchAny(t, ['전화', '엄마', '아빠', '선생님', '119'])) {
      return await _offlineCall(input);
    }
    if (_matchAny(t, ['약', '복용', '먹어야'])) {
      return await _offlineMedicine();
    }
    if (_matchAny(t, ['심심', '놀', '뭐하', '지루'])) {
      return _offlineBored();
    }
    if (_matchAny(t, ['날씨', '비', '우산', '추워', '더워'])) {
      return AgentResponse(text: '날씨 정보는 인터넷이 필요해요.');
    }

    return AgentResponse(text: '잘 이해하지 못했어요. 다시 말해주세요.');
  }

  static Future<AgentResponse> _offlineHungry() async {
    final ingredients = await DatabaseService.getIngredients();
    final names = ingredients.map((i) => i['name'] as String).toList();
    final recipes = getAllRecipeNames();

    // 식재료 매칭
    for (final recipe in recipes) {
      if (names.any((n) => recipe.contains(n) || n.contains(recipe))) {
        return AgentResponse(
          text: '집에 재료가 있으니까 $recipe 어때요?',
          actions: [
            AgentAction(label: '레시피 보기', actionType: 'recipe', data: {'name': recipe}),
            AgentAction(label: '유튜브로 보기', actionType: 'youtube', data: {'query': '$recipe 쉬운 요리'}),
          ],
          youtubeQuery: '$recipe 쉬운 요리 따라하기',
        );
      }
    }

    if (recipes.isNotEmpty) {
      return AgentResponse(
        text: '${recipes.first} 어때요?',
        actions: [
          AgentAction(label: '레시피 보기', actionType: 'recipe', data: {'name': recipes.first}),
          AgentAction(label: '유튜브로 보기', actionType: 'youtube', data: {'query': '${recipes.first} 쉬운 요리'}),
        ],
      );
    }

    return AgentResponse(text: '뭐 먹고 싶어요?');
  }

  static AgentResponse _offlineYouTube(String input) {
    final query = input.replaceAll(RegExp(r'유튜브|영상|보여줘|틀어줘|동영상'), '').trim();
    final q = query.isNotEmpty ? query : '재미있는 영상';
    return AgentResponse(
      text: '"$q" 영상을 찾아볼게요.',
      youtubeQuery: q,
    );
  }

  static Future<AgentResponse> _offlineCall(String input) async {
    final contacts = await DatabaseService.getEmergencyContacts();
    if (contacts.isEmpty) {
      return AgentResponse(text: '등록된 연락처가 없어요. "나의 정보"에서 추가해주세요.');
    }
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
    final names = contacts.map((c) => c['name']).join(', ');
    return AgentResponse(text: '누구에게 전화할까요? $names');
  }

  static Future<AgentResponse> _offlineMedicine() async {
    final meds = await DatabaseService.getMedicineSchedules();
    if (meds.isEmpty) {
      return AgentResponse(text: '등록된 약이 없어요.');
    }
    final list = meds.map((m) => '${m['name']} (${m['time']})').join(', ');
    return AgentResponse(text: '오늘 먹을 약: $list');
  }

  static AgentResponse _offlineBored() {
    return AgentResponse(
      text: '뭐 하고 싶어요?',
      actions: [
        AgentAction(label: '유튜브 보기', actionType: 'youtube', data: {'query': '재미있는 영상'}),
        AgentAction(label: '요리 해보기', actionType: 'navigate', data: {'screen': 'recipes'}),
        AgentAction(label: '운동 하기', actionType: 'navigate', data: {'screen': 'exercise'}),
      ],
    );
  }

  static bool _matchAny(String text, List<String> keywords) {
    return keywords.any((kw) => text.contains(kw));
  }
}
