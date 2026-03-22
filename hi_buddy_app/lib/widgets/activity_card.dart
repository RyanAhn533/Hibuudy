import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ActivityCard extends StatelessWidget {
  final String type;
  final String task;
  final String time;
  final VoidCallback? onTap;
  final bool isActive;

  const ActivityCard({
    super.key,
    required this.type,
    required this.task,
    required this.time,
    this.onTap,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = HiBuddyColors.getActivityColor(type);
    final bgColor = HiBuddyColors.getActivityBgColor(type);
    final emoji = HiBuddyColors.getActivityEmoji(type);
    final label = HiBuddyColors.getActivityLabel(type);

    return Semantics(
      label: '$time $label $task',
      button: onTap != null,
      child: Card(
      elevation: isActive ? 3 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: isActive
            ? BorderSide(color: color, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(16),
            border: Border(left: BorderSide(color: color, width: 5)),
          ),
          child: Row(
            children: [
              // Time badge
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  time,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // Emoji + type label
              Text(emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 8),
              // Task text
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: color.withAlpha(30),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text(
                        label,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: color,
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      task,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: HiBuddyColors.text,
                      ),
                    ),
                  ],
                ),
              ),
              if (onTap != null)
                const Icon(Icons.chevron_right, color: HiBuddyColors.textMuted),
            ],
          ),
        ),
      ),
    ),
    );
  }
}
