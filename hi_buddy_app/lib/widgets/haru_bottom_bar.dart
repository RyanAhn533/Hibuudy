import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/ui_mode_service.dart';

/// ══════════════════════════════════════════════════════════
/// HaruBottomBar — 당사자 모드 하단 고정 내비 (R3)
/// Apple Assistive Access 패턴: 뒤로/홈은 항상 화면 아래 같은 자리.
/// 상단 앱바 뒤로가기는 코디네이터용, 당사자는 이 바로만 이동.
/// - 아이콘 + 라벨 항상 쌍 (R2)
/// - 88pt largeTouchTarget
/// - 키오스크(잠금) 모드에서는 표시 X
/// ══════════════════════════════════════════════════════════
class HaruBottomBar extends StatelessWidget {
  final bool showBack;
  final bool showHome;

  const HaruBottomBar({
    super.key,
    this.showBack = true,
    this.showHome = true,
  });

  /// 당사자(self) 역할 또는 simple 모드일 때만 바를 돌려준다.
  /// 코디네이터 normal 모드 / 키오스크 모드는 null.
  static Widget? maybe(BuildContext context, {bool showHome = true}) {
    if (UiModeService.isKiosk) return null;
    final isUser = SessionService.currentRole == UserRole.self ||
        UiModeService.isAccessibilityMode;
    if (!isUser) return null;
    return HaruBottomBar(showHome: showHome);
  }

  @override
  Widget build(BuildContext context) {
    final canPop = Navigator.of(context).canPop();
    return Container(
      decoration: const BoxDecoration(
        color: HaruTokensV2.surfaceCard,
        border: Border(top: BorderSide(color: HaruTokensV2.borderSoft)),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: HaruTokens.space3,
            vertical: HaruTokens.space2,
          ),
          child: Row(
            children: [
              if (showBack && canPop)
                Expanded(
                  child: _BarButton(
                    icon: Symbols.arrow_back,
                    label: '뒤로',
                    onTap: () => Navigator.of(context).maybePop(),
                  ),
                ),
              if (showBack && canPop && showHome)
                const SizedBox(width: HaruTokens.space3),
              if (showHome)
                Expanded(
                  child: _BarButton(
                    icon: Symbols.home,
                    label: '홈',
                    filled: true,
                    onTap: () =>
                        Navigator.of(context).popUntil((r) => r.isFirst),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BarButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool filled;
  final VoidCallback onTap;

  const _BarButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.filled = false,
  });

  @override
  Widget build(BuildContext context) {
    final fg = filled ? HaruTokensV2.onBrand : HaruTokensV2.inkPrimary;
    return Semantics(
      button: true,
      label: label,
      child: Material(
        color: filled ? HaruTokensV2.brandWarm : HaruTokensV2.surfaceSunken,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
        child: InkWell(
          borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
          onTap: onTap,
          child: SizedBox(
            height: HaruTokensV2.comfortTouchTarget + 8,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 28, color: fg, fill: filled ? 1 : 0),
                const SizedBox(width: HaruTokens.space2),
                Text(
                  label,
                  style: HaruText.h3.copyWith(
                    color: fg,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
