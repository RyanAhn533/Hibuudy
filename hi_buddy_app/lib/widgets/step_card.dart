import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/tts_service.dart';

class StepCard extends StatelessWidget {
  final int stepNumber;
  final String text;
  final Color color;

  const StepCard({
    super.key,
    required this.stepNumber,
    required this.text,
    this.color = HiBuddyColors.primary,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: HiBuddyColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: Text(
              '$stepNumber',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w700,
                fontSize: 16,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 17,
                height: 1.5,
                color: HiBuddyColors.text,
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.volume_up, size: 22),
            color: color,
            onPressed: () => TtsService.speak('$stepNumber단계. $text'),
            tooltip: '듣기',
          ),
        ],
      ),
    );
  }
}

class StepsList extends StatelessWidget {
  final String title;
  final List<String> steps;
  final Color color;

  const StepsList({
    super.key,
    required this.title,
    required this.steps,
    this.color = HiBuddyColors.primary,
  });

  @override
  Widget build(BuildContext context) {
    if (steps.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: HiBuddyColors.text,
              ),
            ),
            const Spacer(),
            TextButton.icon(
              onPressed: () {
                final allText = steps
                    .asMap()
                    .entries
                    .map((e) => '${e.key + 1}단계. ${e.value}')
                    .join(' ');
                TtsService.speak('전체 단계를 안내할게요. $allText');
              },
              icon: const Icon(Icons.play_circle_outline, size: 20),
              label: const Text('전체 듣기'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...steps.asMap().entries.map(
              (e) => StepCard(
                stepNumber: e.key + 1,
                text: e.value,
                color: color,
              ),
            ),
      ],
    );
  }
}
