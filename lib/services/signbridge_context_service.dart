import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class SignBridgeContextService {
  SignBridgeContextService._();

  // Keep this IP synchronized with chatbot_page.dart.
  static const String apiBaseUrl = 'http://192.168.0.118:5000';

  static const String _lastSoundKey = 'signbridge_context_last_sound';
  static const String _lastSignKey = 'signbridge_context_last_sign';
  static const String _lastSpeechKey = 'signbridge_context_last_speech';

  static const Map<int, String> _stageNames = {
    0: 'Learn new signs',
    1: 'Guess the signs',
    2: 'Challenge',
    3: 'Final test',
    4: 'Completed',
  };

  static Future<void> saveRecentSpeech(String text) async {
    final String clean = text.trim();
    if (clean.isEmpty) return;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_lastSpeechKey, clean);

    unawaited(
      _postEvent(
        'speech',
        {
          'text': clean,
          'saved_at': DateTime.now().toIso8601String(),
        },
      ),
    );
  }

  static Future<void> saveLastSound({
    required String label,
    double? confidence,
    String? severity,
    bool? reliable,
  }) async {
    final String cleanLabel = label.trim();
    if (cleanLabel.isEmpty) return;

    final Map<String, dynamic> payload = {
      'label': cleanLabel,
      if (confidence != null) 'confidence': confidence,
      if (severity != null && severity.trim().isNotEmpty)
        'severity': severity.trim(),
      if (reliable != null) 'reliable': reliable,
      'saved_at': DateTime.now().toIso8601String(),
    };

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _lastSoundKey,
      jsonEncode(payload),
    );

    // Best effort only. Voice Assist must never wait for the chatbot server.
    unawaited(_postEvent('sound', payload));
  }

  static Future<void> saveLastSign({
    required String text,
    double? confidence,
  }) async {
    final String clean = text.trim();
    if (clean.isEmpty) return;

    final Map<String, dynamic> payload = {
      'text': clean,
      if (confidence != null) 'confidence': confidence,
      'saved_at': DateTime.now().toIso8601String(),
    };

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _lastSignKey,
      jsonEncode(payload),
    );

    unawaited(_postEvent('sign', payload));
  }

  static Future<Map<String, dynamic>> buildAppContext({
    String? recentSpeech,
  }) async {
    final prefs = await SharedPreferences.getInstance();

    final String speech =
        (recentSpeech ?? '').trim().isNotEmpty
            ? recentSpeech!.trim()
            : (prefs.getString(_lastSpeechKey) ?? '').trim();

    final dynamic lastSound = _decodeStoredJson(
      prefs.getString(_lastSoundKey),
    );

    final dynamic lastSign = _decodeStoredJson(
      prefs.getString(_lastSignKey),
    );

    final Map<String, dynamic> education =
        _collectEducationContext(prefs);

    return {
      'recent_speech': speech,
      'recent_sound': lastSound ?? '',
      'recent_signs': lastSign ?? '',
      'education': education,
    };
  }

  static Map<String, dynamic> _collectEducationContext(
    SharedPreferences prefs,
  ) {
    final List<Map<String, dynamic>> levels = [];

    // The current SignBridge Education flow uses edu_l<level>_* keys.
    // Scan generously so future levels are also visible to the chatbot.
    for (int level = 1; level <= 10; level++) {
      final String prefix = 'edu_l$level';

      final bool hasAnyData =
          prefs.containsKey('${prefix}_stage') ||
              prefs.containsKey('${prefix}_learn_index') ||
              prefs.containsKey('${prefix}_guess_index') ||
              prefs.containsKey('${prefix}_challenge_index') ||
              prefs.containsKey('${prefix}_final_index') ||
              prefs.containsKey('${prefix}_best_score') ||
              prefs.containsKey('${prefix}_completed_once') ||
              prefs.containsKey('${prefix}_unlocked') ||
              prefs.containsKey('l${level}_stage') ||
              prefs.containsKey('l${level}_best_score') ||
              prefs.containsKey('l${level}_completed_once') ||
              prefs.containsKey('l${level}_unlocked');

      // Level 1 is the default first level even before explicit progress exists.
      if (!hasAnyData && level != 1) {
        continue;
      }

      final int stage = (
        prefs.getInt('${prefix}_stage') ??
            prefs.getInt('l${level}_stage') ??
            0
      ).clamp(0, 4);

      final bool completed =
          prefs.getBool('${prefix}_completed_once') ??
              prefs.getBool('l${level}_completed_once') ??
              stage >= 4;

      final bool unlocked = level == 1
          ? true
          : (prefs.getBool('${prefix}_unlocked') ??
              prefs.getBool('l${level}_unlocked') ??
              false);

      levels.add({
        'level': level,
        'stage': stage,
        'stage_name': _stageNames[stage] ?? 'Stage $stage',
        'learn_index': prefs.getInt('${prefix}_learn_index') ?? 0,
        'guess_index': prefs.getInt('${prefix}_guess_index') ?? 0,
        'challenge_index': prefs.getInt('${prefix}_challenge_index') ?? 0,
        'final_index': prefs.getInt('${prefix}_final_index') ?? 0,
        'best_score': prefs.getInt('${prefix}_best_score') ??
            prefs.getInt('l${level}_best_score') ??
            0,
        'completed': completed,
        'unlocked': unlocked,
      });
    }

    Map<String, dynamic>? current;

    for (final Map<String, dynamic> level in levels) {
      if (level['unlocked'] == true && level['completed'] != true) {
        current = level;
        break;
      }
    }

    current ??= levels.isNotEmpty ? levels.last : null;

    return {
      'current': current,
      'levels': levels,
      'captured_at': DateTime.now().toIso8601String(),
    };
  }

  static dynamic _decodeStoredJson(String? raw) {
    if (raw == null || raw.trim().isEmpty) return null;
    try {
      return jsonDecode(raw);
    } catch (_) {
      return raw;
    }
  }

  static Future<void> _postEvent(
    String type,
    dynamic payload,
  ) async {
    try {
      await http
          .post(
            Uri.parse('$apiBaseUrl/api/chatbot/context/event'),
            headers: const {
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'type': type,
              'payload': payload,
            }),
          )
          .timeout(const Duration(seconds: 3));
    } catch (_) {
      // Context sync is best-effort. Never interrupt a core accessibility feature.
    }
  }
}
