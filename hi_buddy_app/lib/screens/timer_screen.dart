import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/timer_service.dart';
import '../services/tts_service.dart';
import '../theme/app_theme.dart';

/// 큰 글씨, 큰 버튼의 접근성 높은 타이머 화면
class TimerScreen extends StatefulWidget {
  final int minutes;
  final String? label;

  const TimerScreen({
    super.key,
    required this.minutes,
    this.label,
  });

  @override
  State<TimerScreen> createState() => _TimerScreenState();
}

class _TimerScreenState extends State<TimerScreen> {
  late int _totalSeconds;
  late int _remaining;
  bool _isRunning = false;
  bool _isPaused = false;
  bool _isCompleted = false;

  @override
  void initState() {
    super.initState();
    _totalSeconds = widget.minutes * 60;
    _remaining = _totalSeconds;
  }

  @override
  void dispose() {
    TimerService.cancel();
    super.dispose();
  }

  void _start() {
    setState(() {
      _isRunning = true;
      _isPaused = false;
      _isCompleted = false;
    });

    TimerService.startTimer(
      _remaining,
      _onComplete,
      _onTick,
    );

    TtsService.speak('타이머 시작할게요. ${widget.minutes}분이에요.');
  }

  void _onTick(int remaining) {
    if (!mounted) return;
    setState(() {
      _remaining = remaining;
    });

    // 30초 남았을 때 알림
    if (remaining == 30) {
      TtsService.speak('30초 남았어요.');
    }
    // 10초 남았을 때 알림
    if (remaining == 10) {
      TtsService.speak('10초 남았어요.');
    }
  }

  void _onComplete() {
    if (!mounted) return;
    setState(() {
      _isRunning = false;
      _isPaused = false;
      _isCompleted = true;
      _remaining = 0;
    });

    // 진동
    HapticFeedback.heavyImpact();

    // TTS 알림
    TtsService.speak('시간이 다 됐어요!');

    // 완료 다이얼로그
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text(
          '시간이 다 됐어요!',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
          textAlign: TextAlign.center,
        ),
        content: Text(
          widget.label != null ? '${widget.label} 완료!' : '타이머가 끝났어요.',
          style: const TextStyle(fontSize: 20),
          textAlign: TextAlign.center,
        ),
        actionsAlignment: MainAxisAlignment.center,
        actions: [
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton(
              onPressed: () {
                Navigator.of(ctx).pop();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: HiBuddyColors.success,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
              child: const Text(
                '확인',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _pause() {
    TimerService.pause();
    setState(() {
      _isPaused = true;
    });
  }

  void _resume() {
    TimerService.resume();
    setState(() {
      _isPaused = false;
    });
  }

  void _reset() {
    TimerService.cancel();
    setState(() {
      _remaining = _totalSeconds;
      _isRunning = false;
      _isPaused = false;
      _isCompleted = false;
    });
  }

  String _formatTime(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  double get _progress {
    if (_totalSeconds == 0) return 0;
    return _remaining / _totalSeconds;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.label ?? '타이머'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 28),
          onPressed: () {
            TimerService.cancel();
            Navigator.of(context).pop();
          },
          tooltip: '뒤로 가기',
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const SizedBox(height: 32),

              // 라벨
              if (widget.label != null)
                Text(
                  widget.label!,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                    color: HiBuddyColors.textMuted,
                  ),
                  textAlign: TextAlign.center,
                ),

              const SizedBox(height: 24),

              // 원형 프로그레스 + 시간 표시
              Expanded(
                child: Center(
                  child: SizedBox(
                    width: 280,
                    height: 280,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        // 배경 원
                        SizedBox(
                          width: 280,
                          height: 280,
                          child: CircularProgressIndicator(
                            value: 1.0,
                            strokeWidth: 12,
                            color: HiBuddyColors.border,
                            backgroundColor: Colors.transparent,
                          ),
                        ),
                        // 프로그레스 원
                        SizedBox(
                          width: 280,
                          height: 280,
                          child: CircularProgressIndicator(
                            value: _progress,
                            strokeWidth: 12,
                            color: _isCompleted
                                ? HiBuddyColors.success
                                : _remaining <= 10 && _isRunning
                                    ? HiBuddyColors.danger
                                    : HiBuddyColors.primary,
                            backgroundColor: Colors.transparent,
                            strokeCap: StrokeCap.round,
                          ),
                        ),
                        // 시간 텍스트
                        Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              _formatTime(_remaining),
                              style: TextStyle(
                                fontSize: 72,
                                fontWeight: FontWeight.w800,
                                color: _isCompleted
                                    ? HiBuddyColors.success
                                    : _remaining <= 10 && _isRunning
                                        ? HiBuddyColors.danger
                                        : HiBuddyColors.text,
                                fontFeatures: const [
                                  FontFeature.tabularFigures(),
                                ],
                              ),
                            ),
                            if (_isCompleted)
                              const Text(
                                '완료!',
                                style: TextStyle(
                                  fontSize: 24,
                                  fontWeight: FontWeight.w700,
                                  color: HiBuddyColors.success,
                                ),
                              ),
                            if (_isPaused)
                              const Text(
                                '일시정지',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.w600,
                                  color: HiBuddyColors.textMuted,
                                ),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // 컨트롤 버튼
              if (!_isRunning && !_isCompleted)
                // 시작 버튼
                SizedBox(
                  width: double.infinity,
                  height: 64,
                  child: ElevatedButton.icon(
                    onPressed: _start,
                    icon: const Icon(Icons.play_arrow, size: 32),
                    label: const Text(
                      '시작',
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: HiBuddyColors.primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),
                ),

              if (_isRunning)
                Row(
                  children: [
                    // 일시정지/재개
                    Expanded(
                      child: SizedBox(
                        height: 64,
                        child: ElevatedButton.icon(
                          onPressed: _isPaused ? _resume : _pause,
                          icon: Icon(
                            _isPaused ? Icons.play_arrow : Icons.pause,
                            size: 32,
                          ),
                          label: Text(
                            _isPaused ? '계속' : '잠깐 멈춤',
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _isPaused
                                ? HiBuddyColors.success
                                : HiBuddyColors.secondary,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    // 취소
                    SizedBox(
                      height: 64,
                      width: 100,
                      child: ElevatedButton(
                        onPressed: _reset,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: HiBuddyColors.danger,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                        child: const Icon(Icons.stop, size: 32),
                      ),
                    ),
                  ],
                ),

              if (_isCompleted)
                Row(
                  children: [
                    // 다시 시작
                    Expanded(
                      child: SizedBox(
                        height: 64,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            _reset();
                            _start();
                          },
                          icon: const Icon(Icons.replay, size: 28),
                          label: const Text(
                            '다시 시작',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: HiBuddyColors.primary,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    // 닫기
                    Expanded(
                      child: SizedBox(
                        height: 64,
                        child: ElevatedButton.icon(
                          onPressed: () => Navigator.of(context).pop(),
                          icon: const Icon(Icons.check, size: 28),
                          label: const Text(
                            '닫기',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: HiBuddyColors.success,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
