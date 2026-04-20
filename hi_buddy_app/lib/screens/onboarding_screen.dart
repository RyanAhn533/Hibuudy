import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/database_service.dart';
import 'home_screen.dart';

/// ══════════════════════════════════════════════════════════
/// OnboardingScreen — 첫 실행 4-step 플로우
/// Design: Figma UR4JMkCsmhZgNmtvznzvv3
/// 유진 피드백 반영:
///   - "누구를 위해 쓰시나요?" (역할 자기규정 회피)
///   - 6자리 페어링 코드
///   - 글자 크기 3단 선택
/// ══════════════════════════════════════════════════════════
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pc = PageController();
  int _step = 0;

  UserRole _role = UserRole.coordinator;
  UserSegment _segment = UserSegment.dd;
  final _nameCtl = TextEditingController();
  FontSizeMode _fontSize = FontSizeMode.large;
  String _pairCode = SessionService.generatePairCode();

  @override
  void dispose() {
    _pc.dispose();
    _nameCtl.dispose();
    super.dispose();
  }

  void _next() {
    if (_step < 4) {
      _pc.nextPage(duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      setState(() => _step++);
    }
  }

  Future<void> _finish() async {
    await SessionService.setRole(_role);
    await SessionService.setSegment(_segment);
    await SessionService.setFontSize(_fontSize);
    await SessionService.setUserName(_nameCtl.text);
    await SessionService.setPairCode(_pairCode);
    await SessionService.completeOnboarding();

    // DB에도 이름 반영
    try {
      await DatabaseService.updateProfile({'name': _nameCtl.text.trim().isEmpty ? '사용자' : _nameCtl.text.trim()});
    } catch (_) {}

    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: HaruTokens.n50,
      body: SafeArea(
        child: Column(
          children: [
            // Progress indicator
            if (_step > 0) _progressBar(),
            Expanded(
              child: PageView(
                controller: _pc,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (i) => setState(() => _step = i),
                children: [
                  _StepWelcome(onStart: _next),
                  _StepRole(role: _role, onChange: (r) => setState(() => _role = r), onNext: _next),
                  _StepSegment(
                    segment: _segment,
                    onChange: (s) => setState(() => _segment = s),
                    onNext: _next,
                  ),
                  _StepProfile(
                    nameCtl: _nameCtl,
                    fontSize: _fontSize,
                    onFontChange: (f) => setState(() => _fontSize = f),
                    onNext: _next,
                  ),
                  _StepPair(
                    role: _role,
                    code: _pairCode,
                    onFinish: _finish,
                    onRegen: () => setState(() => _pairCode = SessionService.generatePairCode()),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _progressBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text('$_step / 4', style: const TextStyle(color: HaruTokens.primary, fontSize: 12, fontWeight: FontWeight.w700)),
          TextButton(
            onPressed: _finish,
            style: TextButton.styleFrom(foregroundColor: HaruTokens.n400),
            child: const Text('건너뛰기', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// STEP 1: Welcome
// ═══════════════════════════════════════════════════════════
class _StepWelcome extends StatelessWidget {
  final VoidCallback onStart;
  const _StepWelcome({required this.onStart});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const Spacer(flex: 2),
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: HaruTokens.primary,
              borderRadius: BorderRadius.circular(HaruTokens.radiusXl),
            ),
            child: const Center(
              child: Icon(Symbols.diversity_3, size: 56, color: HaruTokens.white, fill: 1),
            ),
          ),
          const SizedBox(height: 32),
          Text(
            '하루메이트',
            style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 40),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          const Text(
            '하루를 같이 만드는 도우미',
            style: TextStyle(fontSize: 15, color: HaruTokens.n400),
          ),
          const Spacer(flex: 3),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: onStart,
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(double.infinity, HaruTokens.largeTouchTarget * 0.75),
                textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
              ),
              child: const Text('시작할게요'),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            '사용하면서 개인정보 처리방침에 동의해요',
            style: TextStyle(fontSize: 11, color: HaruTokens.n400),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// STEP 2: Role Selection
// ═══════════════════════════════════════════════════════════
class _StepRole extends StatelessWidget {
  final UserRole role;
  final ValueChanged<UserRole> onChange;
  final VoidCallback onNext;
  const _StepRole({required this.role, required this.onChange, required this.onNext});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 20),
          Text('누구를 위해\n쓰시나요?', style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(height: 6),
          const Text(
            '선택에 맞게 화면이 준비돼요',
            style: TextStyle(fontSize: 13, color: HaruTokens.n400),
          ),
          const SizedBox(height: 28),
          _RoleCard(
            icon: Symbols.supervisor_account,
            title: '가족이나 학생을 위해',
            subtitle: '부모 · 선생님 · 복지사',
            selected: role == UserRole.coordinator,
            onTap: () => onChange(UserRole.coordinator),
          ),
          const SizedBox(height: 12),
          _RoleCard(
            icon: Symbols.person,
            title: '나 자신을 위해',
            subtitle: '본인이 직접 사용해요',
            selected: role == UserRole.self,
            onTap: () => onChange(UserRole.self),
          ),
          const Spacer(),
          ElevatedButton(onPressed: onNext, child: const Text('다음')),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

class _RoleCard extends StatelessWidget {
  final IconData icon;
  final String title, subtitle;
  final bool selected;
  final VoidCallback onTap;
  const _RoleCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? HaruTokens.primarySoft : HaruTokens.white,
      borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
            border: Border.all(
              color: selected ? HaruTokens.primary : HaruTokens.n200,
              width: selected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Icon(icon, size: 36, color: selected ? HaruTokens.primary : HaruTokens.n400),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: HaruTokens.n900)),
                    const SizedBox(height: 4),
                    Text(subtitle, style: const TextStyle(fontSize: 12, color: HaruTokens.n700)),
                  ],
                ),
              ),
              if (selected)
                const Icon(Symbols.check_circle, size: 24, color: HaruTokens.primary, fill: 1),
            ],
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// STEP 2.5: Segment Selection (발달장애/노인/치매/청소년)
// ═══════════════════════════════════════════════════════════
class _StepSegment extends StatelessWidget {
  final UserSegment segment;
  final ValueChanged<UserSegment> onChange;
  final VoidCallback onNext;
  const _StepSegment({required this.segment, required this.onChange, required this.onNext});

  Future<void> _showWaitlist(BuildContext context, UserSegment s) async {
    final emailCtl = TextEditingController();
    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(HaruTokens.radiusLg)),
        title: Text('${s.label}\n곧 출시될 예정이에요', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '준비되면 이메일로 알려드려요.\n(선택 사항이에요)',
              style: TextStyle(fontSize: 13, color: HaruTokens.n700, height: 1.6),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: emailCtl,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(hintText: 'name@example.com'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('나중에'),
          ),
          ElevatedButton(
            onPressed: () async {
              final email = emailCtl.text.trim();
              if (email.isEmpty) {
                Navigator.pop(ctx);
                return;
              }
              // Fire-and-forget 전송 (실패해도 UX 방해 X)
              try {
                await http.post(
                  Uri.parse('https://hibuudy.onrender.com/api/waitlist'),
                  headers: {'Content-Type': 'application/json'},
                  body: jsonEncode({'email': email, 'segment': s.name}),
                ).timeout(const Duration(seconds: 5));
              } catch (_) {}
              if (ctx.mounted) {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(content: Text('알림 요청이 접수됐어요. 고마워요!')),
                );
                Navigator.pop(ctx);
              }
            },
            child: const Text('알림 받기'),
          ),
        ],
      ),
    );
  }

  IconData _iconFor(UserSegment s) {
    switch (s) {
      case UserSegment.dd: return Symbols.diversity_3;
      case UserSegment.senior: return Symbols.elderly;
      case UserSegment.dementia: return Symbols.psychology;
      case UserSegment.youth: return Symbols.school;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 12),
          Text('어떤 분이\n쓰실 거예요?', style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(height: 6),
          const Text(
            '맞춤 기능을 준비해 드려요',
            style: TextStyle(fontSize: 13, color: HaruTokens.n400),
          ),
          const SizedBox(height: 20),
          ...UserSegment.values.map((s) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _SegmentCard(
                  icon: _iconFor(s),
                  label: s.label,
                  available: s.isAvailable,
                  selected: segment == s,
                  onTap: () {
                    if (s.isAvailable) {
                      onChange(s);
                    } else {
                      _showWaitlist(context, s);
                    }
                  },
                ),
              )),
          const Spacer(),
          ElevatedButton(onPressed: onNext, child: const Text('다음')),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

class _SegmentCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool available;
  final bool selected;
  final VoidCallback onTap;
  const _SegmentCard({
    required this.icon,
    required this.label,
    required this.available,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bg = !available
        ? HaruTokens.n100
        : (selected ? HaruTokens.primarySoft : HaruTokens.white);
    final borderColor = !available
        ? HaruTokens.n200
        : (selected ? HaruTokens.primary : HaruTokens.n200);
    final iconColor = !available
        ? HaruTokens.n400
        : (selected ? HaruTokens.primary : HaruTokens.n400);
    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
            border: Border.all(color: borderColor, width: selected && available ? 2 : 1),
          ),
          child: Row(
            children: [
              Icon(icon, size: 32, color: iconColor, fill: available ? 1 : 0),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: available ? HaruTokens.n900 : HaruTokens.n400,
                  ),
                ),
              ),
              if (!available)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: HaruTokens.accentSoft,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text(
                    '준비 중',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Color(0xFFA06A10)),
                  ),
                )
              else if (selected)
                const Icon(Symbols.check_circle, size: 22, color: HaruTokens.primary, fill: 1),
            ],
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// STEP 3: Name + Font Size
// ═══════════════════════════════════════════════════════════
class _StepProfile extends StatelessWidget {
  final TextEditingController nameCtl;
  final FontSizeMode fontSize;
  final ValueChanged<FontSizeMode> onFontChange;
  final VoidCallback onNext;
  const _StepProfile({
    required this.nameCtl,
    required this.fontSize,
    required this.onFontChange,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 20),
          Text('이름을\n알려주세요', style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(height: 6),
          const Text(
            '도우미가 이름으로 불러드려요',
            style: TextStyle(fontSize: 13, color: HaruTokens.n400),
          ),
          const SizedBox(height: 28),
          const Text('이름', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n700)),
          const SizedBox(height: 8),
          TextField(
            controller: nameCtl,
            decoration: const InputDecoration(hintText: '예: 유진'),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 28),
          const Text('글자와 버튼 크기', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n700)),
          const SizedBox(height: 10),
          Row(
            children: [
              _SizeChip(label: '보통', selected: fontSize == FontSizeMode.normal, onTap: () => onFontChange(FontSizeMode.normal)),
              const SizedBox(width: 8),
              _SizeChip(label: '크게', selected: fontSize == FontSizeMode.large, onTap: () => onFontChange(FontSizeMode.large)),
              const SizedBox(width: 8),
              _SizeChip(label: '아주 크게', selected: fontSize == FontSizeMode.xlarge, onTap: () => onFontChange(FontSizeMode.xlarge)),
            ],
          ),
          const Spacer(),
          ElevatedButton(onPressed: onNext, child: const Text('다음')),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

class _SizeChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _SizeChip({required this.label, required this.selected, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: selected ? HaruTokens.primary : HaruTokens.n100,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: selected ? HaruTokens.white : HaruTokens.n700,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// STEP 4: Pair Code
// ═══════════════════════════════════════════════════════════
class _StepPair extends StatelessWidget {
  final UserRole role;
  final String code;
  final VoidCallback onFinish;
  final VoidCallback onRegen;
  const _StepPair({
    required this.role,
    required this.code,
    required this.onFinish,
    required this.onRegen,
  });

  String _formatted() {
    // "842163" → "842 163"
    if (code.length < 6) return code;
    return '${code.substring(0, 3)} ${code.substring(3)}';
  }

  @override
  Widget build(BuildContext context) {
    final isCoord = role == UserRole.coordinator;
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 20),
          Text(
            isCoord ? '당사자 폰과\n연결할까요?' : '돕는 사람과\n연결할까요?',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const SizedBox(height: 6),
          Text(
            isCoord
                ? '코드를 당사자 폰에 입력하면\n일정을 보낼 수 있어요'
                : '코드로 연결하면\n일정을 같이 만들어요',
            style: const TextStyle(fontSize: 13, color: HaruTokens.n400, height: 1.6),
          ),
          const SizedBox(height: 28),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
            decoration: BoxDecoration(
              color: HaruTokens.white,
              borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
              border: Border.all(color: HaruTokens.n200),
            ),
            child: Column(
              children: [
                Text(
                  _formatted(),
                  style: const TextStyle(
                    fontSize: 40,
                    fontWeight: FontWeight.w800,
                    color: HaruTokens.primary,
                    letterSpacing: 8,
                    fontFeatures: [FontFeature.tabularFigures()],
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  '이 6자리 숫자를 상대방에게 말해주세요',
                  style: TextStyle(fontSize: 12, color: HaruTokens.n400),
                ),
                const SizedBox(height: 16),
                TextButton.icon(
                  onPressed: onRegen,
                  icon: const Icon(Symbols.refresh, size: 18),
                  label: const Text('새 코드', style: TextStyle(fontSize: 13)),
                ),
              ],
            ),
          ),
          const Spacer(),
          OutlinedButton(
            onPressed: onFinish,
            child: const Text('나중에 할게요'),
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: onFinish,
            child: const Text('연결됐어요'),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
