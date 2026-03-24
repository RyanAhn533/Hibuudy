import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../models/schedule_item.dart';
import '../services/api_service.dart';
import '../services/schedule_storage.dart';
import '../widgets/activity_card.dart';

class CoordinatorScreen extends StatefulWidget {
  const CoordinatorScreen({super.key});

  @override
  State<CoordinatorScreen> createState() => _CoordinatorScreenState();
}

class _CoordinatorScreenState extends State<CoordinatorScreen> {
  final _textController = TextEditingController(
    text: '08:00 · 오늘 일정 간단 안내\n'
        '10:00 · 옷 입기 연습하기\n'
        '12:00 · 라면 또는 카레 중 하나 먹기\n'
        '15:00 · 쉬는 시간 갖기\n'
        '18:00 · 열심히 운동하기\n'
        '22:00 · 하루 마무리 인사하기',
  );

  List<ScheduleItem> _schedule = [];
  bool _isGenerating = false;
  bool _isSaving = false;
  int? _expandedIndex;

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _generateSchedule() async {
    if (_textController.text.trim().isEmpty) {
      _showErrorDialog('입력 필요', '일정 내용을 입력해 주세요.');
      return;
    }
    setState(() => _isGenerating = true);
    try {
      final items = await ApiService.generateSchedule(_textController.text);
      if (mounted) {
        setState(() {
          _schedule = items;
          _expandedIndex = null;
        });
      }
    } catch (e) {
      if (mounted) {
        final message = e.toString().replaceFirst('Exception: ', '');
        _showErrorDialog(
          '일정 생성 실패',
          '$message\n\n인터넷 연결을 확인하고 다시 시도해 주세요.',
        );
      }
    } finally {
      if (mounted) setState(() => _isGenerating = false);
    }
  }

  Future<void> _saveSchedule() async {
    setState(() => _isSaving = true);
    try {
      final schedule = Schedule(
        date: DateFormat('yyyy-MM-dd').format(DateTime.now()),
        items: _schedule,
      );
      await ScheduleStorage.save(schedule);
      // 서버에도 저장 (실패해도 로컬은 이미 저장됨)
      try {
        await ApiService.saveScheduleToServer(
          'default_user', // TODO: 인증 구현 후 실제 user_id로 교체
          schedule.date,
          schedule.items.map((i) => i.toJson()).toList(),
        );
      } catch (_) {
        // 서버 저장 실패는 무시 (로컬에는 저장됨)
      }
      if (mounted) {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            title: const Row(
              children: [
                Icon(Icons.check_circle, color: HiBuddyColors.success, size: 28),
                SizedBox(width: 8),
                Text('저장 완료!', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              ],
            ),
            content: const Text(
              '일정이 저장되었어요.\n"오늘 하루" 화면에서 확인할 수 있어요.',
              style: TextStyle(fontSize: 16, height: 1.6),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('여기 계속하기'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.pop(context); // 홈으로 돌아가기
                },
                child: const Text('오늘 하루 보기'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        _showErrorDialog('저장 실패', e.toString());
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  void _editItem(int index) {
    final item = _schedule[index];
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _EditItemSheet(
        item: item,
        onSave: (updated) {
          setState(() {
            _schedule[index] = updated;
            _schedule.sort((a, b) => a.timeMinutes.compareTo(b.timeMinutes));
          });
        },
      ),
    );
  }

  void _deleteItem(int index) {
    setState(() {
      _schedule.removeAt(index);
    });
  }

  /// 내일도 같은 일정 사용 (copy schedule to tomorrow)
  Future<void> _copyToTomorrow() async {
    final tomorrow = DateTime.now().add(const Duration(days: 1));
    final tomorrowStr = DateFormat('yyyy-MM-dd').format(tomorrow);
    final schedule = Schedule(date: tomorrowStr, items: _schedule);
    await ScheduleStorage.save(schedule);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$tomorrowStr 일정으로 복사되었어요!'),
          backgroundColor: HiBuddyColors.success,
        ),
      );
    }
  }

  /// 새 일정 항목 수동 추가
  void _addNewItem() {
    final timeCtrl = TextEditingController(text: '09:00');
    final taskCtrl = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: HiBuddyColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              '새 일정 추가',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                SizedBox(
                  width: 100,
                  child: TextField(
                    controller: timeCtrl,
                    decoration: const InputDecoration(labelText: '시간(HH:MM)'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: taskCtrl,
                    decoration: const InputDecoration(labelText: '할 일'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  if (taskCtrl.text.trim().isEmpty) return;
                  final newItem = ScheduleItem(
                    time: timeCtrl.text.trim(),
                    type: 'GENERAL',
                    task: taskCtrl.text.trim(),
                    guideScript: [],
                  );
                  setState(() {
                    _schedule.add(newItem);
                    _schedule.sort(
                        (a, b) => a.timeMinutes.compareTo(b.timeMinutes));
                  });
                  Navigator.pop(ctx);
                },
                child: const Text('추가'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('일정 만들기'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ──
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    HiBuddyColors.primaryBg,
                    HiBuddyColors.primaryBg.withAlpha(200),
                  ],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Column(
                children: [
                  Text(
                    '오늘 일정 만들기',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: HiBuddyColors.text,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    '오늘 할 일을 입력하면 자동으로 일정표를 만들어 드려요',
                    style: TextStyle(
                      fontSize: 14,
                      color: HiBuddyColors.textMuted,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // ── Section 1: Input ──
            _sectionTitle('1. 일정 내용 입력'),
            const SizedBox(height: 8),
            TextField(
              controller: _textController,
              maxLines: 8,
              decoration: const InputDecoration(
                hintText: '예: 08:00 · 오늘 일정 간단 안내',
                hintStyle: TextStyle(color: HiBuddyColors.textMuted),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isGenerating ? null : _generateSchedule,
                icon: _isGenerating
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.auto_awesome),
                label: Text(_isGenerating ? '일정 만드는 중... (최대 30초)' : '일정 자동 만들기'),
              ),
            ),

            if (_schedule.isNotEmpty) ...[
              const SizedBox(height: 24),
              const Divider(),

              // ── Section 2: Schedule Preview ──
              Row(
                children: [
                  Expanded(child: _sectionTitle('2. 자동으로 만들어진 일정')),
                  IconButton(
                    onPressed: _addNewItem,
                    icon: const Icon(Icons.add_circle, size: 32),
                    color: HiBuddyColors.primary,
                    tooltip: '일정 항목 추가',
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ..._schedule.asMap().entries.map((e) {
                final idx = e.key;
                final item = e.value;
                return Dismissible(
                  key: ValueKey('${item.time}_${item.task}_$idx'),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    decoration: BoxDecoration(
                      color: HiBuddyColors.danger,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  confirmDismiss: (_) async {
                    _deleteItem(idx);
                    return false; // We already removed it via setState
                  },
                  child: ActivityCard(
                    type: item.type,
                    task: item.task,
                    time: item.time,
                    onTap: () => _editItem(idx),
                  ),
                );
              }),

              const SizedBox(height: 16),

              // ── Section 3: Guide scripts (expandable) ──
              _sectionTitle('3. 활동 자세히 설정하기'),
              const SizedBox(height: 8),
              ..._schedule.asMap().entries.map((e) {
                final idx = e.key;
                final item = e.value;
                final isExpanded = _expandedIndex == idx;
                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  child: Column(
                    children: [
                      ListTile(
                        leading: Text(
                          HiBuddyColors.getActivityEmoji(item.type),
                          style: const TextStyle(fontSize: 24),
                        ),
                        title: Text(
                          '[${item.time}] ${HiBuddyColors.getActivityLabel(item.type)} · ${item.task}',
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                        trailing: Icon(
                          isExpanded ? Icons.expand_less : Icons.expand_more,
                        ),
                        onTap: () {
                          setState(() {
                            _expandedIndex = isExpanded ? null : idx;
                          });
                        },
                      ),
                      if (isExpanded)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '안내 문장:',
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: HiBuddyColors.textMuted,
                                ),
                              ),
                              const SizedBox(height: 8),
                              ...item.guideScript.asMap().entries.map((gs) {
                                return Padding(
                                  padding: const EdgeInsets.only(bottom: 4),
                                  child: Row(
                                    children: [
                                      CircleAvatar(
                                        radius: 12,
                                        backgroundColor:
                                            HiBuddyColors.getActivityColor(
                                                item.type),
                                        child: Text(
                                          '${gs.key + 1}',
                                          style: const TextStyle(
                                            fontSize: 11,
                                            color: Colors.white,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          gs.value,
                                          style: const TextStyle(fontSize: 14),
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              }),
                              const SizedBox(height: 8),
                              OutlinedButton.icon(
                                onPressed: () => _editItem(idx),
                                icon: const Icon(Icons.edit, size: 16),
                                label: const Text('수정하기'),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                );
              }),

              const SizedBox(height: 24),
              const Divider(),

              // ── Section 4: Save ──
              _sectionTitle('4. 오늘 일정 저장하기'),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isSaving ? null : _saveSchedule,
                  icon: _isSaving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.save),
                  label: Text(_isSaving ? '저장 중...' : '일정 저장하기'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: HiBuddyColors.success,
                    padding: const EdgeInsets.symmetric(vertical: 18),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _copyToTomorrow,
                  icon: const Icon(Icons.copy),
                  label: const Text('내일도 같은 일정 사용'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
              const SizedBox(height: 40),
            ],
          ],
        ),
      ),
    );
  }

  void _showErrorDialog(String title, String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        title: Row(
          children: [
            const Icon(Icons.error_outline, color: HiBuddyColors.danger, size: 28),
            const SizedBox(width: 8),
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          ],
        ),
        content: Text(
          message,
          style: const TextStyle(fontSize: 16, height: 1.6),
        ),
        actions: [
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(ctx),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              child: const Text('알겠어요', style: TextStyle(fontSize: 16)),
            ),
          ),
        ],
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
}

// ── Edit Item Bottom Sheet ──
class _EditItemSheet extends StatefulWidget {
  final ScheduleItem item;
  final ValueChanged<ScheduleItem> onSave;

  const _EditItemSheet({required this.item, required this.onSave});

  @override
  State<_EditItemSheet> createState() => _EditItemSheetState();
}

class _EditItemSheetState extends State<_EditItemSheet> {
  late TextEditingController _timeCtrl;
  late TextEditingController _taskCtrl;
  late TextEditingController _guideCtrl;
  late TextEditingController _gptRequestCtrl;
  bool _isEditing = false;

  @override
  void initState() {
    super.initState();
    _timeCtrl = TextEditingController(text: widget.item.time);
    _taskCtrl = TextEditingController(text: widget.item.task);
    _guideCtrl = TextEditingController(
      text: widget.item.guideScript.join('\n'),
    );
    _gptRequestCtrl = TextEditingController();
  }

  @override
  void dispose() {
    _timeCtrl.dispose();
    _taskCtrl.dispose();
    _guideCtrl.dispose();
    _gptRequestCtrl.dispose();
    super.dispose();
  }

  Future<void> _applyGptEdit() async {
    if (_gptRequestCtrl.text.trim().isEmpty) return;
    setState(() => _isEditing = true);
    try {
      final patch = await ApiService.editScheduleItem(
        {
          'time': _timeCtrl.text,
          'type': widget.item.type,
          'task': _taskCtrl.text,
          'guide_script': _guideCtrl.text.split('\n').where((s) => s.trim().isNotEmpty).toList(),
        },
        _gptRequestCtrl.text,
      );
      if (patch.containsKey('time')) _timeCtrl.text = patch['time'].toString();
      if (patch.containsKey('task')) _taskCtrl.text = patch['task'].toString();
      if (patch.containsKey('guide_script') && patch['guide_script'] is List) {
        _guideCtrl.text = (patch['guide_script'] as List).join('\n');
      }
      setState(() {});
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('수정 오류: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isEditing = false);
    }
  }

  void _save() {
    final guideLines = _guideCtrl.text
        .split('\n')
        .where((s) => s.trim().isNotEmpty)
        .toList();

    final updated = ScheduleItem(
      time: _timeCtrl.text.trim(),
      type: widget.item.type,
      task: _taskCtrl.text.trim(),
      guideScript: guideLines,
      menus: widget.item.menus,
      videoUrl: widget.item.videoUrl,
    );
    widget.onSave(updated);
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: HiBuddyColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              '일정 수정',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                SizedBox(
                  width: 100,
                  child: TextField(
                    controller: _timeCtrl,
                    decoration: const InputDecoration(labelText: '시간(HH:MM)'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _taskCtrl,
                    decoration: const InputDecoration(labelText: '할 일'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _guideCtrl,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: '안내 문장 (한 줄에 하나씩)',
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _gptRequestCtrl,
                    decoration: const InputDecoration(
                      labelText: 'AI로 수정 요청',
                      hintText: '예: 시간을 19:30으로 바꿔줘',
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _isEditing ? null : _applyGptEdit,
                  icon: _isEditing
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.auto_awesome),
                  tooltip: 'AI로 수정',
                ),
              ],
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _save,
                child: const Text('저장'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
