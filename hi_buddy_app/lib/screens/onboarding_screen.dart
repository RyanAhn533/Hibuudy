import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/database_service.dart';
import 'home_screen.dart';

/// ══════════════════════════════════════════════════════════
/// OnboardingScreen v1.3 — 3단계로 축소
///
/// Step 1: 환영 + 역할 선택 (합침)
/// Step 2: 이름 + 세그먼트 + 글자 크기 + 도시 (통합)
/// Step 3: 페어링 코드
///
/// 페르소나 투표 결과 반영:
/// - 혜경: "누구의 일상을 도울까요?" 명확
/// - 민호: 위치 권한 거부 → 도시 드롭다운
/// - 강민: 당사자 주체성 존중 언어
/// - 유진: 3단계 축소
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
  String _city = 'Seoul';
  String _pairCode = SessionService.generatePairCode();

  @override
  void dispose() {
    _pc.dispose();
    _nameCtl.dispose();
    super.dispose();
  }

  void _next() {
    if (_step < 2) {
      _pc.nextPage(duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      setState(() => _step++);
    }
  }

  Future<void> _finish() async {
    await SessionService.setRole(_role);
    await SessionService.setSegment(_segment);
    await SessionService.setFontSize(_fontSize);
    await SessionService.setUserName(_nameCtl.text);
    await SessionService.setCity(_city);
    await SessionService.setPairCode(_pairCode);
    await SessionService.completeOnboarding();

    try {
      await DatabaseService.updateProfile({
        'name': _nameCtl.text.trim().isEmpty ? '사용자' : _nameCtl.text.trim()
      });
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
            if (_step > 0) _progressBar(),
            Expanded(
              child: PageView(
                controller: _pc,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (i) => setState(() => _step = i),
                children: [
                  _Step1WelcomeAndRole(
                    role: _role,
                    onChange: (r) => setState(() => _role = r),
                    onNext: _next,
                  ),
                  _Step2Profile(
                    nameCtl: _nameCtl,
                    segment: _segment,
                    fontSize: _fontSize,
                    city: _city,
                    onSegmentChange: (s) => setState(() => _segment = s),
                    onFontChange: (f) => setState(() => _fontSize = f),
                    onCityChange: (c) => setState(() => _city = c),
                    onNext: _next,
                    onWaitlistRequest: _handleWaitlist,
                  ),
                  _Step3Pair(
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
          Text('$_step / 2',
              style: const TextStyle(color: HaruTokens.primary, fontSize: 12, fontWeight: FontWeight.w700)),
          TextButton(
            onPressed: _finish,
            style: TextButton.styleFrom(foregroundColor: HaruTokens.n400),
            child: const Text('건너뛰기', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Future<void> _handleWaitlist(UserSegment s) async {
    final emailCtl = TextEditingController();
    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(HaruTokens.radiusLg)),
        title: Text('${s.label}\n곧 출시돼요', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('준비되면 이메일로 알려드려요.',
                style: TextStyle(fontSize: 13, color: HaruTokens.n700, height: 1.6)),
            const SizedBox(height: 14),
            TextField(
              controller: emailCtl,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(hintText: 'name@example.com'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('나중에')),
          ElevatedButton(
            onPressed: () async {
              final email = emailCtl.text.trim();
              if (email.isEmpty) {
                Navigator.pop(ctx);
                return;
              }
              try {
                await http
                    .post(
                      Uri.parse('https://hibuudy.onrender.com/api/waitlist'),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({'email': email, 'segment': s.name}),
                    )
                    .timeout(const Duration(seconds: 5));
              } catch (_) {}
              if (ctx.mounted) {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(content: Text('알림 요청이 접수됐어요.')),
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
}

// ═══════════════════════════════════════════════════════════
// STEP 1 — Welcome + Role (통합)
// ═══════════════════════════════════════════════════════════
class _Step1WelcomeAndRole extends StatelessWidget {
  final UserRole role;
  final ValueChanged<UserRole> onChange;
  final VoidCallback onNext;
  const _Step1WelcomeAndRole({
    required this.role,
    required this.onChange,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const Spacer(flex: 2),
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: HaruTokens.primary,
              borderRadius: BorderRadius.circular(HaruTokens.radiusXl),
            ),
            child: const Center(
              child: Icon(Symbols.diversity_3, size: 48, color: HaruTokens.white, fill: 1),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            '하루메이트',
            style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 36),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          const Text(
            '하루를 같이 만드는 도우미',
            style: TextStyle(fontSize: 14, color: HaruTokens.n400),
          ),
          const Spacer(flex: 2),
          const Text(
            '누구를 위해 쓰시나요?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: HaruTokens.n900),
          ),
          const SizedBox(height: 16),
          _RoleCard(
            icon: Symbols.supervisor_account,
            title: '가족이나 학생을 위해',
            subtitle: '부모 · 선생님 · 복지사',
            selected: role == UserRole.coordinator,
            onTap: () => onChange(UserRole.coordinator),
          ),
          const SizedBox(height: 10),
          _RoleCard(
            icon: Symbols.person,
            title: '나 자신을 위해',
            subtitle: '본인이 직접 사용',
            selected: role == UserRole.self,
            onTap: () => onChange(UserRole.self),
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(onPressed: onNext, child: const Text('시작할게요')),
          ),
          const SizedBox(height: 10),
          const Text(
            '사용하면서 개인정보 처리방침에 동의해요',
            style: TextStyle(fontSize: 11, color: HaruTokens.n400),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
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
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
            border: Border.all(
              color: selected ? HaruTokens.primary : HaruTokens.n200,
              width: selected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Icon(icon, size: 32, color: selected ? HaruTokens.primary : HaruTokens.n400),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w800, color: HaruTokens.n900)),
                    const SizedBox(height: 2),
                    Text(subtitle,
                        style: const TextStyle(fontSize: 12, color: HaruTokens.n700)),
                  ],
                ),
              ),
              if (selected)
                const Icon(Symbols.check_circle, size: 22, color: HaruTokens.primary, fill: 1),
            ],
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// STEP 2 — 이름 + 세그먼트 + 글자 크기 + 도시 (통합)
// ═══════════════════════════════════════════════════════════
class _Step2Profile extends StatelessWidget {
  final TextEditingController nameCtl;
  final UserSegment segment;
  final FontSizeMode fontSize;
  final String city;
  final ValueChanged<UserSegment> onSegmentChange;
  final ValueChanged<FontSizeMode> onFontChange;
  final ValueChanged<String> onCityChange;
  final VoidCallback onNext;
  final Future<void> Function(UserSegment) onWaitlistRequest;

  const _Step2Profile({
    required this.nameCtl,
    required this.segment,
    required this.fontSize,
    required this.city,
    required this.onSegmentChange,
    required this.onFontChange,
    required this.onCityChange,
    required this.onNext,
    required this.onWaitlistRequest,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 8),
            Text('누구의 일상을\n도와드릴까요?', style: Theme.of(context).textTheme.headlineLarge),
            const SizedBox(height: 6),
            const Text('이름과 기본 설정을 한 번에',
                style: TextStyle(fontSize: 13, color: HaruTokens.n400)),
            const SizedBox(height: 20),

            // 이름
            const Text('이름',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n700)),
            const SizedBox(height: 6),
            TextField(
              controller: nameCtl,
              decoration: const InputDecoration(hintText: '예: 유진'),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),

            const SizedBox(height: 20),

            // 세그먼트
            const Text('어떤 상황인가요?',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n700)),
            const SizedBox(height: 8),
            ...UserSegment.values.map((s) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: _MiniSegmentCard(
                    label: s.label,
                    available: s.isAvailable,
                    selected: segment == s,
                    onTap: () {
                      if (s.isAvailable) {
                        onSegmentChange(s);
                      } else {
                        onWaitlistRequest(s);
                      }
                    },
                  ),
                )),

            const SizedBox(height: 16),

            // 도시
            const Text('사는 지역 (날씨 안내용)',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n700)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: HaruTokens.white,
                borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
                border: Border.all(color: HaruTokens.n200),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: city,
                  isExpanded: true,
                  icon: const Icon(Symbols.expand_more, color: HaruTokens.n400),
                  items: SessionService.supportedCities.entries
                      .map((e) => DropdownMenuItem(
                            value: e.key,
                            child: Text(e.value,
                                style: const TextStyle(
                                    fontSize: 15, fontWeight: FontWeight.w600)),
                          ))
                      .toList(),
                  onChanged: (v) => v != null ? onCityChange(v) : null,
                ),
              ),
            ),

            const SizedBox(height: 16),

            // 글자 크기
            const Text('글자와 버튼 크기',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n700)),
            const SizedBox(height: 8),
            Row(
              children: [
                _SizeChip(
                    label: '보통',
                    selected: fontSize == FontSizeMode.normal,
                    onTap: () => onFontChange(FontSizeMode.normal)),
                const SizedBox(width: 8),
                _SizeChip(
                    label: '크게',
                    selected: fontSize == FontSizeMode.large,
                    onTap: () => onFontChange(FontSizeMode.large)),
                const SizedBox(width: 8),
                _SizeChip(
                    label: '아주 크게',
                    selected: fontSize == FontSizeMode.xlarge,
                    onTap: () => onFontChange(FontSizeMode.xlarge)),
              ],
            ),

            const SizedBox(height: 28),
            ElevatedButton(onPressed: onNext, child: const Text('다음')),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}

class _MiniSegmentCard extends StatelessWidget {
  final String label;
  final bool available;
  final bool selected;
  final VoidCallback onTap;
  const _MiniSegmentCard({
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
    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
            border: Border.all(
              color: !available
                  ? HaruTokens.n200
                  : (selected ? HaruTokens.primary : HaruTokens.n200),
              width: selected && available ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: available ? HaruTokens.n900 : HaruTokens.n400,
                  ),
                ),
              ),
              if (!available)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    color: HaruTokens.accentSoft,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text('준비 중',
                      style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFFA06A10))),
                )
              else if (selected)
                const Icon(Symbols.check_circle, size: 18, color: HaruTokens.primary, fill: 1),
            ],
          ),
        ),
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
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 11),
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
// STEP 3 — 페어 코드
// ═══════════════════════════════════════════════════════════
class _Step3Pair extends StatelessWidget {
  final UserRole role;
  final String code;
  final VoidCallback onFinish;
  final VoidCallback onRegen;
  const _Step3Pair({
    required this.role,
    required this.code,
    required this.onFinish,
    required this.onRegen,
  });

  String _formatted() => code.length >= 6
      ? '${code.substring(0, 3)} ${code.substring(3)}'
      : code;

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
            isCoord ? '코드를 당사자 폰에 입력하면\n일정을 보낼 수 있어요' : '코드로 연결하면\n일정을 같이 만들어요',
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
                const Text('이 6자리 숫자를 상대방에게 말해주세요',
                    style: TextStyle(fontSize: 12, color: HaruTokens.n400)),
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
          OutlinedButton(onPressed: onFinish, child: const Text('나중에 할게요')),
          const SizedBox(height: 12),
          ElevatedButton(onPressed: onFinish, child: const Text('연결됐어요')),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
