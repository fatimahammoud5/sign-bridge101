import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../models/alert_record.dart';
import '../models/sound_prediction.dart';
import 'ai_service.dart';
import 'flash_alert_service.dart';
import 'local_notification_service.dart';
import 'notification_history_service.dart';

class SoundMonitoringService {
  SoundMonitoringService._();

  static final SoundMonitoringService instance =
      SoundMonitoringService._();

  static const String monitoringPreferenceKey =
      'sound_monitoring_enabled';

  // ============================================================
  // INITIALIZE
  // ============================================================

  static Future<void> initialize() async {
    FlutterForegroundTask.init(
      androidNotificationOptions:
          AndroidNotificationOptions(
        channelId: 'sound_monitoring',
        channelName: 'Sound Monitoring',
        channelDescription:
            'Keeps Voice Assist listening for important environmental sounds.',
        onlyAlertOnce: true,
      ),
      iosNotificationOptions:
          const IOSNotificationOptions(
        showNotification: true,
        playSound: false,
      ),
      foregroundTaskOptions:
          ForegroundTaskOptions(
        eventAction:
            ForegroundTaskEventAction.repeat(
          2000,
        ),
        autoRunOnBoot: false,
        autoRunOnMyPackageReplaced:
            false,
        allowWakeLock: true,
        allowWifiLock: false,
      ),
    );
  }

  // ============================================================
  // IS RUNNING
  // ============================================================

  Future<bool> isRunning() async {
    return FlutterForegroundTask
        .isRunningService;
  }

  // ============================================================
  // START
  // ============================================================

  Future<bool> start() async {
    try {
      final notificationPermission =
          await FlutterForegroundTask
              .checkNotificationPermission();

      if (notificationPermission !=
          NotificationPermission.granted) {
        await FlutterForegroundTask
            .requestNotificationPermission();
      }

      final alreadyRunning =
          await FlutterForegroundTask
              .isRunningService;

      if (alreadyRunning) {
        debugPrint(
          'SOUND MONITORING: service already running.',
        );

        return true;
      }

      final result =
          await FlutterForegroundTask
              .startService(
        serviceId: 707,
        serviceTypes: const [
          ForegroundServiceTypes.microphone,
        ],
        notificationTitle:
            'Voice Assist is active',
        notificationText:
            'AI is monitoring surrounding sounds. Tap Stop to end monitoring.',
        notificationButtons: const [
          NotificationButton(
            id: 'stop_monitoring',
            text: 'Stop',
          ),
        ],
        callback:
            startSoundMonitoringCallback,
      );

      debugPrint(
        'SOUND MONITORING START RESULT: $result',
      );

      await Future<void>.delayed(
        const Duration(
          milliseconds: 500,
        ),
      );

      final running =
          await FlutterForegroundTask
              .isRunningService;

      debugPrint(
        'SOUND MONITORING RUNNING: $running',
      );

      return running;
    } catch (error, stackTrace) {
      debugPrint(
        'SOUND MONITORING START ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      return false;
    }
  }

  // ============================================================
  // STOP
  // ============================================================

  Future<void> stop() async {
    try {
      await FlutterForegroundTask
          .stopService();
    } catch (error) {
      debugPrint(
        'MONITORING STOP ERROR: $error',
      );
    }
  }
}

// ===============================================================
// BACKGROUND ENTRY POINT
// ===============================================================

@pragma('vm:entry-point')
void startSoundMonitoringCallback() {
  FlutterForegroundTask.setTaskHandler(
    SoundMonitoringTaskHandler(),
  );
}

// ===============================================================
// BACKGROUND HANDLER
// ===============================================================

class SoundMonitoringTaskHandler
    extends TaskHandler {
  final AudioRecorder _recorder =
      AudioRecorder();

  final AIService _aiService =
      AIService();

  final NotificationHistoryService
      _historyService =
      NotificationHistoryService.instance;

  // IMPORTANT:
  // Keep this IP identical to chatbot_page.dart.
  static const String
      _signBridgeApiBaseUrl =
      'http://192.168.0.118:5000';

  static const Duration
      _contextSyncTimeout =
      Duration(
    seconds: 3,
  );

  bool _initialized = false;

  bool _busy = false;

  bool _destroyed = false;

  final Map<String, DateTime>
      _lastAlertTimes =
      <String, DateTime>{};

  // ============================================================
  // AUDIO SETTINGS
  // ============================================================

  static const Duration
      recordingDuration =
      Duration(
    milliseconds: 1500,
  );

  // ============================================================
  // ALERT COOLDOWNS
  // ============================================================

  static const Duration
      normalCooldown =
      Duration(
    seconds: 30,
  );

  static const Duration
      warningCooldown =
      Duration(
    seconds: 20,
  );

  static const Duration
      criticalCooldown =
      Duration(
    seconds: 10,
  );

  // ============================================================
  // START BACKGROUND HANDLER
  // ============================================================

  @override
  Future<void> onStart(
    DateTime timestamp,
    TaskStarter starter,
  ) async {
    debugPrint(
      '========================================',
    );

    debugPrint(
      'FAST SOUND MONITORING STARTED',
    );

    debugPrint(
      'Recording duration = '
      '${recordingDuration.inMilliseconds}ms',
    );

    debugPrint(
      '========================================',
    );

    await _initializeAI();

    // Start immediately.
    unawaited(
      _analyzeNextChunk(),
    );
  }

  // ============================================================
  // INITIALIZE YAMNET
  // ============================================================

  Future<void> _initializeAI() async {
    if (_initialized) {
      return;
    }

    try {
      await _aiService.loadModel();

      _initialized = true;

      debugPrint(
        'BACKGROUND PRESENTATION AI READY',
      );
    } catch (error, stackTrace) {
      debugPrint(
        'BACKGROUND PRESENTATION AI ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );
    }
  }

  // ============================================================
  // REPEAT
  // ============================================================

  @override
  void onRepeatEvent(
    DateTime timestamp,
  ) {
    if (_busy ||
        _destroyed) {
      return;
    }

    unawaited(
      _analyzeNextChunk(),
    );
  }

  // ============================================================
  // ANALYZE AUDIO
  // ============================================================

  Future<void> _analyzeNextChunk() async {
    if (_busy ||
        _destroyed) {
      return;
    }

    _busy = true;

    final cycleStopwatch =
        Stopwatch()
          ..start();

    String? recordedPath;

    try {
      // ========================================================
      // 1. AI READY
      // ========================================================

      if (!_aiService.isLoaded) {
        await _initializeAI();
      }

      if (!_aiService.isLoaded) {
        debugPrint(
          'BACKGROUND MONITOR: AI not ready.',
        );

        return;
      }

      // ========================================================
      // 2. STOP OLD RECORDING
      // ========================================================

      if (await _recorder
          .isRecording()) {
        await _recorder.stop();
      }

      // ========================================================
      // 3. TEMP FILE
      // ========================================================

      final directory =
          await getTemporaryDirectory();

      final filePath =
          '${directory.path}'
          '${Platform.pathSeparator}'
          'voice_assist_monitor_'
          '${DateTime.now().millisecondsSinceEpoch}.wav';

      debugPrint(
        'BACKGROUND MONITOR: listening...',
      );

      FlutterForegroundTask
          .sendDataToMain(
        <String, dynamic>{
          'type':
              'monitoring_status',
          'status':
              'listening',
        },
      );

      // ========================================================
      // 4. START RECORDING
      // ========================================================

      await _recorder.start(
        const RecordConfig(
          encoder:
              AudioEncoder.wav,
          sampleRate:
              AIService.sampleRate,
          numChannels:
              1,
          bitRate:
              256000,
        ),
        path:
            filePath,
      );

      debugPrint(
        'BACKGROUND MONITOR: recording started.',
      );

      // ========================================================
      // 5. RECORD FOR 1.5 SEC
      // ========================================================

      await Future<void>.delayed(
        recordingDuration,
      );

      if (_destroyed) {
        if (await _recorder
            .isRecording()) {
          recordedPath =
              await _recorder.stop();
        }

        return;
      }

      // ========================================================
      // 6. STOP RECORDING
      // ========================================================

      recordedPath =
          await _recorder.stop();

      debugPrint(
        'BACKGROUND MONITOR: recording stopped.',
      );

      if (recordedPath ==
          null) {
        debugPrint(
          'BACKGROUND MONITOR: recording path is null.',
        );

        return;
      }

      // ========================================================
      // 7. WAV -> PCM
      // ========================================================

      final samples =
          await _readWavSamples(
        recordedPath,
      );

      debugPrint(
        'BACKGROUND MONITOR: '
        'samples=${samples.length}',
      );

      // ========================================================
      // 8. DELETE TEMP FILE
      // ========================================================

      await _deleteTemporaryFile(
        recordedPath,
      );

      recordedPath = null;

      if (samples.isEmpty) {
        debugPrint(
          'BACKGROUND MONITOR: '
          'audio contains no samples.',
        );

        return;
      }

      // ========================================================
      // 9. ANALYZE
      // ========================================================

      FlutterForegroundTask
          .sendDataToMain(
        <String, dynamic>{
          'type':
              'monitoring_status',
          'status':
              'analyzing',
        },
      );

      final aiStopwatch =
          Stopwatch()
            ..start();

      final SoundPrediction
          prediction =
          _aiService.analyzeAudio(
        samples,
      );

      aiStopwatch.stop();

      // ========================================================
      // 10. LOG
      // ========================================================

      debugPrint(
        '========================================',
      );

      debugPrint(
        'BACKGROUND RESULT: '
        '${prediction.label}',
      );

      debugPrint(
        'BACKGROUND CONFIDENCE: '
        '${(prediction.confidence * 100).toStringAsFixed(1)}%',
      );

      debugPrint(
        'BACKGROUND RELIABLE: '
        '${prediction.isReliable}',
      );

      debugPrint(
        'BACKGROUND SEVERITY: '
        '${prediction.severity.name}',
      );

      debugPrint(
        'BACKGROUND AI TIME: '
        '${aiStopwatch.elapsedMilliseconds}ms',
      );

      debugPrint(
        '========================================',
      );

      // ========================================================
      // 11. SEND RESULT TO VOICE ASSIST UI
      // ========================================================

      FlutterForegroundTask
          .sendDataToMain(
        <String, dynamic>{
          'type':
              'sound_result',
          'label':
              prediction.label,
          'confidence':
              prediction.confidence,
          'severity':
              prediction
                  .severity
                  .name,
          'reliable':
              prediction.isReliable,
          'timestamp':
              prediction
                  .detectedAt
                  .millisecondsSinceEpoch,
        },
      );

      // ========================================================
      // 12. RELIABLE SOUND
      //
      // IMPORTANT:
      // Save the latest sound for SignBridge BEFORE notification
      // cooldown is checked.
      //
      // This means:
      //
      // Bird detected
      //     ↓
      // SignBridge remembers Bird immediately
      //     ↓
      // Notification cooldown is checked separately
      //
      // Therefore the chatbot always receives the newest sound.
      // ========================================================

      if (prediction.isReliable) {
        unawaited(
          _saveReliableSoundForSignBridge(
            prediction,
          ),
        );

        await _processReliableSound(
          prediction,
        );
      } else {
        debugPrint(
          'BACKGROUND MONITOR: '
          'uncertain result -> '
          'not saved as latest SignBridge sound.',
        );
      }
    } catch (
      error,
      stackTrace
    ) {
      debugPrint(
        '========================================',
      );

      debugPrint(
        'BACKGROUND ANALYSIS ERROR: $error',
      );

      debugPrintStack(
        stackTrace:
            stackTrace,
      );

      debugPrint(
        '========================================',
      );

      FlutterForegroundTask
          .sendDataToMain(
        <String, dynamic>{
          'type':
              'monitoring_status',
          'status':
              'error',
          'message':
              error.toString(),
        },
      );
    } finally {
      if (recordedPath !=
          null) {
        await _deleteTemporaryFile(
          recordedPath,
        );
      }

      _busy = false;

      cycleStopwatch.stop();

      debugPrint(
        'BACKGROUND CYCLE TIME: '
        '${cycleStopwatch.elapsedMilliseconds}ms',
      );

      debugPrint(
        'BACKGROUND MONITOR: ready for next cycle.',
      );
    }
  }

  // ============================================================
  // SAVE LATEST SOUND FOR SIGNBRIDGE AI
  // ============================================================

  Future<void>
      _saveReliableSoundForSignBridge(
    SoundPrediction prediction,
  ) async {
    final Map<String, dynamic>
        payload =
        <String, dynamic>{
      'label':
          prediction.label,

      'confidence':
          prediction.confidence,

      'severity':
          prediction
              .severity
              .name,

      'reliable':
          true,

      'detected_at':
          prediction
              .detectedAt
              .toIso8601String(),

      'timestamp':
          prediction
              .detectedAt
              .millisecondsSinceEpoch,
    };

    final Uri uri =
        Uri.parse(
      '$_signBridgeApiBaseUrl'
      '/api/chatbot/context/event',
    );

    final HttpClient client =
        HttpClient()
          ..connectionTimeout =
              _contextSyncTimeout;

    try {
      final HttpClientRequest
          httpRequest =
          await client
              .postUrl(
                uri,
              )
              .timeout(
                _contextSyncTimeout,
              );

      httpRequest
          .headers
          .contentType =
          ContentType.json;

      httpRequest.headers.set(
        HttpHeaders
            .acceptHeader,
        'application/json',
      );

      httpRequest.write(
        jsonEncode(
          <String, dynamic>{
            'type':
                'sound',
            'payload':
                payload,
          },
        ),
      );

      final HttpClientResponse
          response =
          await httpRequest
              .close()
              .timeout(
                _contextSyncTimeout,
              );

      final String responseBody =
          await utf8
              .decodeStream(
                response,
              )
              .timeout(
                _contextSyncTimeout,
              );

      if (response.statusCode >=
              200 &&
          response.statusCode <
              300) {
        debugPrint(
          'SIGNBRIDGE CONTEXT: '
          'latest sound saved = '
          '${prediction.label}',
        );
      } else {
        debugPrint(
          'SIGNBRIDGE CONTEXT ERROR: '
          'HTTP ${response.statusCode} '
          '$responseBody',
        );
      }
    } catch (error) {
      // IMPORTANT:
      // Backend problems must NEVER stop Voice Assist.
      debugPrint(
        'SIGNBRIDGE CONTEXT WARNING: '
        'could not sync latest sound: '
        '$error',
      );
    } finally {
      client.close(
        force:
            true,
      );
    }
  }

  // ============================================================
  // PROCESS RELIABLE SOUND
  // ============================================================

  Future<void>
      _processReliableSound(
    SoundPrediction prediction,
  ) async {
    final normalized =
        prediction.label
            .trim()
            .toLowerCase();

    final previous =
        _lastAlertTimes[
            normalized];

    final Duration cooldown;

    switch (
        prediction.severity) {
      case AlertSeverity.normal:
        cooldown =
            normalCooldown;

        break;

      case AlertSeverity.warning:
        cooldown =
            warningCooldown;

        break;

      case AlertSeverity.critical:
        cooldown =
            criticalCooldown;

        break;
    }

    // ==========================================================
    // COOLDOWN
    // ==========================================================

    if (previous != null) {
      final elapsed =
          DateTime.now()
              .difference(
        previous,
      );

      if (elapsed <
          cooldown) {
        debugPrint(
          'ALERT COOLDOWN: '
          '${prediction.label}',
        );

        return;
      }
    }

    _lastAlertTimes[
        normalized] =
        DateTime.now();

    // ==========================================================
    // CREATE RECORD
    // ==========================================================

    final record =
        AlertRecord(
      id:
          '${prediction.detectedAt.millisecondsSinceEpoch}'
          '_${prediction.label.hashCode}',

      title:
          prediction.label,

      description:
          _descriptionFor(
        prediction,
      ),

      confidence:
          prediction.confidence,

      severity:
          prediction.severity,

      createdAt:
          prediction.detectedAt,
    );

    // ==========================================================
    // HISTORY
    // ==========================================================

    debugPrint(
      'NOTIFICATION HISTORY: '
      'adding ${prediction.label}',
    );

    await _historyService
        .addRecord(
      record,
    );

    // ==========================================================
    // NOTIFICATIONS ENABLED?
    // ==========================================================

    final notificationsEnabled =
        await _historyService
            .notificationsEnabled();

    if (!notificationsEnabled) {
      debugPrint(
        'BACKGROUND MONITOR: '
        'notifications disabled.',
      );

      return;
    }

    // ==========================================================
    // SYSTEM NOTIFICATION
    // ==========================================================

    await LocalNotificationService
        .instance
        .showSoundAlert(
      record,
    );

    // ==========================================================
    // FLASH
    // ==========================================================

    if (prediction.severity !=
        AlertSeverity.normal) {
      unawaited(
        FlashAlertService
            .instance
            .flashForSeverity(
          prediction.severity,
        ),
      );
    }
  }

  // ============================================================
  // DESCRIPTION
  // ============================================================

  String _descriptionFor(
    SoundPrediction prediction,
  ) {
    switch (
        prediction.severity) {
      case AlertSeverity.normal:
        return 'A surrounding sound was detected.';

      case AlertSeverity.warning:
        return 'An important sound was detected nearby. '
            'Check your surroundings.';

      case AlertSeverity.critical:
        return 'A potentially dangerous sound was detected. '
            'Check your surroundings immediately.';
    }
  }

  // ============================================================
  // READ WAV
  // ============================================================

  Future<List<double>>
      _readWavSamples(
    String path,
  ) async {
    final bytes =
        await File(
      path,
    ).readAsBytes();

    if (bytes.length <=
        44) {
      return <double>[];
    }

    final dataOffset =
        _findWavDataOffset(
      bytes,
    );

    if (dataOffset >=
        bytes.length) {
      return <double>[];
    }

    final pcmBytes =
        bytes.sublist(
      dataOffset,
    );

    final byteData =
        ByteData.sublistView(
      Uint8List.fromList(
        pcmBytes,
      ),
    );

    final samples =
        <double>[];

    for (
      int i = 0;
      i + 1 <
          byteData
              .lengthInBytes;
      i += 2
    ) {
      final value =
          byteData.getInt16(
        i,
        Endian.little,
      );

      samples.add(
        value /
            32768.0,
      );
    }

    return samples;
  }

  // ============================================================
  // FIND WAV DATA
  // ============================================================

  int _findWavDataOffset(
    Uint8List bytes,
  ) {
    for (
      int i = 12;
      i + 8 <
          bytes.length;
      i++
    ) {
      if (bytes[i] ==
              0x64 &&
          bytes[i + 1] ==
              0x61 &&
          bytes[i + 2] ==
              0x74 &&
          bytes[i + 3] ==
              0x61) {
        return i + 8;
      }
    }

    return 44;
  }

  // ============================================================
  // RECEIVE DATA
  // ============================================================

  @override
  void onReceiveData(
    Object data,
  ) {
    // Reserved for future commands.
  }

  // ============================================================
  // STOP BUTTON
  // ============================================================

  @override
  void onNotificationButtonPressed(
    String id,
  ) {
    if (id ==
        'stop_monitoring') {
      FlutterForegroundTask
          .stopService();
    }
  }

  // ============================================================
  // NOTIFICATION PRESSED
  // ============================================================

  @override
  void onNotificationPressed() {
    FlutterForegroundTask
        .launchApp(
      '/',
    );
  }

  // ============================================================
  // NOTIFICATION DISMISSED
  // ============================================================

  @override
  void onNotificationDismissed() {}

  // ============================================================
  // DELETE TEMP FILE
  // ============================================================

  Future<void>
      _deleteTemporaryFile(
    String path,
  ) async {
    try {
      final file =
          File(
        path,
      );

      if (await file
          .exists()) {
        await file.delete();

        debugPrint(
          'BACKGROUND MONITOR: '
          'temporary audio deleted.',
        );
      }
    } catch (error) {
      debugPrint(
        'BACKGROUND MONITOR: '
        'could not delete temporary file: '
        '$error',
      );
    }
  }

  // ============================================================
  // DESTROY
  // ============================================================

  @override
  Future<void> onDestroy(
    DateTime timestamp,
    bool isTimeout,
  ) async {
    _destroyed = true;

    debugPrint(
      '========================================',
    );

    debugPrint(
      'BACKGROUND SOUND MONITORING DESTROYED',
    );

    debugPrint(
      '========================================',
    );

    // ==========================================================
    // STOP RECORDER
    // ==========================================================

    try {
      if (await _recorder
          .isRecording()) {
        await _recorder.stop();

        debugPrint(
          'BACKGROUND MONITOR: '
          'recorder stopped.',
        );
      }
    } catch (error) {
      debugPrint(
        'BACKGROUND MONITOR: '
        'error while stopping recorder: '
        '$error',
      );
    }

    // ==========================================================
    // DISPOSE RECORDER
    // ==========================================================

    try {
      await _recorder.dispose();

      debugPrint(
        'BACKGROUND MONITOR: '
        'recorder disposed.',
      );
    } catch (error) {
      debugPrint(
        'BACKGROUND MONITOR: '
        'error while disposing recorder: '
        '$error',
      );
    }

    // ==========================================================
    // DISPOSE AI
    // ==========================================================

    try {
      _aiService.dispose();

      debugPrint(
        'BACKGROUND MONITOR: '
        'AI disposed.',
      );
    } catch (error) {
      debugPrint(
        'BACKGROUND MONITOR: '
        'error while disposing AI: '
        '$error',
      );
    }

    FlutterForegroundTask
        .sendDataToMain(
      <String, dynamic>{
        'type':
            'monitoring_status',
        'status':
            'stopped',
      },
    );
  }
}