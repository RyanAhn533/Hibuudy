import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/database_service.dart';
import '../services/ui_mode_service.dart';

/// SOS 버튼: 키오스크/간단 모드에서 항상 표시
/// 긴급 연락처 첫 번째로 전화, 없으면 119
class SosButton extends StatelessWidget {
  const SosButton({super.key});

  Future<void> _callEmergency(BuildContext context) async {
    String phoneNumber = '119'; // 기본 응급번호

    try {
      final contacts = await DatabaseService.getEmergencyContacts();
      if (contacts.isNotEmpty) {
        phoneNumber = contacts.first['phone'] as String;
      }
    } catch (_) {
      // DB 오류 시 119로 폴백
    }

    final uri = Uri.parse('tel:$phoneNumber');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '$phoneNumber 으로 전화할 수 없어요',
              style: const TextStyle(fontSize: 18),
            ),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // normal 모드에서는 표시 안 함
    if (UiModeService.isNormal) return const SizedBox.shrink();

    return Positioned(
      bottom: 24,
      right: 24,
      child: SizedBox(
        width: 80,
        height: 80,
        child: FloatingActionButton(
          heroTag: 'sos_button',
          onPressed: () => _callEmergency(context),
          backgroundColor: Colors.red,
          elevation: 8,
          shape: const CircleBorder(),
          child: const Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.phone, color: Colors.white, size: 28),
              SizedBox(height: 2),
              Text(
                '도와주세요',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Scaffold의 floatingActionButton으로 사용할 수 있는 버전
  static Widget? floatingButton(BuildContext context) {
    if (UiModeService.isNormal) return null;

    return SizedBox(
      width: 80,
      height: 80,
      child: FloatingActionButton(
        heroTag: 'sos_fab',
        onPressed: () => _callEmergencyStatic(context),
        backgroundColor: Colors.red,
        elevation: 8,
        shape: const CircleBorder(),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.phone, color: Colors.white, size: 28),
            SizedBox(height: 2),
            Text(
              '도와주세요',
              style: TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Future<void> _callEmergencyStatic(BuildContext context) async {
    String phoneNumber = '119';

    try {
      final contacts = await DatabaseService.getEmergencyContacts();
      if (contacts.isNotEmpty) {
        phoneNumber = contacts.first['phone'] as String;
      }
    } catch (_) {
      // DB 오류 시 119로 폴백
    }

    final uri = Uri.parse('tel:$phoneNumber');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '$phoneNumber 으로 전화할 수 없어요',
              style: const TextStyle(fontSize: 18),
            ),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}
