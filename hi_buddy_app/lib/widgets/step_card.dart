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
    // "N분" 패턴
    final minuteMatch = RegExp(r'(\d+)\s*분').firstMatch(text);
    if (minuteMatch != null) {
      return int.tryParse(minuteMatch.group(1)!);
    }
    // "N초" 패턴 — 1분 미만이면 1분으로 올림
    final secondMatch = RegExp(r'(\d+)\s*초').firstMatch(text);
    if (secondMatch != null) {
      final seconds = int.tryParse(secondMatch.group(1)!) ?? 0;
      if (seconds > 0) {
        return (seconds / 60).ceil().clamp(1, 999);
      }
    }
    return null;
  }

  /// 시간 관련 키워드가 포함되어 있는지
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
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isCompleted ? const Color(0xFFD1FAE5) : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isCompleted ? HiBuddyColors.success : HiBuddyColors.border,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (onCompletedChanged != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: SizedBox(
                width: 32,
                height: 32,
                child: Checkbox(
                  value: isCompleted,
                  onChanged: (v) => onCompletedChanged?.call(v ?? false),
                  activeColor: HiBuddyColors.success,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
              ),
            ),
          if (isCompleted)
            Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: HiBuddyColors.success,
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
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 16,
                ),
              ),
            ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 17,
                height: 1.5,
                color: HiBuddyColors.text,
                decoration: isCompleted ? TextDecoration.lineThrough : null,
              ),
            ),
          ),
          // 타이머 버튼 (시간 키워드가 있을 때만 표시)
          if (timerMinutes != null)
            SizedBox(
              width: 48,
              height: 48,
              child: IconButton(
                icon: const Icon(Icons.timer, size: 28),
                color: HiBuddyColors.cooking,
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => TimerScreen(
                        minutes: timerMinutes,
                        label: '$stepNumber단계 타이머',
                      ),
                    ),
                  );
                },
                tooltip: '$timerMinutes분 타이머',
                padding: EdgeInsets.zero,
              ),
            ),
          SizedBox(
            width: 48,
            height: 48,
            child: IconButton(
              icon: const Icon(Icons.volume_up, size: 32),
              color: color,
              onPressed: () => TtsService.speak('$stepNumber단계. $text'),
              tooltip: '$stepNumber단계 듣기',
              padding: EdgeInsets.zero,
            ),
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

  const StepsList({
    super.key,
    required this.title,
    required this.steps,
    this.color = HiBuddyColors.primary,
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
    // Check if all steps completed
    if (_completed.every((c) => c) && !_allDoneBannerShown) {
      _allDoneBannerShown = true;
      TtsService.speak('잘했어요! 다 했어요!');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.steps.isEmpty) return const SizedBox.shrink();

    final allDone = _completed.every((c) => c) && _completed.isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              widget.title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: HiBuddyColors.text,
              ),
            ),
            const Spacer(),
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
        const SizedBox(height: 8),
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
          const SizedBox(height: 12),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: HiBuddyColors.successBg,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: HiBuddyColors.success, width: 2),
            ),
            child: const Column(
              children: [
                Text(
                  '잘했어요! 다 했어요!',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF065F46),
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  '모든 단계를 완료했어요!',
                  style: TextStyle(
                    fontSize: 16,
                    color: Color(0xFF047857),
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
