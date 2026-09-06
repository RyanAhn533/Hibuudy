// Tier 1 라우터: Gemini Nano (Android AICore) 온디바이스 추론.
// Pixel 8/9/10 + Tensor G3+ 또는 AICore 지원 단말에서만 동작.
// 미지원 단말은 즉시 false 반환 → 백엔드 폴백.
//
// v3.0의 추론 계층:
//   Tier 0  로컬 패턴      (현재 schedule_generator의 정규식)
//   Tier 1  Gemini Nano    ← 이 파일
//   Tier 2  백엔드 Claude/Gemini (현재 haru_agent)

import 'dart:async';
import 'package:flutter/services.dart';

class OnDeviceLLM {
  static const _channel = MethodChannel('com.harumate.care/ondevice_llm');

  static bool? _availableCache;

  /// Gemini Nano (AICore) 사용 가능 여부. 첫 호출 시 캐시.
  static Future<bool> isAvailable() async {
    if (_availableCache != null) return _availableCache!;
    try {
      final ok = await _channel.invokeMethod<bool>('isAvailable');
      _availableCache = ok ?? false;
    } catch (_) {
      _availableCache = false;
    }
    return _availableCache!;
  }

  /// 짧은 추론 (예: 일정 파싱, 단순 Q&A). 1초 이내 응답 기대.
  /// 실패 시 null → 호출자가 Tier 2로 폴백해야 함.
  static Future<String?> infer({
    required String prompt,
    String? systemPrompt,
    int maxTokens = 256,
    Duration timeout = const Duration(seconds: 3),
  }) async {
    if (!await isAvailable()) return null;
    try {
      final result = await _channel.invokeMethod<String>('infer', {
        'prompt': prompt,
        'systemPrompt': systemPrompt ?? _defaultSystem,
        'maxTokens': maxTokens,
      }).timeout(timeout);
      return result;
    } on TimeoutException {
      return null;
    } catch (_) {
      return null;
    }
  }

  /// 의도 분류 — Tier 1 라우팅에 사용.
  /// 반환: 'schedule' | 'meal' | 'health' | 'social' | 'unknown'
  static Future<String> classifyIntent(String userInput) async {
    final result = await infer(
      systemPrompt:
          '너는 발달장애인 도우미 앱의 의도 분류기다. '
          '사용자 입력을 다음 중 하나로 분류해서 그 단어 하나만 답해라: '
          'schedule, meal, health, social, unknown',
      prompt: userInput,
      maxTokens: 16,
    );
    if (result == null) return 'unknown';
    final clean = result.toLowerCase().trim();
    for (final cat in ['schedule', 'meal', 'health', 'social']) {
      if (clean.contains(cat)) return cat;
    }
    return 'unknown';
  }

  static const _defaultSystem =
      '너는 발달장애인을 돕는 따뜻한 도우미야. '
      '쉽고 짧은 한국어로 답해. 어려운 단어 쓰지 마.';
}
