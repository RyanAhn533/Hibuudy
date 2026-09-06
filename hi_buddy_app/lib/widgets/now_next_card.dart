import 'dart:async';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../models/schedule_item.dart';
import '../theme/app_theme.dart';
import 'activity_card.dart';

/// ══════════════════════════════════════════════════════════
/// NowNextCard — 「지금 | 다음」 2칸 (P1) + 남은 시간 원형 표시 (P2)
/// First-Then 보드 패턴. 다음 칸은 60% 불투명으로 위계.
/// 시간은 색이 바뀌지 않고 천천히 줄어들기만 한다 (N2: 압박 X).
/// ══════════════════════════════════════════════════════════
class NowNextCard extends StatefulWidget {
  final ScheduleItem? current;
  final ScheduleItem? next;
  final VoidCallback? onTap;

  const NowNextCard({
    super.key,
    required this.current,
    required this.next,
    this.onTap,
  });

  @override
  State<NowNextCard> createState() => _NowNextCardState();
}

class _NowNextCardState extends State<NowNextCard> {
  Timer? _tick;

  @override
  void initState() {
    super.initState();
    // 1분 단위로만 갱신. 초 단위 카운트는 불안을 키운다.
    _tick = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _tick?.cancel();
    super.dispose();
  }

  /// (남은 분, 전체 분). 다음 일정이 없으면 null.
  (int, int)? _remaining() {
    final cur = widget.current;
    final nxt = widget.next;
    if (cur == null || nxt == null) return null;
    final now = DateTime.now();
    final nowMin = now.hour * 60 + now.minute;
    final total = nxt.timeMinutes - cur.timeMinutes;
    if (total <= 0) return null;
    final remaining = (nxt.timeMinutes - nowMin).clamp(0, total);
    return (remaining, total);
  }

  @override
  Widget build(BuildContext context) {
    final cur = widget.current;
    final nxt = widget.next;
    final rem = _remaining();

    return Semantics(
      button: widget.onTap != null,
      label: cur != null
          ? '지금 ${cur.task}. ${nxt != null ? "다음 ${nxt.time} ${nxt.task}" : ""}'
          : (nxt != null ? '곧 ${nxt.time} ${nxt.task}' : '오늘은 자유시간'),
      child: GestureDetector(
        onTap: widget.onTap,
        // Column 안(높이 무한)에서 stretch 하려면 IntrinsicHeight 필요
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 3,
                child: _NowPane(item: cur, upcoming: nxt, remaining: rem),
              ),
              // 아직 시작한 일정이 없으면 「다음」 칸은 숨긴다 (곧 시작 칸이 곧 다음).
              if (cur != null) ...[
                const SizedBox(width: HaruTokens.space3),
                Expanded(
                  flex: 2,
                  child: Opacity(
                    opacity: 0.6,
                    child: _NextPane(item: nxt),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _NowPane extends StatelessWidget {
  final ScheduleItem? item;
  final ScheduleItem? upcoming;
  final (int, int)? remaining;

  const _NowPane({
    required this.item,
    required this.upcoming,
    required this.remaining,
  });

  @override
  Widget build(BuildContext context) {
    // 진행 중 일정이 없을 때: 곧 시작 / 자유시간
    final it = item;
    final type = it?.type ?? upcoming?.type ?? 'REST';
    final main = HaruTokensV2.activityMainFor(type);
    final soft = HaruTokensV2.activitySoftFor(type);
    final badge = it != null ? '지금' : (upcoming != null ? '곧 시작' : '자유시간');
    final title = it?.task ?? upcoming?.task ?? '오늘은 자유시간';
    final sub = it != null
        ? '${it.time}부터'
        : (upcoming != null ? '${upcoming!.time} 시작' : null);

    return Container(
      padding: const EdgeInsets.all(HaruTokens.space4),
      decoration: BoxDecoration(
        color: soft,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        border: Border.all(color: main, width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Symbols.schedule, size: 18, color: main),
              const SizedBox(width: HaruTokens.space1),
              Text(
                badge,
                style: HaruText.small.copyWith(
                  color: main,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: HaruTokens.space3),
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Icon(ActivityCard.iconFor(type), size: 40, color: main, fill: 1),
              const SizedBox(width: HaruTokens.space3),
              if (remaining != null)
                _MinuteRing(
                  remaining: remaining!.$1,
                  total: remaining!.$2,
                  color: main,
                ),
            ],
          ),
          const SizedBox(height: HaruTokens.space3),
          Text(
            title,
            style: HaruText.h2.copyWith(color: HaruTokensV2.inkPrimary),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (sub != null) ...[
            const SizedBox(height: 2),
            Text(sub, style: HaruText.small.copyWith(color: HaruTokensV2.inkBody)),
          ],
        ],
      ),
    );
  }
}

class _NextPane extends StatelessWidget {
  final ScheduleItem? item;
  const _NextPane({required this.item});

  @override
  Widget build(BuildContext context) {
    final it = item;
    final type = it?.type ?? 'GENERAL';
    final main = HaruTokensV2.activityMainFor(type);

    return Container(
      padding: const EdgeInsets.all(HaruTokens.space4),
      decoration: BoxDecoration(
        color: HaruTokensV2.surfaceCard,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        border: Border.all(color: HaruTokensV2.borderSoft, width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Symbols.arrow_forward, size: 18, color: HaruTokensV2.inkMuted),
              const SizedBox(width: HaruTokens.space1),
              Text(
                '다음',
                style: HaruText.small.copyWith(
                  color: HaruTokensV2.inkMuted,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: HaruTokens.space3),
          Icon(
            it != null ? ActivityCard.iconFor(type) : Symbols.bedtime,
            size: 32,
            color: it != null ? main : HaruTokensV2.inkMuted,
            fill: 1,
          ),
          const SizedBox(height: HaruTokens.space3),
          Text(
            it?.task ?? '오늘 일정 끝',
            style: HaruText.h3.copyWith(color: HaruTokensV2.inkPrimary),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (it != null) ...[
            const SizedBox(height: 2),
            Text(it.time, style: HaruText.small.copyWith(color: HaruTokensV2.inkBody)),
          ],
        ],
      ),
    );
  }
}

/// 남은 시간 링. 색 고정, 1분 단위, 숫자는 보조.
class _MinuteRing extends StatelessWidget {
  final int remaining;
  final int total;
  final Color color;

  const _MinuteRing({
    required this.remaining,
    required this.total,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final ratio = total == 0 ? 0.0 : remaining / total;
    return Semantics(
      label: '$remaining분 남음',
      child: SizedBox(
        width: 56,
        height: 56,
        child: Stack(
          alignment: Alignment.center,
          children: [
            CircularProgressIndicator(
              value: ratio,
              strokeWidth: 6,
              backgroundColor: HaruTokensV2.borderSoft,
              valueColor: AlwaysStoppedAnimation(color),
              strokeCap: StrokeCap.round,
            ),
            Text(
              '$remaining분',
              style: HaruText.tiny.copyWith(
                color: HaruTokensV2.inkBody,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
