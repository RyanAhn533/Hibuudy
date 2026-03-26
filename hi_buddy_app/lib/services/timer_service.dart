import 'dart:async';

/// 간단한 카운트다운 타이머 서비스
class TimerService {
  static Timer? _timer;
  static int _remaining = 0;
  static bool _isPaused = false;

  /// 타이머 시작
  /// [seconds] 카운트다운 초
  /// [onComplete] 타이머 완료 시 콜백
  /// [onTick] 매초 남은 시간(초) 콜백
  static void startTimer(
    int seconds,
    Function onComplete,
    Function(int) onTick,
  ) {
    cancel();
    _remaining = seconds;
    _isPaused = false;

    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_isPaused) return;

      _remaining--;
      onTick(_remaining);

      if (_remaining <= 0) {
        timer.cancel();
        _timer = null;
        onComplete();
      }
    });
  }

  /// 타이머 일시정지
  static void pause() {
    _isPaused = true;
  }

  /// 타이머 재개
  static void resume() {
    _isPaused = false;
  }

  /// 일시정지 상태인지
  static bool get isPaused => _isPaused;

  /// 남은 시간(초)
  static int get remaining => _remaining;

  /// 타이머 취소
  static void cancel() {
    _timer?.cancel();
    _timer = null;
    _remaining = 0;
    _isPaused = false;
  }

  /// 타이머 실행 중인지
  static bool get isRunning => _timer != null && !_isPaused;
}
