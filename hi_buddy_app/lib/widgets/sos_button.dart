import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/database_service.dart';
import '../services/ui_mode_service.dart';

/// ══════════════════════════════════════════════════════════
/// SOS 버튼 (v1.4「메이트」)
/// HaruTokensV2 danger + radiusXl 강화
/// 키오스크/간단 모드에서만 표시 (P5 + UiMode 합의)
/// ══════════════════════════════════════════════════════════
class SosButton extends StatelessWidget {
  const SosButton({super.key});

  static Future<void> _call(BuildContext context) async {
    String phoneNumber = '119';
    try {
      final contacts = await DatabaseService.getEmergencyContacts();
      if (contacts.isNotEmpty) {
        phoneNumber = contacts.first['phone'] as String;
      }
    } catch (_) {
      // DB 오류 시 119 폴백
    }

    final uri = Uri.parse('tel:$phoneNumber');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('$phoneNumber 으로 전화할 수 없어요',
                style: HaruText.body.copyWith(color: HaruTokensV2.onDanger)),
            backgroundColor: HaruTokensV2.danger,
          ),
        );
      }
    }
  }

  static Widget _content() => Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Symbols.call,
              color: HaruTokensV2.onDanger, size: 28, fill: 1),
          const SizedBox(height: 2),
          Text(
            '도움 요청',
            style: HaruText.tiny.copyWith(
              color: HaruTokensV2.onDanger,
              fontWeight: FontWeight.w800,
              fontSize: 11,
            ),
          ),
        ],
      );

  @override
  Widget build(BuildContext context) {
    if (UiModeService.isNormal) return const SizedBox.shrink();

    return Positioned(
      bottom: HaruTokens.space6,
      right: HaruTokens.space6,
      child: SizedBox(
        width: HaruTokens.largeTouchTarget,
        height: HaruTokens.largeTouchTarget,
        child: FloatingActionButton(
          heroTag: 'sos_button',
          onPressed: () => _call(context),
          backgroundColor: HaruTokensV2.danger,
          elevation: 4,
          shape: const CircleBorder(),
          child: _content(),
        ),
      ),
    );
  }

  /// Scaffold의 floatingActionButton 으로 사용.
  static Widget? floatingButton(BuildContext context) {
    if (UiModeService.isNormal) return null;

    return Semantics(
      button: true,
      label: '도움 요청 SOS 버튼. 누르면 가족이나 119에 전화',
      child: Tooltip(
        message: 'SOS · 도움 요청',
        child: SizedBox(
          width: HaruTokens.largeTouchTarget,
          height: HaruTokens.largeTouchTarget,
          child: FloatingActionButton(
            heroTag: 'sos_fab',
            onPressed: () => _call(context),
            backgroundColor: HaruTokensV2.danger,
            elevation: 4,
            shape: const CircleBorder(),
            child: _content(),
          ),
        ),
      ),
    );
  }
}
