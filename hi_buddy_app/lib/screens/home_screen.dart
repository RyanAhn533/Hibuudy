import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/ui_mode_service.dart';
import '../services/session_service.dart';
import '../widgets/sos_button.dart';
import 'coordinator_screen.dart';
import 'user_screen.dart';
import 'agent_screen.dart';
import 'profile_screen.dart';
import 'home_user_screen.dart';
import 'home_coordinator_screen.dart';

/// ══════════════════════════════════════════════════════════
/// HomeScreen — 역할 기반 라우터
/// v3.0: 당사자/코디 분기 추가, 기존 normal/simple/kiosk는 호환 유지
/// ══════════════════════════════════════════════════════════
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  UserRole? _role;

  @override
  void initState() {
    super.initState();
    _loadRole();
  }

  Future<void> _loadRole() async {
    final r = await SessionService.getRole();
    if (!mounted) return;
    setState(() => _role = r);
  }

  @override
  Widget build(BuildContext context) {
    // 키오스크 모드: 홈 건너뛰고 바로 활동 화면
    if (UiModeService.isKiosk) {
      return const UserScreen();
    }

    // 역할 로딩 중
    if (_role == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    // v3.0 역할 기반 분기
    if (_role == UserRole.self) {
      return const HomeUserScreen();
    }

    // 코디네이터 (기본값) → simple 모드면 간단형, 아니면 v3.0 HomeCoordinator
    if (UiModeService.isSimple) {
      return _buildSimpleHome(context);
    }

    return const HomeCoordinatorScreen();
  }

  // ⚠️ DEPRECATED (v2.x 호환 유지 · legacy 4-카드 홈)
  // ignore: unused_element
  Widget _buildLegacyHome(BuildContext context) {
    return _buildNormalHome(context);
  }

  Widget _buildSimpleHome(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              // 상단 인사
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarm,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                ),
                child: Column(
                  children: [
                    const Icon(Symbols.waving_hand, size: 56, color: Colors.white, fill: 1),
                    const SizedBox(height: 12),
                    Text(
                      '하루메이트',
                      style: TextStyle(
                        fontSize: UiModeService.headerSize + 8,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '무엇을 하고 싶어요?',
                      style: TextStyle(
                        fontSize: UiModeService.fontSize,
                        color: Colors.white70,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // 오늘 하루 (큰 버튼)
              Expanded(
                child: GestureDetector(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const UserScreen()),
                  ),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: HaruTokensV2.brandWarmSoft,
                      borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                      border: Border.all(color: HaruTokensV2.brandWarm, width: 3),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Symbols.tv, size: 64, color: HaruTokensV2.brandWarm, fill: 1),
                        const SizedBox(height: 16),
                        Text(
                          '오늘 하루 보기',
                          style: TextStyle(
                            fontSize: UiModeService.headerSize,
                            fontWeight: FontWeight.w800,
                            color: HaruTokensV2.inkPrimary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '지금 할 일을 확인해요',
                          style: TextStyle(
                            fontSize: UiModeService.fontSize,
                            color: HaruTokensV2.inkMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // 도우미 (큰 버튼)
              Expanded(
                child: GestureDetector(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const AgentScreen()),
                  ),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: HiBuddyColors.healthBg,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: HiBuddyColors.health, width: 3),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Symbols.chat_bubble, size: 64, color: HaruTokensV2.brandWarm, fill: 1),
                        const SizedBox(height: 16),
                        Text(
                          '도우미에게 물어보기',
                          style: TextStyle(
                            fontSize: UiModeService.headerSize,
                            fontWeight: FontWeight.w800,
                            color: HaruTokensV2.inkPrimary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '궁금한 것을 물어봐요',
                          style: TextStyle(
                            fontSize: UiModeService.fontSize,
                            color: HaruTokensV2.inkMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: SosButton.floatingButton(context),
    );
  }

  Widget _buildNormalHome(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              // ── Topbar ──
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarm,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                  boxShadow: [
                    BoxShadow(
                      color: HaruTokensV2.brandWarm.withAlpha(40),
                      blurRadius: 20,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: const Column(
                  children: [
                    Icon(Symbols.waving_hand, size: 40, color: Colors.white, fill: 1),
                    SizedBox(height: 8),
                    Text(
                      '하루메이트',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                        letterSpacing: -0.5,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      '발달장애인을 위한 하루 도우미',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.white70,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // ── Hero Section ──
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarmSoft,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                  border: Border.all(
                    color: HaruTokensV2.brandWarm.withAlpha(25),
                  ),
                ),
                child: const Column(
                  children: [
                    Icon(Symbols.extension, size: 48, color: HaruTokensV2.brandWarm, fill: 1),
                    SizedBox(height: 12),
                    Text(
                      '오늘 하루, 같이 해봐요!',
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.w800,
                        color: HaruTokensV2.inkPrimary,
                        letterSpacing: -1,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      '선생님이 만든 일정을 따라 하루를 보내요',
                      style: TextStyle(
                        fontSize: 15,
                        color: HaruTokensV2.inkMuted,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // ── Feature Cards ──
              LayoutBuilder(
                builder: (context, constraints) {
                  final cards = [
                    _FeatureCard(
                      icon: Symbols.edit_note,
                      iconBgColor: HaruTokensV2.brandWarmSoft,
                      title: '일정 만들기',
                      features: const [
                        '말로 적으면 일정표 자동 생성',
                        '활동별 안내 문장 자동 작성',
                        '저장하면 바로 사용 가능',
                      ],
                      buttonLabel: '일정 만들기 (선생님용)',
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const CoordinatorScreen(),
                        ),
                      ),
                    ),
                    _FeatureCard(
                      icon: Symbols.today,
                      iconBgColor: HaruTokensV2.actRestSoft,
                      title: '오늘 하루',
                      features: const [
                        '하루 종일 켜두는 안내 화면',
                        '지금 할 일 한 개만 크게',
                        '단계별 음성 안내 제공',
                      ],
                      buttonLabel: '오늘 하루 보기',
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const UserScreen(),
                        ),
                      ),
                    ),
                    _FeatureCard(
                      icon: Symbols.chat_bubble,
                      iconBgColor: HiBuddyColors.healthBg,
                      title: '도우미',
                      features: const [
                        '궁금한 것 뭐든 물어보기',
                        '요리, 운동, 영상 추천',
                        '음성으로 답변 들을 수 있어요',
                      ],
                      buttonLabel: '도우미에게 물어보기',
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const AgentScreen(),
                        ),
                      ),
                    ),
                    _FeatureCard(
                      icon: Symbols.settings,
                      iconBgColor: HiBuddyColors.clothingBg,
                      title: '나의 정보',
                      features: const [
                        '이름, 장애 수준 설정',
                        '냉장고 재료, 약 알림 관리',
                        '긴급 연락처 등록',
                      ],
                      buttonLabel: '나의 정보 관리',
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const ProfileScreen(),
                        ),
                      ),
                    ),
                  ];
                  // Use Column on narrow screens to prevent overflow
                  if (constraints.maxWidth < 400) {
                    return Column(
                      children: cards
                          .expand((card) => [card, const SizedBox(height: 12)])
                          .toList()
                        ..removeLast(),
                    );
                  }
                  return Column(
                    children: [
                      Row(
                        children: [
                          Expanded(child: cards[0]),
                          const SizedBox(width: 12),
                          Expanded(child: cards[1]),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(child: cards[2]),
                          const SizedBox(width: 12),
                          Expanded(child: cards[3]),
                        ],
                      ),
                    ],
                  );
                },
              ),

              const SizedBox(height: 28),

              // ── How to Use ──
              Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  padding: const EdgeInsets.only(bottom: 8),
                  decoration: const BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: HaruTokensV2.brandWarm,
                        width: 3,
                      ),
                    ),
                  ),
                  child: const Text(
                    '사용 방법 안내',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: HaruTokensV2.inkPrimary,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ..._buildSteps(),

              const SizedBox(height: 20),

              // ── Info box ──
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarmSoft,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: HaruTokensV2.brandWarm.withAlpha(50),
                  ),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Symbols.info, size: 20, color: HaruTokensV2.brandWarm),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '어렵게 조작할 필요 없습니다. 화면에 나오는 안내를 그대로 따라 하면 됩니다.',
                        style: TextStyle(
                          fontSize: 15,
                          color: HaruTokensV2.inkPrimary,
                          height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildSteps() {
    const steps = [
      '선생님이 "일정 만들기"로 들어가서 오늘 일정을 입력하고 저장합니다',
      '그 다음 "오늘 하루 보기"를 열어, 하루 동안 화면을 켜두면 됩니다',
      '화면에는 지금 해야 할 것만 크게 나오고, 다음 할 일은 작게 표시됩니다',
    ];

    return steps.asMap().entries.map((e) {
      return Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: HaruTokensV2.borderSoft),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withAlpha(10),
              blurRadius: 2,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: HaruTokensV2.brandWarm,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text(
                '${e.key + 1}',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                e.value,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.6,
                  color: HaruTokensV2.inkPrimary,
                ),
              ),
            ),
          ],
        ),
      );
    }).toList();
  }
}

class _FeatureCard extends StatelessWidget {
  final IconData icon;
  final Color iconBgColor;
  final String title;
  final List<String> features;
  final String buttonLabel;
  final VoidCallback onPressed;

  const _FeatureCard({
    required this.icon,
    required this.iconBgColor,
    required this.title,
    required this.features,
    required this.buttonLabel,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: HaruTokensV2.borderSoft),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(10),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: iconBgColor,
              borderRadius: BorderRadius.circular(16),
            ),
            alignment: Alignment.center,
            child: Icon(icon, size: 28, color: HaruTokensV2.brandWarm, fill: 1),
          ),
          const SizedBox(height: 12),
          Text(
            title,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: HaruTokensV2.inkPrimary,
            ),
          ),
          const SizedBox(height: 8),
          ...features.map(
            (f) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Padding(
                    padding: EdgeInsets.only(top: 2, right: 4),
                    child: Icon(Symbols.check, size: 14, color: HaruTokensV2.success),
                  ),
                  Expanded(
                    child: Text(
                      f,
                      style: const TextStyle(
                        fontSize: 13,
                        color: HaruTokensV2.inkMuted,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: onPressed,
              child: Text(
                buttonLabel,
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
