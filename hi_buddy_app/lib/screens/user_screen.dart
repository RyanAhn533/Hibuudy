import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../models/schedule_item.dart';
import '../models/recipe.dart';
import '../services/schedule_storage.dart';
import '../services/tts_service.dart';
import '../widgets/activity_card.dart';
import '../widgets/step_card.dart';

class UserScreen extends StatefulWidget {
  const UserScreen({super.key});

  @override
  State<UserScreen> createState() => _UserScreenState();
}

class _UserScreenState extends State<UserScreen> {
  Schedule? _schedule;
  Timer? _timer;
  String? _selectedMenu;
  String _healthRoutineId = 'seated';

  @override
  void initState() {
    super.initState();
    _loadSchedule();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) setState(() {}); // refresh to update active item
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    TtsService.stop();
    super.dispose();
  }

  Future<void> _loadSchedule() async {
    final schedule = await ScheduleStorage.load();
    if (mounted) {
      setState(() => _schedule = schedule);
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

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return '🌅 좋은 아침이에요';
    if (hour < 18) return '☀️ 좋은 오후예요';
    return '🌙 좋은 저녁이에요';
  }

  @override
  Widget build(BuildContext context) {
    if (_schedule == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('따라 하기')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.calendar_today, size: 64, color: HiBuddyColors.textMuted),
              SizedBox(height: 16),
              Text(
                '오늘 일정이 없습니다.\n코디네이터 페이지에서 먼저 저장해 주세요.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: HiBuddyColors.textMuted),
              ),
            ],
          ),
        ),
      );
    }

    final (active, next) = _findActiveAndNext();

    return Scaffold(
      appBar: AppBar(
        title: const Text('오늘 따라하기'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              _loadSchedule();
              setState(() {});
            },
            tooltip: '새로고침',
          ),
        ],
      ),
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
                  // Greeting banner
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [HiBuddyColors.primaryBg, Color(0xFFDBEAFE)],
                      ),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _getGreeting(),
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                            color: HiBuddyColors.text,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '오늘도 하이버디랑 함께 해볼까요?  ${DateFormat('yyyy-MM-dd HH:mm').format(DateTime.now())}',
                          style: const TextStyle(
                            fontSize: 14,
                            color: HiBuddyColors.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),

                  if (active == null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: HiBuddyColors.primaryBg,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Column(
                        children: [
                          const Text(
                            '아직 첫 활동 전이에요.',
                            style: TextStyle(
                              fontSize: 18,
                              color: HiBuddyColors.text,
                            ),
                          ),
                          if (next != null) ...[
                            const SizedBox(height: 8),
                            Text(
                              '다음 활동: ${next.time} - ${next.task}',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 8),
                            ElevatedButton.icon(
                              onPressed: () => TtsService.speak(
                                '다음 활동은 ${next.time}에 시작하는 ${next.task} 입니다.',
                              ),
                              icon: const Icon(Icons.volume_up),
                              label: const Text('다음 활동 듣기'),
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
                      child: OutlinedButton.icon(
                        onPressed: () {
                          final header = _headerText(active.type);
                          TtsService.speak(
                            '$header 시간이에요. 오늘 할 일은 ${active.task} 입니다.',
                          );
                        },
                        icon: const Icon(Icons.volume_up),
                        label: const Text('현재 활동 요약 듣기'),
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

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
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
              fontSize: 26,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            item.task,
            style: TextStyle(
              fontSize: 18,
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
              '🍳 선택된 메뉴: $_selectedMenu',
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
                '🪑 앉아서 하는 운동',
                _healthRoutineId == 'seated',
                () => setState(() => _healthRoutineId = 'seated'),
                color,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _choiceButton(
                '🧍 서서 하는 운동',
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
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: HiBuddyColors.getActivityBgColor(item.type),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(
          item.task,
          style: const TextStyle(fontSize: 18),
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
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isSelected ? color.withAlpha(30) : Colors.white,
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
        style: const TextStyle(
          fontSize: 18,
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
