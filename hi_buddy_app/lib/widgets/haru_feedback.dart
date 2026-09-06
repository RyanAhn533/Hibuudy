import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/ui_mode_service.dart';

/// ══════════════════════════════════════════════════════════
/// HaruFeedback — 시간 제한 없는 피드백 (R5)
/// 당사자 모드에서는 스낵바가 스스로 사라지지 않는다.
/// 「확인」을 눌러야 닫힘 (Assistive Access: 시간 의존 UI 금지).
/// 코디네이터 normal 모드는 기존 4초 유지.
/// ══════════════════════════════════════════════════════════
class HaruFeedback {
  HaruFeedback._();

  static void show(
    BuildContext context,
    String message, {
    bool error = false,
  }) {
    final persistent = SessionService.currentRole == UserRole.self ||
        UiModeService.isAccessibilityMode;
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Text(
          message,
          style: HaruText.body.copyWith(
            color: HaruTokensV2.onBrand,
            fontWeight: FontWeight.w600,
          ),
        ),
        backgroundColor:
            error ? HaruTokensV2.danger : HaruTokensV2.inkPrimary,
        duration: persistent
            ? const Duration(days: 1)
            : const Duration(seconds: 4),
        action: SnackBarAction(
          label: '확인',
          textColor: HaruTokensV2.onBrand,
          onPressed: messenger.hideCurrentSnackBar,
        ),
      ),
    );
  }
}
