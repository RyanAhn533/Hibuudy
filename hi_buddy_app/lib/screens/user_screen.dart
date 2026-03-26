import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../models/schedule_item.dart';
import '../models/recipe.dart';
import '../services/schedule_storage.dart';
import '../services/tts_service.dart';
import '../widgets/activity_card.dart';
import '../widgets/step_card.dart';
import '../widgets/morning_briefing.dart';
import '../widgets/sos_button.dart';
import '../services/ui_mode_service.dart';

class UserScreen extends StatefulWidget {
  const UserScreen({super.key});

  @override
  State<UserScreen> createState() => _UserScreenState();
}

class _UserScreenState extends State<UserScreen> {
  Schedule? _schedule;
  Timer? _timer;
  Timer? _kioskAutoTimer; // 키오스크 모드 자동 진행 타이머
  String? _selectedMenu;
  String _healthRoutineId = 'seated';
  bool _isOfflineFallback = false; // 오프라인 폴백으로 불러온 스케줄인지
  bool _isLoading = true; // 초기 로딩 상태
  String? _lastActiveTime; // 이전 활성 활동의 시간 (전환 감지용)
  bool _autoTtsPlayed = false; // 현재 활동에 대한 자동 TTS 재생 여부
  int _kioskStepIndex = 0; // 키오스크 모드 현재 단계 인덱스

  @override
  void initState() {
    super.initState();
    _loadSchedule();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) {
        _checkActivityTransition();
        setState(() {}); // refresh to update active item
      }
    });
    // 키오스크 모드: 30초마다 자동 단계 진행
    if (UiModeService.isKiosk) {
      _kioskAutoTimer = Timer.periodic(const Duration(seconds: 30), (_) {
        if (mounted) {
          setState(() => _kioskStepIndex++);
          _speakCurrentStep();
        }
      });
    }
  }

  /// 활동 전환 감지: 활성 활동이 바뀌면 TTS 안내 + 진동
  void _checkActivityTransition() {
    final (active, _) = _findActiveAndNext();
    if (active != null && _lastActiveTime != null && active.time != _lastActiveTime) {
      // 활동이 바뀜 - 진동 + TTS 안내
      HapticFeedback.heavyImpact();
      _autoTtsPlayed = false; // 새 활동이면 자동 TTS 다시 재생
      _kioskStepIndex = 0; // 키오스크 단계 초기화
      if (UiModeService.isAccessibilityMode) {
        // simple/kiosk: 자동으로 활동 안내
        final header = _headerText(active.type);
        TtsService.speak('$header 시간이에요. 오늘 할 일은 ${active.task} 입니다.');
        _autoTtsPlayed = true;
      } else {
        TtsService.speak('다음 활동 시간이에요');
      }
    }
    _lastActiveTime = active?.time;
  }

  /// 키오스크 모드: 현재 단계 음성 안내
  void _speakCurrentStep() {
    final (active, _) = _findActiveAndNext();
    if (active == null) return;
    if (active.guideScript.isNotEmpty && _kioskStepIndex < active.guideScript.length) {
      TtsService.speak('${_kioskStepIndex + 1}단계. ${active.guideScript[_kioskStepIndex]}');
    }
  }

  /// simple/kiosk 모드: 화면 로드 시 자동 TTS
  void _autoSpeakActivity() {
    if (!UiModeService.isAccessibilityMode || _autoTtsPlayed) return;
    final (active, _) = _findActiveAndNext();
    if (active != null) {
      final header = _headerText(active.type);
      TtsService.speak('$header 시간이에요. 오늘 할 일은 ${active.task} 입니다.');
      _autoTtsPlayed = true;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _kioskAutoTimer?.cancel();
    TtsService.stop();
    super.dispose();
  }

  Future<void> _loadSchedule() async {
    try {
      final schedule = await ScheduleStorage.load();
      if (mounted) {
        final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
        setState(() {
          _schedule = schedule;
          _isLoading = false;
          // 오늘 날짜가 아닌 스케줄이면 오프라인 폴백 표시
          _isOfflineFallback =
              schedule != null && schedule.date != today;
        });
        // 초기 활성 활동 시간 기록 (첫 로드 시 전환 알림 방지)
        final (active, _) = _findActiveAndNext();
        _lastActiveTime = active?.time;
        // simple/kiosk 모드: 로드 완료 후 자동 TTS
        _autoSpeakActivity();
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  (ScheduleItem?, ScheduleItem?) _findActiveAndNext() {
    if (_schedule == null || _schedule!.items.isEmpty) return (null, null);

    final now = DateTime.now();
    final nowMinutes = now.hour * 60 + now.minute;

    ScheduleItem? active;
    ScheduleItem? next;

    for (int i = 0; i < _schedule!.items.length; i++) {
      final item = _schedule!.items[i];
      if (item.timeMinutes <= nowMinutes) {
        active = item;
        if (i + 1 < _schedule!.items.length) {
          next = _schedule!.items[i + 1];
        }
      }
    }

    if (active == null && _schedule!.items.isNotEmpty) {
      next = _schedule!.items.first;
    }

    return (active, next);
  }

  @override
  Widget build(BuildContext context) {
    // ── 로딩 중 ──
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('오늘 하루')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text(
                '일정을 불러오고 있어요...',
                style: TextStyle(fontSize: 18, color: HiBuddyColors.textMuted),
              ),
            ],
          ),
        ),
      );
    }

    // ── 일정 없음: 접근성 있는 빈 화면 ──
    if (_schedule == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('오늘 하루')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 100,
                  height: 100,
                  decoration: const BoxDecoration(
                    color: HiBuddyColors.primaryBg,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.calendar_today,
                    size: 48,
                    color: HiBuddyColors.primary,
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  '오늘 일정이 아직 없어요',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    color: HiBuddyColors.text,
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  '코디네이터 선생님께\n일정을 만들어 달라고 해주세요',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 18,
                    color: HiBuddyColors.textMuted,
                    height: 1.6,
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => TtsService.speak(
                      '오늘 일정이 아직 없어요. 코디네이터 선생님께 일정을 만들어 달라고 해주세요.',
                    ),
                    icon: const Icon(Icons.volume_up, size: 28),
                    label: const Text(
                      '안내 듣기',
                      style: TextStyle(fontSize: 18),
                    ),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final (active, next) = _findActiveAndNext();
    final isAccessible = UiModeService.isAccessibilityMode;
    final textSize = UiModeService.fontSize;
    final headSize = UiModeService.headerSize;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          '오늘 하루',
          style: TextStyle(fontSize: isAccessible ? headSize : null),
        ),
        // 키오스크 모드에서는 뒤로가기 버튼 제거
        automaticallyImplyLeading: !UiModeService.isKiosk,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, size: UiModeService.iconSize),
            onPressed: () {
              setState(() => _isLoading = true);
              _loadSchedule();
            },
            tooltip: '새로고침',
          ),
        ],
      ),
      floatingActionButton: SosButton.floatingButton(context),
      body: Row(
        children: [
          // ── Main Content ──
          Expanded(
            flex: 3,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── 오프라인 폴백 알림 배너 ──
                  if (_isOfflineFallback)
                    Container(
                      width: double.infinity,
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF3CD),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: HiBuddyColors.warning,
                          width: 2,
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.wifi_off,
                            color: HiBuddyColors.warning,
                            size: 28,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              '${_schedule!.date} 일정을 보여드려요.\n새 일정은 코디네이터 선생님이 저장하면 나와요.',
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF856404),
                                height: 1.5,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                  // 아침 브리핑 (날씨 + 인사 + 일정 요약)
                  MorningBriefing(
                    activityCount: _schedule?.items.length ?? 0,
                  ),

                  const SizedBox(height: 16),

                  if (active == null) ...[
                    Container(
                      width: double.infinity,
                      padding: EdgeInsets.all(isAccessible ? 28 : 20),
                      decoration: BoxDecoration(
                        color: HiBuddyColors.primaryBg,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Column(
                        children: [
                          Text(
                            '아직 첫 활동 전이에요.',
                            style: TextStyle(
                              fontSize: isAccessible ? 24 : 18,
                              color: HiBuddyColors.text,
                            ),
                          ),
                          if (next != null) ...[
                            const SizedBox(height: 8),
                            Text(
                              '다음 활동: ${next.time} - ${next.task}',
                              style: TextStyle(
                                fontSize: isAccessible ? 22 : 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 8),
                            SizedBox(
                              height: UiModeService.buttonHeight,
                              child: ElevatedButton.icon(
                                onPressed: () => TtsService.speak(
                                  '다음 활동은 ${next.time}에 시작하는 ${next.task} 입니다.',
                                ),
                                icon: Icon(Icons.volume_up, size: UiModeService.iconSize),
                                label: Text(
                                  '다음 활동 듣기',
                                  style: TextStyle(fontSize: textSize),
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ] else ...[
                    // ── Activity Header ──
                    _buildActivityHeader(active),
                    const SizedBox(height: 8),
                    // TTS button for current activity
                    SizedBox(
                      width: double.infinity,
                      height: UiModeService.buttonHeight,
                      child: OutlinedButton.icon(
                        onPressed: () {
                          final header = _headerText(active.type);
                          TtsService.speak(
                            '$header 시간이에요. 오늘 할 일은 ${active.task} 입니다.',
                          );
                        },
                        icon: Icon(Icons.volume_up, size: UiModeService.iconSize),
                        label: Text(
                          '현재 활동 요약 듣기',
                          style: TextStyle(fontSize: textSize),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Divider(),
                    const SizedBox(height: 8),
                    // ── Activity-specific content ──
                    _buildActivityContent(active),
                  ],
                ],
              ),
            ),
          ),

          // ── Sidebar Timeline ──
          if (MediaQuery.of(context).size.width > 600)
            SizedBox(
              width: 250,
              child: Container(
                color: Colors.white,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (next != null) ...[
                        _sidebarSection('다음 활동'),
                        ActivityCard(
                          type: next.type,
                          task: next.task,
                          time: next.time,
                        ),
                        const Divider(),
                      ],
                      _sidebarSection('오늘 타임라인'),
                      ..._schedule!.items.map((item) {
                        final isActive = item == active;
                        final isPast = active != null &&
                            item.timeMinutes < active.timeMinutes;
                        return _timelineItem(item, isActive, isPast);
                      }),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildActivityHeader(ScheduleItem item) {
    final color = HiBuddyColors.getActivityColor(item.type);
    final bgColor = HiBuddyColors.getActivityBgColor(item.type);
    final emoji = HiBuddyColors.getActivityEmoji(item.type);
    final isAccessible = UiModeService.isAccessibilityMode;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(isAccessible ? 28 : 20),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$emoji ${_headerText(item.type)}',
            style: TextStyle(
              fontSize: isAccessible ? 34 : 26,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            item.task,
            style: TextStyle(
              fontSize: isAccessible ? 24 : 18,
              color: color.withAlpha(200),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActivityContent(ScheduleItem item) {
    final type = item.type.toUpperCase();
    switch (type) {
      case 'COOKING':
      case 'MEAL':
        return _buildCookingView(item);
      case 'HEALTH':
        return _buildHealthView(item);
      default:
        return _buildGeneralView(item);
    }
  }

  Widget _buildCookingView(ScheduleItem item) {
    final color = HiBuddyColors.cooking;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Guide script
        if (item.guideScript.isNotEmpty)
          StepsList(
            title: '오늘 요리 안내',
            steps: item.guideScript,
            color: color,
          ),

        if (item.menus.isNotEmpty) ...[
          const SizedBox(height: 16),
          _sectionTitle('메뉴 선택'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: item.menus.map((m) {
              final isSelected = _selectedMenu == m.name;
              return ChoiceChip(
                label: Text(
                  m.name,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: isSelected ? Colors.white : color,
                  ),
                ),
                selected: isSelected,
                selectedColor: color,
                backgroundColor: HiBuddyColors.cookingBg,
                onSelected: (_) {
                  setState(() => _selectedMenu = m.name);
                },
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
              );
            }).toList(),
          ),
        ],

        if (_selectedMenu != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: HiBuddyColors.cookingBg,
              borderRadius: BorderRadius.circular(14),
              border: Border(
                left: BorderSide(color: color, width: 5),
              ),
            ),
            child: Text(
              '선택된 메뉴: $_selectedMenu',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          const SizedBox(height: 12),
          _buildRecipeDetail(_selectedMenu!),
        ],
      ],
    );
  }

  Widget _buildRecipeDetail(String menuName) {
    final recipe = getRecipe(menuName);
    if (recipe == null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: HiBuddyColors.primaryBg,
          borderRadius: BorderRadius.circular(14),
        ),
        child: const Text(
          '이 메뉴의 상세 레시피가 등록되어 있지 않아요.',
          style: TextStyle(fontSize: 15),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (recipe.tools.isNotEmpty) ...[
          _sectionTitle('준비물'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: recipe.tools.map((t) {
              return Chip(
                label: Text(t),
                backgroundColor: HiBuddyColors.cookingBg,
                labelStyle: const TextStyle(color: Color(0xFF9A3412)),
              );
            }).toList(),
          ),
        ],
        if (recipe.ingredients.isNotEmpty) ...[
          const SizedBox(height: 12),
          _sectionTitle('재료'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: recipe.ingredients.map((i) {
              return Chip(
                label: Text(i),
                backgroundColor: HiBuddyColors.generalBg,
              );
            }).toList(),
          ),
        ],
        const SizedBox(height: 12),
        StepsList(
          title: '레시피 단계',
          steps: recipe.steps,
          color: HiBuddyColors.cooking,
        ),
      ],
    );
  }

  Widget _buildHealthView(ScheduleItem item) {
    final color = HiBuddyColors.health;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle('운동 방식 선택'),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _choiceButton(
                '앉아서 하는 운동',
                _healthRoutineId == 'seated',
                () => setState(() => _healthRoutineId = 'seated'),
                color,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _choiceButton(
                '서서 하는 운동',
                _healthRoutineId == 'standing',
                () => setState(() => _healthRoutineId = 'standing'),
                color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Builder(
          builder: (context) {
            final routine = getHealthRoutine(_healthRoutineId);
            if (routine == null) {
              return const Text('운동 루틴을 불러오지 못했습니다.');
            }
            return StepsList(
              title: routine.title,
              steps: routine.steps,
              color: color,
            );
          },
        ),
        if (item.guideScript.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Divider(),
          StepsList(
            title: '추가 안내',
            steps: item.guideScript,
            color: color,
          ),
        ],
      ],
    );
  }

  Widget _buildGeneralView(ScheduleItem item) {
    final color = HiBuddyColors.getActivityColor(item.type);
    if (item.guideScript.isEmpty) {
      return Container(
        padding: EdgeInsets.all(UiModeService.isAccessibilityMode ? 28 : 20),
        decoration: BoxDecoration(
          color: HiBuddyColors.getActivityBgColor(item.type),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(
          item.task,
          style: TextStyle(fontSize: UiModeService.fontSize + 2),
        ),
      );
    }
    return StepsList(
      title: '안내',
      steps: item.guideScript,
      color: color,
    );
  }

  Widget _choiceButton(
    String label,
    bool isSelected,
    VoidCallback onTap,
    Color color,
  ) {
    return Semantics(
      label: label,
      selected: isSelected,
      button: true,
      child: Material(
        color: isSelected ? color.withAlpha(30) : Colors.white,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(14),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: isSelected ? color : HiBuddyColors.border,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 15,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                color: isSelected ? color : HiBuddyColors.text,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _sectionTitle(String text) {
    return Container(
      padding: const EdgeInsets.only(bottom: 8),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: HiBuddyColors.primary, width: 3),
        ),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: UiModeService.isAccessibilityMode ? 24 : 18,
          fontWeight: FontWeight.w700,
          color: HiBuddyColors.text,
        ),
      ),
    );
  }

  Widget _sidebarSection(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w700,
          color: HiBuddyColors.text,
        ),
      ),
    );
  }

  Widget _timelineItem(ScheduleItem item, bool isActive, bool isPast) {
    final emoji = HiBuddyColors.getActivityEmoji(item.type);
    final dotColor = isActive
        ? HiBuddyColors.success
        : isPast
            ? HiBuddyColors.textMuted
            : HiBuddyColors.border;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: isActive ? HiBuddyColors.successBg : Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: isActive
            ? Border.all(color: HiBuddyColors.success, width: 2)
            : Border.all(color: HiBuddyColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: dotColor,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(emoji, style: const TextStyle(fontSize: 14)),
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              '${item.time} ${item.task}',
              style: TextStyle(
                fontSize: 13,
                fontWeight: isActive ? FontWeight.w700 : FontWeight.normal,
                color: isPast
                    ? HiBuddyColors.textMuted
                    : HiBuddyColors.text,
                decoration: isPast ? TextDecoration.lineThrough : null,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  String _headerText(String type) {
    const map = {
      'MORNING_BRIEFING': '아침 준비',
      'COOKING': '요리/식사',
      'MEAL': '요리/식사',
      'HEALTH': '운동',
      'REST': '쉬는 시간',
      'LEISURE': '여가',
      'CLOTHING': '옷 입기',
      'NIGHT_WRAPUP': '마무리',
    };
    return map[type.toUpperCase()] ?? '활동';
  }
}
