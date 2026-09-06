// 에이전트가 만든 plan을 사용자에게 보여주고 승인/거부 받는 위젯.
// arXiv 2511.22737 + NTT DATA "Agentic AI for Disability" 가이드라인 적용:
//   - 사용자가 plan을 inspect 가능 (이해 가능한 한국어)
//   - 사용자가 언제든 override 가능
//   - 위험 단계는 명확히 표시
//
// 사용:
//   AgentPlanCard(
//     plan: planFromBackend,
//     onApprove: () => sendApproval(planId),
//     onCancel: () => sendCancel(planId),
//   )

import 'package:flutter/material.dart';

class PlanStep {
  final String description;
  final String actionType;
  final bool requiresConfirmation;

  const PlanStep({
    required this.description,
    required this.actionType,
    this.requiresConfirmation = false,
  });

  factory PlanStep.fromJson(Map<String, dynamic> j) => PlanStep(
        description: j['description'] ?? '',
        actionType: j['action_type'] ?? '',
        requiresConfirmation: j['requires_confirmation'] ?? false,
      );
}

class AgentPlan {
  final String agentName;
  final String intent;
  final List<PlanStep> steps;
  final double confidence;
  final String reasoning;

  const AgentPlan({
    required this.agentName,
    required this.intent,
    required this.steps,
    this.confidence = 0.0,
    this.reasoning = '',
  });

  factory AgentPlan.fromJson(Map<String, dynamic> j) => AgentPlan(
        agentName: j['agent_name'] ?? '',
        intent: j['intent'] ?? '',
        steps: ((j['steps'] as List?) ?? [])
            .map((s) => PlanStep.fromJson(s as Map<String, dynamic>))
            .toList(),
        confidence: (j['confidence'] as num?)?.toDouble() ?? 0.0,
        reasoning: j['reasoning'] ?? '',
      );

  bool get hasRiskySteps => steps.any((s) => s.requiresConfirmation);
}

class AgentPlanCard extends StatelessWidget {
  final AgentPlan plan;
  final VoidCallback onApprove;
  final VoidCallback onCancel;
  final bool simpleMode; // 간단/키오스크 모드면 큰 글씨 + 큰 버튼

  const AgentPlanCard({
    super.key,
    required this.plan,
    required this.onApprove,
    required this.onCancel,
    this.simpleMode = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final base = simpleMode ? 22.0 : 16.0;
    final btnH = simpleMode ? 64.0 : 48.0;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                const Icon(Icons.assignment, size: 28),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    plan.intent,
                    style: TextStyle(
                      fontSize: base + 4,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              '이렇게 도울게',
              style: TextStyle(fontSize: base, color: Colors.grey[700]),
            ),
            const SizedBox(height: 8),
            ...plan.steps.asMap().entries.map((entry) {
              final i = entry.key + 1;
              final step = entry.value;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 28, height: 28,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: step.requiresConfirmation
                            ? Colors.orange[100]
                            : theme.primaryColor.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Text(
                        '$i',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: base,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            step.description,
                            style: TextStyle(fontSize: base),
                          ),
                          if (step.requiresConfirmation)
                            Padding(
                              padding: const EdgeInsets.only(top: 2),
                              child: Row(
                                children: [
                                  Icon(Icons.warning_amber_rounded,
                                      size: base, color: Colors.orange[800]),
                                  const SizedBox(width: 4),
                                  Text(
                                    '중요한 단계',
                                    style: TextStyle(
                                      fontSize: base,
                                      color: Colors.orange[800],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: btnH,
                    child: OutlinedButton.icon(
                      onPressed: onCancel,
                      icon: const Icon(Icons.close),
                      label: Text('아니에요',
                          style: TextStyle(fontSize: base)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: btnH,
                    child: FilledButton.icon(
                      onPressed: onApprove,
                      icon: const Icon(Icons.check),
                      label: Text('네 좋아요',
                          style: TextStyle(fontSize: base)),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
