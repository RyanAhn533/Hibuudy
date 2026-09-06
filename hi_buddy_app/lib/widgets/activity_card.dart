import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';

/// ══════════════════════════════════════════════════════════
/// ActivityCard — 시간대 활동 카드 (v1.4「메이트」)
/// HaruTokensV2 적용:
///   - 9 type → 4 그룹 컬러 패밀리 (P1)
///   - 이모지 폐기, Material Symbols 픽토 사용 (P6)
///   - 좌측 컬러 바 강화 (활동 그룹 시각 단서)
/// ══════════════════════════════════════════════════════════
class ActivityCard extends StatelessWidget {
  final String type;
  final String task;
  final String time;
  final VoidCallback? onTap;
  final bool isActive;

  const ActivityCard({
    super.key,
    required this.type,
    required this.task,
    required this.time,
    this.onTap,
    this.isActive = false,
  });

  /// 활동 타입 → Material Symbols 픽토. NowNextCard 등에서 재사용.
  static IconData iconFor(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
        return Symbols.restaurant;
      case 'MEAL':
      case 'SNACK':
        return Symbols.restaurant_menu;
      case 'HEALTH':
      case 'EXERCISE':
        return Symbols.directions_walk;
      case 'WALK':
        return Symbols.directions_walk;
      case 'CLOTHING':
        return Symbols.checkroom;
      case 'LEISURE':
        return Symbols.sentiment_satisfied;
      case 'REST':
      case 'SLEEP':
        return Symbols.bedtime;
      case 'MORNING_BRIEFING':
        return Symbols.wb_sunny;
      case 'NIGHT_WRAPUP':
        return Symbols.dark_mode;
      case 'ROUTINE':
        return Symbols.cleaning_services;
      default:
        return Symbols.event;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = HaruTokensV2.activityMainFor(type);
    final bgColor = HaruTokensV2.activitySoftFor(type);
    final groupLabel = HaruTokensV2.activityGroupLabel(type);
    final icon = iconFor(type);

    return Semantics(
      label: '$time $groupLabel $task',
      button: onTap != null,
      child: Material(
        color: bgColor,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
          child: Container(
            padding: const EdgeInsets.all(HaruTokens.space4),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
              border: Border(
                left: BorderSide(color: color, width: 5),
              ),
            ),
            child: Row(
              children: [
                // ─── 시간 배지 ───
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: HaruTokens.space3,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(HaruTokensV2.radiusSm),
                  ),
                  child: Text(
                    time,
                    style: HaruText.small.copyWith(
                      color: HaruTokensV2.onBrand,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                const SizedBox(width: HaruTokens.space3),
                // ─── 픽토 (이모지 폐기) ───
                Icon(icon, size: 24, color: color, fill: 1),
                const SizedBox(width: HaruTokens.space2),
                // ─── 본문 ───
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: HaruTokens.space2,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          groupLabel,
                          style: HaruText.tiny.copyWith(
                            color: color,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        task,
                        style: HaruText.body.copyWith(
                          color: HaruTokensV2.inkPrimary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                if (onTap != null)
                  Icon(Symbols.chevron_right,
                      color: HaruTokensV2.inkMuted, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
