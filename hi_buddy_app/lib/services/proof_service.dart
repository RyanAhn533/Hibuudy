import 'dart:io';

import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// ══════════════════════════════════════════════════════════
/// ProofService — 완료 인증 사진 (P0-2)
/// 「보통의 하루」의 사진/NFC 해제 패턴을 "옵션"으로 도입.
/// - 기본 OFF. 코디네이터가 내 정보에서 켠다 (기관 모드에서 권장).
/// - 사진은 기기 안에만 저장 (앱 문서 폴더/proofs). 서버로 나가지 않음.
/// - 인증 실패/취소는 완료를 막지 않는다 (R6: 당사자가 막히는 흐름 금지).
/// ══════════════════════════════════════════════════════════
class ProofService {
  ProofService._();

  static const _kEnabled = 'harumate_proof_photo';
  static bool _cached = false;
  static bool _loaded = false;

  static Future<bool> isEnabled() async {
    if (_loaded) return _cached;
    final prefs = await SharedPreferences.getInstance();
    _cached = prefs.getBool(_kEnabled) ?? false;
    _loaded = true;
    return _cached;
  }

  static Future<void> setEnabled(bool v) async {
    _cached = v;
    _loaded = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kEnabled, v);
  }

  /// 카메라로 1장 촬영 → 앱 문서 폴더에 복사 → 경로 반환. 취소/실패 시 null.
  static Future<String?> capture() async {
    try {
      final picker = ImagePicker();
      final shot = await picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 60,
        maxWidth: 1280,
        preferredCameraDevice: CameraDevice.rear,
      );
      if (shot == null) return null;
      final dir = await getApplicationDocumentsDirectory();
      final proofs = Directory(p.join(dir.path, 'proofs'));
      if (!await proofs.exists()) await proofs.create(recursive: true);
      final ts = DateTime.now().toIso8601String().replaceAll(RegExp(r'[:.]'), '-');
      final dest = p.join(proofs.path, 'proof_$ts.jpg');
      await File(shot.path).copy(dest);
      return dest;
    } catch (_) {
      return null;
    }
  }
}
