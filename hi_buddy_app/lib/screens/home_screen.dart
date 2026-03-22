import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'coordinator_screen.dart';
import 'user_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
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
                  gradient: const LinearGradient(
                    colors: [HiBuddyColors.primary, HiBuddyColors.primaryLight],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: HiBuddyColors.primary.withAlpha(40),
                      blurRadius: 20,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: const Column(
                  children: [
                    Text('👋', style: TextStyle(fontSize: 40)),
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
                  gradient: const LinearGradient(
                    colors: [
                      HiBuddyColors.primaryBg,
                      Color(0xFFDBEAFE),
                      Color(0xFFFEF3C7),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: HiBuddyColors.primary.withAlpha(25),
                  ),
                ),
                child: const Column(
                  children: [
                    Text('🧩', style: TextStyle(fontSize: 48)),
                    SizedBox(height: 12),
                    Text(
                      '오늘 하루, 같이 해봐요!',
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.w800,
                        color: HiBuddyColors.text,
                        letterSpacing: -1,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      '선생님이 만든 일정을 따라 하루를 보내요',
                      style: TextStyle(
                        fontSize: 15,
                        color: HiBuddyColors.textMuted,
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
                      icon: '📝',
                      iconBgColor: HiBuddyColors.primaryBg,
                      title: '일정 만들기',
                      features: const [
                        '말로 적으면 일정표 자동 생성',
                        '요리 사진/영상 첨부 가능',
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
                      icon: '📺',
                      iconBgColor: const Color(0xFFFEF3C7),
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
                  ];
                  // Use Column on narrow screens to prevent overflow
                  if (constraints.maxWidth < 400) {
                    return Column(
                      children: [
                        cards[0],
                        const SizedBox(height: 12),
                        cards[1],
                      ],
                    );
                  }
                  return Row(
                    children: [
                      Expanded(child: cards[0]),
                      const SizedBox(width: 12),
                      Expanded(child: cards[1]),
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
                        color: HiBuddyColors.primary,
                        width: 3,
                      ),
                    ),
                  ),
                  child: const Text(
                    '사용 방법 안내',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: HiBuddyColors.text,
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
                  color: HiBuddyColors.primaryBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: HiBuddyColors.primary.withAlpha(50),
                  ),
                ),
                child: const Text(
                  'ℹ️ 어렵게 조작할 필요 없습니다. 화면에 나오는 안내를 그대로 따라 하면 됩니다.',
                  style: TextStyle(
                    fontSize: 15,
                    color: HiBuddyColors.text,
                    height: 1.5,
                  ),
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
          border: Border.all(color: HiBuddyColors.border),
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
                color: HiBuddyColors.primary,
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
                  color: HiBuddyColors.text,
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
  final String icon;
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
        border: Border.all(color: HiBuddyColors.border),
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
            child: Text(icon, style: const TextStyle(fontSize: 28)),
          ),
          const SizedBox(height: 12),
          Text(
            title,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: HiBuddyColors.text,
            ),
          ),
          const SizedBox(height: 8),
          ...features.map(
            (f) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '✓ ',
                    style: TextStyle(
                      color: HiBuddyColors.success,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Expanded(
                    child: Text(
                      f,
                      style: const TextStyle(
                        fontSize: 13,
                        color: HiBuddyColors.textMuted,
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
