import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/tts_service.dart';
import '../screens/timer_screen.dart';

class StepCard extends StatelessWidget {
  final int stepNumber;
  final String text;
  final Color color;
  final bool isCompleted;
  final ValueChanged<bool>? onCompletedChanged;

  const StepCard({
    super.key,
    required this.stepNumber,
    required this.text,
    this.color = HiBuddyColors.primary,
    this.isCompleted = false,
    this.onCompletedChanged,
  });

  /// 텍스트에서 시간 키워드를 찾아 분 단위로 반환 (없으면 null)
  static int? _extractTimerMinutes(String text) {
    final minuteMatch = RegExp(r'(\d+)\s*분').firstMatch(text);
    if (minuteMatch != null) {
      return int.tryParse(minuteMatch.group(1)!);
    }
    final secondMatch = RegExp(r'(\d+)\s*초').firstMatch(text);
    if (secondMatch != null) {
      final seconds = int.tryParse(secondMatch.group(1)!) ?? 0;
      if (seconds > 0) {
        return (seconds / 60).ceil().clamp(1, 999);
      }
    }
    return null;
  }

  static bool _hasTimeKeyword(String text) {
    return RegExp(r'\d+\s*(분|초)').hasMatch(text) ||
        text.contains('기다려') ||
        text.contains('기다리') ||
        text.contains('끓여') ||
        text.contains('끓이') ||
        text.contains('익혀') ||
        text.contains('익히');
  }

  @override
  Widget build(BuildContext context) {
    final timerMinutes = _hasTimeKeyword(text) ? _extractTimerMinutes(text) : null;

    return Semantics(
      label: '$stepNumber단계. $text${isCompleted ? " 완료" : ""}',
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: HaruTokens.space1),
        padding: const EdgeInsets.all(HaruTokens.space4),
        decoration: BoxDecoration(
          color: isCompleted ? HaruTokensV2.successSoft : HaruTokensV2.surfaceCard,
          borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
          border: Border.all(
            color: isCompleted ? HaruTokensV2.success : HaruTokensV2.borderSoft,
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (onCompletedChanged != null)
              Padding(
                padding: const EdgeInsets.only(right: HaruTokens.space2),
                // 터치 타겟 48pt (minTouchTarget), 체크 표시는 1.4배 확대
                child: SizedBox(
                  width: HaruTokensV2.minTouchTarget,
                  height: HaruTokensV2.minTouchTarget,
                  child: Transform.scale(
                    scale: 1.4,
                    child: Checkbox(
                      value: isCompleted,
                      onChanged: (v) => onCompletedChanged?.call(v ?? false),
                      activeColor: HaruTokensV2.success,
                      materialTapTargetSize: MaterialTapTargetSize.padded,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ),
                  ),
                ),
              ),
            if (isCompleted)
              Container(
                width: 36,
                height: 36,
                decoration: const BoxDecoration(
                  color: HaruTokensV2.success,
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: const Icon(Icons.check, color: Colors.white, size: 22),
              )
            else
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: Text(
                  '$stepNumber',
                  style: HaruText.body.copyWith(
                    color: HaruTokensV2.surfaceCard,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            const SizedBox(width: HaruTokens.space3),
            Expanded(
              child: Text(
                text,
                style: HaruText.body.copyWith(
                  color: HaruTokensV2.inkPrimary,
                  decoration: isCompleted ? TextDecoration.lineThrough : null,
                ),
              ),
            ),
            // R2: 아이콘 + 라벨 쌍. 56pt.
            if (timerMinutes != null)
              _StepAction(
                icon: Icons.timer,
                label: '$timerMinutes분',
                color: HaruTokensV2.actMealMain,
                semantics: '$timerMinutes분 타이머',
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => TimerScreen(
                        minutes: timerMinutes,
                        label: '$stepNumber단계 타이머',
                      ),
                    ),
                  );
                },
              ),
            _StepAction(
              icon: Icons.volume_up,
              label: '듣기',
              color: color,
              semantics: '$stepNumber단계 듣기',
              onTap: () => TtsService.speak('$stepNumber단계. $text'),
            ),
          ],
        ),
      ),
    );
  }
}

class StepsList extends StatefulWidget {
  final String title;
  final List<String> steps;
  final Color color;
  /// kiosk 전용 단일 단계 포커스 모드. true면 현재 단계 1개만 크게 표시.
  /// normal/simple은 false로 두고 기존 리스트 UX 유지.
  final bool singleFocusMode;

  const StepsList({
    super.key,
    required this.title,
    required this.steps,
    this.color = HiBuddyColors.primary,
    this.singleFocusMode = false,
  });

  @override
  State<StepsList> createState() => _StepsListState();
}

class _StepsListState extends State<StepsList> {
  late List<bool> _completed;
  bool _allDoneBannerShown = false;

  @override
  void initState() {
    super.initState();
    _completed = List.filled(widget.steps.length, false);
  }

  @override
  void didUpdateWidget(covariant StepsList oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.steps.length != widget.steps.length) {
      _completed = List.filled(widget.steps.length, false);
      _allDoneBannerShown = false;
    }
  }

  void _onStepCompleted(int index, bool value) {
    setState(() {
      _completed[index] = value;
    });
    if (_completed.every((c) => c) && !_allDoneBannerShown) {
      _allDoneBannerShown = true;
      TtsService.speak('잘했어요! 다 했어요!');
    }
  }

  int? get _currentFocusIndex {
    for (int i = 0; i < _completed.length; i++) {
      if (!_completed[i]) return i;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.steps.isEmpty) return const SizedBox.shrink();

    final allDone = _completed.every((c) => c) && _completed.isNotEmpty;
    final completedCount = _completed.where((c) => c).length;
    final total = widget.steps.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(widget.title, style: HaruText.h2),
            ),
            TextButton.icon(
              onPressed: () {
                final allText = widget.steps
                    .asMap()
                    .entries
                    .map((e) => '${e.key + 1}단계. ${e.value}')
                    .join(' ');
                TtsService.speak('전체 단계를 안내할게요. $allText');
              },
              icon: const Icon(Icons.play_circle_outline, size: 20),
              label: const Text('전체 듣기'),
            ),
          ],
        ),
        const SizedBox(height: HaruTokens.space2),

        // 진행 표시
        _ProgressIndicator(
          completed: completedCount,
          total: total,
          color: widget.color,
        ),
        const SizedBox(height: HaruTokens.space3),

        // 모드별 분기
        if (widget.singleFocusMode && !allDone)
          _SingleFocusStep(
            stepIndex: _currentFocusIndex!,
            text: widget.steps[_currentFocusIndex!],
            total: total,
            color: widget.color,
            nextHint: _currentFocusIndex! + 1 < total
                ? widget.steps[_currentFocusIndex! + 1]
                : null,
            onComplete: () => _onStepCompleted(_currentFocusIndex!, true),
          )
        else
          ...widget.steps.asMap().entries.map(
                (e) => StepCard(
                  stepNumber: e.key + 1,
                  text: e.value,
                  color: widget.color,
                  isCompleted: _completed[e.key],
                  onCompletedChanged: (v) => _onStepCompleted(e.key, v),
                ),
              ),

        if (allDone) ...[
          const SizedBox(height: HaruTokens.space3),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(HaruTokens.space5),
            decoration: BoxDecoration(
              color: HaruTokensV2.successSoft,
              borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
              border: Border.all(color: HaruTokensV2.success, width: 2),
            ),
            child: Column(
              children: [
                Text(
                  '잘했어요! 다 했어요!',
                  style: HaruText.h2.copyWith(
                    color: HaruTokensV2.success,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: HaruTokens.space1),
                Text(
                  '모든 단계를 완료했어요!',
                  style: HaruText.body.copyWith(
                    color: HaruTokensV2.inkBody,
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

/// 단계 진행 바 (완료/전체)
class _ProgressIndicator extends StatelessWidget {
  final int completed;
  final int total;
  final Color color;
  const _ProgressIndicator({
    required this.completed,
    required this.total,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final ratio = total == 0 ? 0.0 : completed / total;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$completed / $total 단계',
          style: HaruText.small.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: HaruTokens.space1),
        ClipRRect(
          borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
          child: LinearProgressIndicator(
            value: ratio,
            minHeight: 8,
            backgroundColor: HaruTokens.n200,
            valueColor: AlwaysStoppedAnimation(color),
          ),
        ),
      ],
    );
  }
}

/// 키오스크 모드 — 한 화면 한 단계 풀포커스 카드
class _SingleFocusStep extends StatelessWidget {
  final int stepIndex;
  final String text;
  final int total;
  final Color color;
  final String? nextHint;
  final VoidCallback onComplete;

  const _SingleFocusStep({
    required this.stepIndex,
    required this.text,
    required this.total,
    required this.color,
    required this.nextHint,
    required this.onComplete,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '${stepIndex + 1}단계 / 전체 $total단계. $text',
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(HaruTokens.space6),
        decoration: BoxDecoration(
          color: HaruTokensV2.surfaceCard,
          borderRadius: BorderRadius.circular(HaruTokens.radiusXl),
          border: Border.all(color: color, width: 2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 큰 단계 번호
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text(
                '${stepIndex + 1}',
                style: HaruText.h1.copyWith(color: HaruTokensV2.surfaceCard),
              ),
            ),
            const SizedBox(height: HaruTokens.space4),

            // 단계 본문 (큰 글씨)
            Text(text, style: HaruText.h1),

            const SizedBox(height: HaruTokens.space5),

            // "다 했어요" 버튼 (largeTouchTarget)
            SizedBox(
              width: double.infinity,
              height: HaruTokens.largeTouchTarget,
              child: ElevatedButton.icon(
                onPressed: onComplete,
                icon: const Icon(Icons.check_circle, size: 32),
                label: Text('다 했어요', style: HaruText.h2),
                style: ElevatedButton.styleFrom(
                  backgroundColor: HaruTokensV2.success,
                  foregroundColor: HaruTokensV2.surfaceCard,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(HaruTokens.radiusLg),
                  ),
                ),
              ),
            ),

            const SizedBox(height: HaruTokens.space3),

            // 다시 듣기
            SizedBox(
              width: double.infinity,
              height: HaruTokens.comfortTouchTarget,
              child: OutlinedButton.icon(
                onPressed: () => TtsService.speak('${stepIndex + 1}단계. $text'),
                icon: const Icon(Icons.volume_up),
                label: Text('다시 들려줘', style: HaruText.h3),
              ),
            ),

            // 다음 힌트 (실데이터 있을 때만)
            if (nextHint != null) ...[
              const SizedBox(height: HaruTokens.space4),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(HaruTokens.space3),
                decoration: BoxDecoration(
                  color: HaruTokens.n100,
                  borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.arrow_forward,
                      size: 16,
                      color: HaruTokens.n400,
                    ),
                    const SizedBox(width: HaruTokens.space2),
                    Expanded(
                      child: Text(
                        '다음: $nextHint',
                        style: HaruText.small,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// 단계 카드 우측 액션 — 아이콘 + 라벨 (R2), 56pt
class _StepAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final String semantics;
  final VoidCallback onTap;
  const _StepAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.semantics,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: semantics,
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusSm),
        onTap: onTap,
        child: SizedBox(
          width: HaruTokensV2.comfortTouchTarget,
          height: HaruTokensV2.comfortTouchTarget,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 26, color: color),
              Text(
                label,
                style: HaruText.tiny.copyWith(color: color, fontWeight: FontWeight.w800),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
