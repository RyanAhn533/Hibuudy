import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// ══════════════════════════════════════════════════════════
/// ChatMemory — 5분 세션 기반 대화 메모리
/// 비용 최소화: 최근 3턴 + 5분 지나면 자동 리셋
/// 저장: SharedPreferences (메모리 휘발성 + 영속성 하이브리드)
/// ══════════════════════════════════════════════════════════
class ChatMemory {
  static const _kMessagesKey = 'harumate_chat_messages';
  static const _kLastTsKey = 'harumate_chat_last_ts';
  static const _sessionMinutes = 5;
  static const _maxTurns = 3;

  /// 메시지 1쌍 (user + assistant)
  static Future<void> addTurn(String userMsg, String assistantMsg) async {
    final prefs = await SharedPreferences.getInstance();
    final now = DateTime.now();
    final lastTs = prefs.getInt(_kLastTsKey) ?? 0;

    // 5분 경과 시 세션 리셋
    List<Map<String, String>> history = [];
    if (now.millisecondsSinceEpoch - lastTs < _sessionMinutes * 60 * 1000) {
      history = _load(prefs);
    }

    history.add({'role': 'user', 'content': userMsg});
    history.add({'role': 'assistant', 'content': assistantMsg});

    // 최근 N턴만 유지 (user + assistant = 1턴 = 2엔트리)
    if (history.length > _maxTurns * 2) {
      history = history.sublist(history.length - _maxTurns * 2);
    }

    await prefs.setString(_kMessagesKey, jsonEncode(history));
    await prefs.setInt(_kLastTsKey, now.millisecondsSinceEpoch);
  }

  /// 현재 세션의 대화 기록 반환 (5분 넘으면 빈 리스트)
  static Future<List<Map<String, String>>> getActive() async {
    final prefs = await SharedPreferences.getInstance();
    final lastTs = prefs.getInt(_kLastTsKey) ?? 0;
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - lastTs >= _sessionMinutes * 60 * 1000) {
      return [];
    }
    return _load(prefs);
  }

  /// 1줄 요약용 (토큰 절약)
  static Future<String> getSummary() async {
    final history = await getActive();
    if (history.isEmpty) return '';
    final topics = history
        .where((m) => m['role'] == 'user')
        .map((m) => (m['content'] ?? '').split(' ').take(3).join(' '))
        .toList();
    return topics.isEmpty ? '' : '최근 대화: ${topics.join(', ')}';
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kMessagesKey);
    await prefs.remove(_kLastTsKey);
  }

  static List<Map<String, String>> _load(SharedPreferences prefs) {
    final raw = prefs.getString(_kMessagesKey);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List;
      return list
          .map((e) => Map<String, String>.from(e as Map))
          .toList();
    } catch (_) {
      return [];
    }
  }
}
