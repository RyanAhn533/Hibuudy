import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path_provider/path_provider.dart';
import 'api_service.dart';

class TtsService {
  static final FlutterTts _flutterTts = FlutterTts();
  static bool _initialized = false;

  static Future<void> _init() async {
    if (_initialized) return;
    await _flutterTts.setLanguage('ko-KR');
    await _flutterTts.setSpeechRate(0.45);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);
    _initialized = true;
  }

  /// Speak using device TTS (offline fallback)
  static Future<void> speakLocal(String text) async {
    await _init();
    await _flutterTts.speak(text);
  }

  static Future<void> stop() async {
    await _flutterTts.stop();
  }

  /// Synthesize using OpenAI TTS and return file path
  static Future<String?> synthesizeToFile(String text) async {
    try {
      final bytes = await ApiService.synthesizeTts(text);
      final dir = await getTemporaryDirectory();
      final hash = text.hashCode.toUnsigned(32).toRadixString(16);
      final file = File('${dir.path}/tts_$hash.mp3');
      await file.writeAsBytes(Uint8List.fromList(bytes));
      return file.path;
    } catch (_) {
      return null;
    }
  }

  /// Speak: try OpenAI TTS first, fallback to device TTS
  static Future<void> speak(String text) async {
    // For now use device TTS for simplicity (works offline)
    await speakLocal(text);
  }
}
