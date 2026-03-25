import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/database_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // ── 프로필 ──
  final _nameController = TextEditingController();
  String _disabilityLevel = '경증';
  String _uiMode = '일반';
  double _ttsSpeed = 0.45;

  // ── 식재료 ──
  final _ingredientController = TextEditingController();
  List<Map<String, dynamic>> _ingredients = [];

  // ── 긴급 연락처 ──
  final _contactNameController = TextEditingController();
  final _contactPhoneController = TextEditingController();
  List<Map<String, dynamic>> _contacts = [];

  // ── 약 알림 ──
  final _medicineNameController = TextEditingController();
  TimeOfDay _medicineTime = const TimeOfDay(hour: 9, minute: 0);
  List<Map<String, dynamic>> _medicines = [];

  // ── 수행 기록 ──
  List<Map<String, dynamic>> _completionLogs = [];

  bool _isLoading = true;

  // 장애 수준 매핑 (DB 저장값 <-> 표시값)
  static const _disabilityMap = {
    'mild': '경증',
    'moderate': '중등도',
    'severe': '중증',
    '경증': '경증',
    '중등도': '중등도',
    '중증': '중증',
  };

  static const _disabilityToDb = {
    '경증': 'mild',
    '중등도': 'moderate',
    '중증': 'severe',
  };

  static const _uiModeMap = {
    'normal': '일반',
    'simple': '간단',
    'kiosk': '키오스크',
    '일반': '일반',
    '간단': '간단',
    '키오스크': '키오스크',
  };

  static const _uiModeToDb = {
    '일반': 'normal',
    '간단': 'simple',
    '키오스크': 'kiosk',
  };

  @override
  void initState() {
    super.initState();
    _loadAllData();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _ingredientController.dispose();
    _contactNameController.dispose();
    _contactPhoneController.dispose();
    _medicineNameController.dispose();
    super.dispose();
  }

  Future<void> _loadAllData() async {
    try {
      final profile = await DatabaseService.getProfile();
      final ingredients = await DatabaseService.getIngredients();
      final contacts = await DatabaseService.getEmergencyContacts();
      final medicines = await DatabaseService.getMedicineSchedules();
      final logs = await DatabaseService.getCompletionLogs(limit: 30);

      if (!mounted) return;
      setState(() {
        _nameController.text = profile['name'] as String? ?? '';
        final dbLevel = profile['disability_level'] as String? ?? 'mild';
        _disabilityLevel = _disabilityMap[dbLevel] ?? '경증';
        final dbMode = profile['ui_mode'] as String? ?? 'normal';
        _uiMode = _uiModeMap[dbMode] ?? '일반';
        _ttsSpeed = (profile['tts_speed'] as num?)?.toDouble() ?? 0.45;
        _ingredients = ingredients;
        _contacts = contacts;
        _medicines = medicines;
        _completionLogs = logs;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _saveProfile() async {
    await DatabaseService.updateProfile({
      'name': _nameController.text.trim(),
      'disability_level': _disabilityToDb[_disabilityLevel] ?? 'mild',
      'ui_mode': _uiModeToDb[_uiMode] ?? 'normal',
      'tts_speed': _ttsSpeed,
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('저장되었습니다', style: TextStyle(fontSize: 16)),
          backgroundColor: HiBuddyColors.success,
        ),
      );
    }
  }

  Future<void> _addIngredient() async {
    final name = _ingredientController.text.trim();
    if (name.isEmpty) return;
    await DatabaseService.addIngredient(name);
    _ingredientController.clear();
    final ingredients = await DatabaseService.getIngredients();
    if (mounted) setState(() => _ingredients = ingredients);
  }

  Future<void> _removeIngredient(int id) async {
    await DatabaseService.removeIngredient(id);
    final ingredients = await DatabaseService.getIngredients();
    if (mounted) setState(() => _ingredients = ingredients);
  }

  Future<void> _addContact() async {
    final name = _contactNameController.text.trim();
    final phone = _contactPhoneController.text.trim();
    if (name.isEmpty || phone.isEmpty) return;
    await DatabaseService.addEmergencyContact(name, phone);
    _contactNameController.clear();
    _contactPhoneController.clear();
    final contacts = await DatabaseService.getEmergencyContacts();
    if (mounted) setState(() => _contacts = contacts);
  }

  Future<void> _removeContact(int id) async {
    await DatabaseService.removeEmergencyContact(id);
    final contacts = await DatabaseService.getEmergencyContacts();
    if (mounted) setState(() => _contacts = contacts);
  }

  Future<void> _addMedicine() async {
    final name = _medicineNameController.text.trim();
    if (name.isEmpty) return;
    final timeStr =
        '${_medicineTime.hour.toString().padLeft(2, '0')}:${_medicineTime.minute.toString().padLeft(2, '0')}';
    await DatabaseService.addMedicine(name, timeStr);
    _medicineNameController.clear();
    final medicines = await DatabaseService.getMedicineSchedules();
    if (mounted) setState(() => _medicines = medicines);
  }

  Future<void> _removeMedicine(int id) async {
    await DatabaseService.removeMedicine(id);
    final medicines = await DatabaseService.getMedicineSchedules();
    if (mounted) setState(() => _medicines = medicines);
  }

  Future<void> _pickMedicineTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _medicineTime,
      helpText: '약 먹을 시간',
    );
    if (picked != null) {
      setState(() => _medicineTime = picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('나의 정보')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text(
                '정보를 불러오고 있어요...',
                style: TextStyle(fontSize: 18, color: HiBuddyColors.textMuted),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('나의 정보')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildProfileSection(),
            const SizedBox(height: 24),
            _buildIngredientsSection(),
            const SizedBox(height: 24),
            _buildContactsSection(),
            const SizedBox(height: 24),
            _buildMedicineSection(),
            const SizedBox(height: 24),
            _buildCompletionLogSection(),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  // ── 사용자 정보 섹션 ──
  Widget _buildProfileSection() {
    return _buildSection(
      title: '사용자 정보',
      icon: Icons.person,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 이름
          const Text(
            '이름',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: HiBuddyColors.text,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _nameController,
            style: const TextStyle(fontSize: 18),
            decoration: const InputDecoration(
              hintText: '이름을 입력하세요',
              hintStyle: TextStyle(fontSize: 16),
            ),
          ),

          const SizedBox(height: 16),

          // 장애 수준
          const Text(
            '장애 수준',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: HiBuddyColors.text,
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: DropdownButtonFormField<String>(
              initialValue: _disabilityLevel,
              decoration: const InputDecoration(
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              ),
              style: const TextStyle(fontSize: 18, color: HiBuddyColors.text),
              items: const [
                DropdownMenuItem(value: '경증', child: Text('경증')),
                DropdownMenuItem(value: '중등도', child: Text('중등도')),
                DropdownMenuItem(value: '중증', child: Text('중증')),
              ],
              onChanged: (v) {
                if (v != null) setState(() => _disabilityLevel = v);
              },
            ),
          ),

          const SizedBox(height: 16),

          // UI 모드
          const Text(
            'UI 모드',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: HiBuddyColors.text,
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: DropdownButtonFormField<String>(
              initialValue: _uiMode,
              decoration: const InputDecoration(
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              ),
              style: const TextStyle(fontSize: 18, color: HiBuddyColors.text),
              items: const [
                DropdownMenuItem(value: '일반', child: Text('일반')),
                DropdownMenuItem(value: '간단', child: Text('간단')),
                DropdownMenuItem(value: '키오스크', child: Text('키오스크')),
              ],
              onChanged: (v) {
                if (v != null) setState(() => _uiMode = v);
              },
            ),
          ),

          const SizedBox(height: 16),

          // TTS 속도
          const Text(
            'TTS 속도',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: HiBuddyColors.text,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const Text('느리게', style: TextStyle(fontSize: 14, color: HiBuddyColors.textMuted)),
              Expanded(
                child: Slider(
                  value: _ttsSpeed,
                  min: 0.2,
                  max: 1.0,
                  divisions: 8,
                  label: _ttsSpeed.toStringAsFixed(2),
                  activeColor: HiBuddyColors.primary,
                  onChanged: (v) => setState(() => _ttsSpeed = v),
                ),
              ),
              const Text('빠르게', style: TextStyle(fontSize: 14, color: HiBuddyColors.textMuted)),
            ],
          ),
          Text(
            '현재: ${_ttsSpeed.toStringAsFixed(2)}',
            style: const TextStyle(fontSize: 14, color: HiBuddyColors.textMuted),
          ),

          const SizedBox(height: 16),

          // 저장 버튼
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _saveProfile,
              icon: const Icon(Icons.save, size: 22),
              label: const Text('저장하기', style: TextStyle(fontSize: 18)),
            ),
          ),
        ],
      ),
    );
  }

  // ── 냉장고 (식재료 관리) 섹션 ──
  Widget _buildIngredientsSection() {
    // 카테고리별 그룹핑
    final categories = <String, List<Map<String, dynamic>>>{};
    for (final item in _ingredients) {
      final cat = item['category'] as String? ?? '기타';
      categories.putIfAbsent(cat, () => []).add(item);
    }

    return _buildSection(
      title: '냉장고 (식재료 관리)',
      icon: Icons.kitchen,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 추가 입력
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _ingredientController,
                  style: const TextStyle(fontSize: 17),
                  decoration: const InputDecoration(
                    hintText: '식재료 이름',
                    hintStyle: TextStyle(fontSize: 16),
                  ),
                  onSubmitted: (_) => _addIngredient(),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _addIngredient,
                  child: const Text('추가', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // 카테고리 칩
          if (categories.isNotEmpty)
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: categories.keys.map((cat) {
                return Chip(
                  label: Text(
                    '$cat (${categories[cat]!.length})',
                    style: const TextStyle(fontSize: 14),
                  ),
                  backgroundColor: HiBuddyColors.cookingBg,
                );
              }).toList(),
            ),

          const SizedBox(height: 8),

          // 식재료 목록
          if (_ingredients.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text(
                '등록된 식재료가 없어요',
                style: TextStyle(fontSize: 16, color: HiBuddyColors.textMuted),
              ),
            )
          else
            ..._ingredients.map((item) {
              return Container(
                margin: const EdgeInsets.symmetric(vertical: 3),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: HiBuddyColors.border),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        item['name'] as String,
                        style: const TextStyle(fontSize: 17),
                      ),
                    ),
                    Text(
                      item['category'] as String? ?? '기타',
                      style: const TextStyle(
                        fontSize: 13,
                        color: HiBuddyColors.textMuted,
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 48,
                      height: 48,
                      child: IconButton(
                        onPressed: () => _removeIngredient(item['id'] as int),
                        icon: const Icon(Icons.delete_outline, color: HiBuddyColors.danger),
                        tooltip: '삭제',
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  // ── 긴급 연락처 섹션 ──
  Widget _buildContactsSection() {
    return _buildSection(
      title: '긴급 연락처',
      icon: Icons.phone,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 추가 입력
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _contactNameController,
                  style: const TextStyle(fontSize: 17),
                  decoration: const InputDecoration(
                    hintText: '이름',
                    hintStyle: TextStyle(fontSize: 16),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _contactPhoneController,
                  style: const TextStyle(fontSize: 17),
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    hintText: '전화번호',
                    hintStyle: TextStyle(fontSize: 16),
                  ),
                  onSubmitted: (_) => _addContact(),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _addContact,
                  child: const Text('추가', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          if (_contacts.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text(
                '등록된 연락처가 없어요',
                style: TextStyle(fontSize: 16, color: HiBuddyColors.textMuted),
              ),
            )
          else
            ..._contacts.map((contact) {
              return Container(
                margin: const EdgeInsets.symmetric(vertical: 3),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: HiBuddyColors.border),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.person, color: HiBuddyColors.primary, size: 24),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            contact['name'] as String,
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            contact['phone'] as String,
                            style: const TextStyle(
                              fontSize: 15,
                              color: HiBuddyColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(
                      width: 48,
                      height: 48,
                      child: IconButton(
                        onPressed: () => _removeContact(contact['id'] as int),
                        icon: const Icon(Icons.delete_outline, color: HiBuddyColors.danger),
                        tooltip: '삭제',
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  // ── 약 알림 섹션 ──
  Widget _buildMedicineSection() {
    return _buildSection(
      title: '약 알림',
      icon: Icons.medication,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 추가 입력
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _medicineNameController,
                  style: const TextStyle(fontSize: 17),
                  decoration: const InputDecoration(
                    hintText: '약 이름',
                    hintStyle: TextStyle(fontSize: 16),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 52,
                child: OutlinedButton(
                  onPressed: _pickMedicineTime,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                  ),
                  child: Text(
                    '${_medicineTime.hour.toString().padLeft(2, '0')}:${_medicineTime.minute.toString().padLeft(2, '0')}',
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _addMedicine,
                  child: const Text('추가', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          if (_medicines.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text(
                '등록된 약이 없어요',
                style: TextStyle(fontSize: 16, color: HiBuddyColors.textMuted),
              ),
            )
          else
            ..._medicines.map((med) {
              return Container(
                margin: const EdgeInsets.symmetric(vertical: 3),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: HiBuddyColors.border),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.medication, color: HiBuddyColors.health, size: 24),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            med['name'] as String,
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            med['time'] as String,
                            style: const TextStyle(
                              fontSize: 15,
                              color: HiBuddyColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(
                      width: 48,
                      height: 48,
                      child: IconButton(
                        onPressed: () => _removeMedicine(med['id'] as int),
                        icon: const Icon(Icons.delete_outline, color: HiBuddyColors.danger),
                        tooltip: '삭제',
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  // ── 수행 기록 섹션 ──
  Widget _buildCompletionLogSection() {
    return _buildSection(
      title: '수행 기록',
      icon: Icons.checklist,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_completionLogs.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text(
                '수행 기록이 없어요',
                style: TextStyle(fontSize: 16, color: HiBuddyColors.textMuted),
              ),
            )
          else
            ..._completionLogs.map((log) {
              final completed = (log['completed'] as int?) == 1;
              return Container(
                margin: const EdgeInsets.symmetric(vertical: 3),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: completed ? HiBuddyColors.successBg : Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: completed ? HiBuddyColors.success : HiBuddyColors.border,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      completed ? Icons.check_circle : Icons.cancel_outlined,
                      color: completed ? HiBuddyColors.success : HiBuddyColors.danger,
                      size: 24,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            log['task'] as String? ?? '',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            log['date'] as String? ?? '',
                            style: const TextStyle(
                              fontSize: 14,
                              color: HiBuddyColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  // ── 공통 섹션 레이아웃 ──
  Widget _buildSection({
    required String title,
    required IconData icon,
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: HiBuddyColors.cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: HiBuddyColors.border),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(8),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 섹션 헤더
          Row(
            children: [
              Icon(icon, color: HiBuddyColors.primary, size: 24),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: HiBuddyColors.text,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Divider(color: HiBuddyColors.border),
          const SizedBox(height: 8),
          child,
        ],
      ),
    );
  }
}
