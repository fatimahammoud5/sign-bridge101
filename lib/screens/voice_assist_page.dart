import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:record/record.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../models/sound_prediction.dart';
import '../services/local_notification_service.dart';
import '../services/notification_history_service.dart';
import '../services/sound_monitoring_service.dart';
import 'notification_history_page.dart';

import 'dart:async';

import '../services/signbridge_context_service.dart';

class VoiceAssistPage extends StatefulWidget {
  const VoiceAssistPage({super.key});

  @override
  State<VoiceAssistPage> createState() =>
      _VoiceAssistPageState();
}

enum VoiceAssistMode {
  idle,
  monitoring,
  speechToText,
  error,
}

class _VoiceAssistPageState extends State<VoiceAssistPage> {
  // ==========================================================
  // COLORS
  // ==========================================================

  static const Color purple =
      Color(0xFF7B2FF7);

  static const Color pink =
      Color(0xFFFF5AA5);

  static const Color orange =
      Color(0xFFFF8C42);

  static const Color darkText =
      Color(0xFF20243A);

  static const Color success =
      Color(0xFF40B97B);

  static const Color danger =
      Color(0xFFE53935);

  static const Color dangerDark =
      Color(0xFFB71C1C);

  // ==========================================================
  // SERVICES
  // ==========================================================

  final AudioRecorder _permissionRecorder =
      AudioRecorder();

  final stt.SpeechToText _speech =
      stt.SpeechToText();

  final NotificationHistoryService _historyService =
      NotificationHistoryService.instance;

  // ==========================================================
  // STATE
  // ==========================================================

  VoiceAssistMode _mode =
      VoiceAssistMode.idle;

  bool _monitoringEnabled = false;

  bool _monitoringChanging = false;

  bool _notificationsEnabled = true;

  int _savedNotificationCount = 0;

  String _displayTitle =
      'Ready';

  String _displaySubtitle =
      'Start Sound Monitoring to continuously analyze your surroundings.';

  String _recognizedSpeech = '';

  // Last reliable AI result.
  String? _lastDetectedSound;

  double? _lastConfidence;

  AlertSeverity? _lastSeverity;

  DateTime? _lastDetectedAt;

  // ==========================================================
  // INIT
  // ==========================================================

  @override
  void initState() {
    super.initState();

    _historyService.historyVersion.addListener(
      _handleHistoryChanged,
    );

    FlutterForegroundTask.addTaskDataCallback(
      _onMonitoringData,
    );

    _initializePage();
  }

  @override
  void dispose() {
    _historyService.historyVersion.removeListener(
      _handleHistoryChanged,
    );

    FlutterForegroundTask.removeTaskDataCallback(
      _onMonitoringData,
    );

    _speech.stop();

    _permissionRecorder.dispose();

    /*
     * IMPORTANT:
     *
     * We intentionally do NOT stop SoundMonitoringService here.
     *
     * This allows environmental sound monitoring to continue
     * when the user leaves this page or moves the application
     * to the background.
     */

    super.dispose();
  }

  // ==========================================================
  // PAGE INITIALIZATION
  // ==========================================================

  Future<void> _initializePage() async {
    await LocalNotificationService.instance.initialize();

    final notificationSetting =
        await _historyService.notificationsEnabled();

    final monitoringRunning =
        await SoundMonitoringService.instance.isRunning();

    final history =
        await _historyService.getHistory();

    if (!mounted) {
      return;
    }

    setState(() {
      _notificationsEnabled =
          notificationSetting;

      _savedNotificationCount =
          history.length;

      _monitoringEnabled =
          monitoringRunning;

      if (monitoringRunning) {
        _mode =
            VoiceAssistMode.monitoring;

        _displayTitle =
            'Monitoring Active';

        _displaySubtitle =
            'AI is continuously listening to your surroundings.';
      }
    });
  }

  // ==========================================================
  // HISTORY
  // ==========================================================

  void _handleHistoryChanged() {
    _refreshHistoryCount();
  }

  Future<void> _refreshHistoryCount() async {
    final history =
        await _historyService.getHistory();

    if (!mounted) {
      return;
    }

    setState(() {
      _savedNotificationCount =
          history.length;
    });
  }

  // ==========================================================
  // SOUND MONITORING ON / OFF
  // ==========================================================

  Future<void> _toggleMonitoring(
    bool enabled,
  ) async {
    if (_monitoringChanging) {
      return;
    }

    _monitoringChanging = true;

    try {
      // ======================================================
      // START
      // ======================================================

      if (enabled) {
        if (_speech.isListening) {
          await _speech.stop();
        }

        final microphoneAllowed =
            await _permissionRecorder.hasPermission();

        if (!microphoneAllowed) {
          if (!mounted) {
            return;
          }

          setState(() {
            _mode =
                VoiceAssistMode.error;

            _displayTitle =
                'Microphone permission required';

            _displaySubtitle =
                'Allow microphone access to activate continuous sound monitoring.';
          });

          ScaffoldMessenger.of(
            context,
          ).showSnackBar(
            const SnackBar(
              content: Text(
                'Please allow microphone access.',
              ),
            ),
          );

          return;
        }

        if (!mounted) {
          return;
        }

        setState(() {
          _lastDetectedSound =
              null;

          _lastConfidence =
              null;

          _lastSeverity =
              null;

          _lastDetectedAt =
              null;

          _displayTitle =
              'Starting monitoring...';

          _displaySubtitle =
              'Preparing continuous AI sound analysis.';
        });

        final started =
            await SoundMonitoringService.instance.start();

        if (!mounted) {
          return;
        }

        setState(() {
          _monitoringEnabled =
              started;

          if (started) {
            _mode =
                VoiceAssistMode.monitoring;

            _displayTitle =
                'Monitoring Active';

            _displaySubtitle =
                'AI is continuously listening to your surroundings.';
          } else {
            _mode =
                VoiceAssistMode.error;

            _displayTitle =
                'Monitoring could not start';

            _displaySubtitle =
                'Check microphone and notification permissions, then try again.';
          }
        });

        return;
      }

      // ======================================================
      // STOP
      // ======================================================

      if (!mounted) {
        return;
      }

      setState(() {
        _displayTitle =
            'Stopping monitoring...';

        _displaySubtitle =
            'Turning off continuous microphone analysis.';
      });

      await SoundMonitoringService.instance.stop();

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .hideCurrentMaterialBanner();

      setState(() {
        _monitoringEnabled =
            false;

        _mode =
            VoiceAssistMode.idle;

        _displayTitle =
            'Monitoring Off';

        _displaySubtitle =
            'The microphone is no longer monitoring environmental sounds.';

        _lastDetectedSound =
            null;

        _lastConfidence =
            null;

        _lastSeverity =
            null;

        _lastDetectedAt =
            null;
      });
    } finally {
      _monitoringChanging = false;
    }
  }

  // ==========================================================
  // RECEIVE DATA FROM BACKGROUND MONITORING
  // ==========================================================

  void _onMonitoringData(
    Object data,
  ) {
    if (!mounted ||
        data is! Map) {
      return;
    }

    final type =
        data['type']?.toString();

    // ========================================================
    // MONITORING STATUS
    // ========================================================

    if (type ==
        'monitoring_status') {
      final status =
          data['status']?.toString();

      switch (status) {
        // ----------------------------------------------------
        // READY
        // ----------------------------------------------------

        case 'ready':
          setState(() {
            _monitoringEnabled =
                true;

            _mode =
                VoiceAssistMode.monitoring;

            /*
             * Do NOT erase the last reliable result.
             */
            if (_lastDetectedSound ==
                null) {
              _displayTitle =
                  'Monitoring Active';

              _displaySubtitle =
                  'AI is continuously listening to your surroundings.';
            }
          });

          break;

        // ----------------------------------------------------
        // LISTENING
        // ----------------------------------------------------

        case 'listening':
          setState(() {
            _monitoringEnabled =
                true;

            _mode =
                VoiceAssistMode.monitoring;

            /*
             * If there is already a reliable result,
             * keep it visible while AI starts listening again.
             */
            if (_lastDetectedSound ==
                null) {
              _displayTitle =
                  'Listening...';

              _displaySubtitle =
                  'AI is monitoring surrounding sounds.';
            }
          });

          break;

        // ----------------------------------------------------
        // ANALYZING
        // ----------------------------------------------------

        case 'analyzing':
          setState(() {
            _monitoringEnabled =
                true;

            _mode =
                VoiceAssistMode.monitoring;

            /*
             * Keep previous detection visible while
             * the next audio segment is analyzed.
             */
            if (_lastDetectedSound ==
                null) {
              _displayTitle =
                  'Analyzing...';

              _displaySubtitle =
                  'AI is analyzing the surrounding sound.';
            }
          });

          break;

        // ----------------------------------------------------
        // STOPPED
        // ----------------------------------------------------

        case 'stopped':
          ScaffoldMessenger.of(context)
              .hideCurrentMaterialBanner();

          setState(() {
            _monitoringEnabled =
                false;

            _mode =
                VoiceAssistMode.idle;

            _lastDetectedSound =
                null;

            _lastConfidence =
                null;

            _lastSeverity =
                null;

            _lastDetectedAt =
                null;

            _displayTitle =
                'Monitoring Off';

            _displaySubtitle =
                'Turn on Sound Monitoring to start continuous analysis.';
          });

          break;

        // ----------------------------------------------------
        // MICROPHONE ERROR
        // ----------------------------------------------------

        case 'microphone_error':
          setState(() {
            _mode =
                VoiceAssistMode.error;

            _displayTitle =
                'Microphone unavailable';

            _displaySubtitle =
                'Voice Assist could not access the microphone.';
          });

          break;

        // ----------------------------------------------------
        // AI / UNKNOWN ERROR
        // ----------------------------------------------------

        case 'ai_error':
        case 'error':
          setState(() {
            _mode =
                VoiceAssistMode.error;

            _displayTitle =
                'Monitoring error';

            _displaySubtitle =
                data['message']?.toString() ??
                    'An unexpected monitoring error occurred.';
          });

          break;
      }

      return;
    }

    // ========================================================
    // AI SOUND RESULT
    // ========================================================

    if (type !=
        'sound_result') {
      return;
    }

    final reliable =
        data['reliable'] ==
            true;

    /*
     * An unreliable result must NOT delete
     * the last reliable detection.
     */
    if (!reliable) {
      if (_lastDetectedSound ==
          null) {
        setState(() {
          _displayTitle =
              'Listening...';

          _displaySubtitle =
              'No reliable sound detected yet.';
        });
      }

      return;
    }

    final label =
        data['label']?.toString() ??
            'Sound detected';

    final confidence =
        (data['confidence'] as num?)
                ?.toDouble() ??
            0.0;

    final severityName =
        data['severity']?.toString() ??
            AlertSeverity.normal.name;

    AlertSeverity severity =
        AlertSeverity.normal;

    if (severityName ==
        AlertSeverity.critical.name) {
      severity =
          AlertSeverity.critical;
    } else if (severityName ==
        AlertSeverity.warning.name) {
      severity =
          AlertSeverity.warning;
    }

    final timestamp =
        (data['timestamp'] as num?)
            ?.toInt();

    final detectedAt =
        timestamp != null
            ? DateTime.fromMillisecondsSinceEpoch(
                timestamp,
              )
            : DateTime.now();

    setState(() {
      _monitoringEnabled =
          true;

      _mode =
          VoiceAssistMode.monitoring;

      _lastDetectedSound =
          label;

      _lastConfidence =
          confidence;

      _lastSeverity =
          severity;

      _lastDetectedAt =
          detectedAt;

      _displayTitle =
          label;

      if (severity ==
          AlertSeverity.critical) {
        _displaySubtitle =
            'DANGER • '
            '${(confidence * 100).toStringAsFixed(0)}% confidence';
      } else if (severity ==
          AlertSeverity.warning) {
        _displaySubtitle =
            'Important sound • '
            '${(confidence * 100).toStringAsFixed(0)}% confidence';
      } else {
        _displaySubtitle =
            'Detected automatically • '
            '${(confidence * 100).toStringAsFixed(0)}% confidence';
      }
    });
    unawaited(
  SignBridgeContextService.saveLastSound(
    label: label,
    confidence: confidence,
    severity: severity.name,
    reliable: true,
  ),
);
    // ========================================================
    // CRITICAL IN-APP RED ALERT
    // ========================================================

    if (severity ==
        AlertSeverity.critical) {
      _showCriticalInAppAlert(
        label,
        confidence,
      );
    }

    /*
     * Give the background isolate enough time
     * to save its new history entry.
     */
    Future<void>.delayed(
      const Duration(
        milliseconds: 700,
      ),
      () {
        if (mounted) {
          _refreshHistoryCount();
        }
      },
    );
  }

  // ==========================================================
  // RED CRITICAL ALERT INSIDE APPLICATION
  // ==========================================================

  void _showCriticalInAppAlert(
    String label,
    double confidence,
  ) {
    if (!mounted) {
      return;
    }

    final messenger =
        ScaffoldMessenger.of(
      context,
    );

    messenger.hideCurrentMaterialBanner();

    messenger.showMaterialBanner(
      MaterialBanner(
        backgroundColor:
            danger,
        elevation: 10,
        padding:
            const EdgeInsets.symmetric(
          horizontal: 18,
          vertical: 14,
        ),
        leading:
            const Icon(
          Icons.warning_amber_rounded,
          color: Colors.white,
          size: 35,
        ),
        content: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Text(
              'CRITICAL ALERT • $label',
              style:
                  const TextStyle(
                color:
                    Colors.white,
                fontSize: 16,
                fontWeight:
                    FontWeight.w900,
              ),
            ),
            const SizedBox(
              height: 4,
            ),
            Text(
              'Potential danger detected • '
              '${(confidence * 100).toStringAsFixed(0)}% confidence',
              style:
                  TextStyle(
                color:
                    Colors.white
                        .withValues(
                  alpha: 0.90,
                ),
                fontSize: 12,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              messenger
                  .hideCurrentMaterialBanner();
            },
            child:
                const Text(
              'DISMISS',
              style:
                  TextStyle(
                color:
                    Colors.white,
                fontWeight:
                    FontWeight.w900,
              ),
            ),
          ),
        ],
      ),
    );

    /*
     * Automatically hide it after 7 seconds.
     *
     * Monitoring itself continues.
     */
    Future<void>.delayed(
      const Duration(
        seconds: 7,
      ),
      () {
        if (mounted) {
          messenger
              .hideCurrentMaterialBanner();
        }
      },
    );
  }

  // ==========================================================
  // SPEECH TO TEXT
  // ==========================================================

  Future<void> _startSpeechToText() async {
    if (_monitoringEnabled) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(
        const SnackBar(
          content: Text(
            'Turn off Sound Monitoring before using Speech to Text.',
          ),
        ),
      );

      return;
    }

    try {
      // ------------------------------------------------------
      // STOP CURRENT STT
      // ------------------------------------------------------

      if (_speech.isListening) {
        await _speech.stop();

        if (!mounted) {
          return;
        }

        setState(() {
          _mode =
              VoiceAssistMode.idle;

          if (_recognizedSpeech
              .trim()
              .isNotEmpty) {
            _displayTitle =
                _recognizedSpeech;

            _displaySubtitle =
                'Speech converted successfully.';
          } else {
            _displayTitle =
                'Speech to Text';

            _displaySubtitle =
                'Tap again when you want to convert speech.';
          }
        });

        return;
      }

      // ------------------------------------------------------
      // INITIALIZE STT
      // ------------------------------------------------------

      final available =
          await _speech.initialize(
        onStatus: (
          status,
        ) {
          if (!mounted) {
            return;
          }

          if ((status == 'done' ||
                  status ==
                      'notListening') &&
              _mode ==
                  VoiceAssistMode
                      .speechToText) {
            setState(() {
              _mode =
                  VoiceAssistMode.idle;

              if (_recognizedSpeech
                  .trim()
                  .isEmpty) {
                _displayTitle =
                    'No speech recognized';

                _displaySubtitle =
                    'Try again and speak clearly.';
              } else {
                _displayTitle =
                    _recognizedSpeech;

                _displaySubtitle =
                    'Speech converted successfully.';
              }
            });
          }
        },
        onError: (
          error,
        ) {
          if (!mounted) {
            return;
          }

          setState(() {
            _mode =
                VoiceAssistMode.error;

            _displayTitle =
                'Speech recognition error';

            _displaySubtitle =
                error.errorMsg;
          });
        },
      );

      if (!available) {
        if (!mounted) {
          return;
        }

        setState(() {
          _mode =
              VoiceAssistMode.error;

          _displayTitle =
              'Speech recognition unavailable';

          _displaySubtitle =
              'Check microphone and speech-recognition permissions.';
        });

        return;
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _recognizedSpeech =
            '';

        _mode =
            VoiceAssistMode.speechToText;

        _displayTitle =
            'Listening to speech...';

        _displaySubtitle =
            'Speak clearly. Your words will appear as text.';
      });

      // ------------------------------------------------------
      // LISTEN
      // ------------------------------------------------------

      await _speech.listen(
        onResult: (
          result,
        ) {
          if (!mounted) {
            return;
          }

          setState(() {
            _recognizedSpeech =
                result.recognizedWords;

            if (_recognizedSpeech
                .trim()
                .isNotEmpty) {
              _displayTitle =
                  _recognizedSpeech;

              _displaySubtitle =
                  result.finalResult
                      ? 'Speech converted successfully.'
                      : 'Listening to speech...';
            }
          });
        },
        listenFor:
            const Duration(
          seconds: 30,
        ),
        pauseFor:
            const Duration(
          seconds: 4,
        ),
        listenOptions:
            stt.SpeechListenOptions(
          partialResults: true,
          cancelOnError: true,
          listenMode:
              stt.ListenMode.dictation,
          autoPunctuation: true,
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _mode =
            VoiceAssistMode.error;

        _displayTitle =
            'Speech to text failed';

        _displaySubtitle =
            error.toString();
      });
    }
  }

  // ==========================================================
  // NOTIFICATIONS
  // ==========================================================

  Future<void> _toggleNotifications(
    bool enabled,
  ) async {
    if (enabled) {
      final permissionGranted =
          await LocalNotificationService
              .instance
              .requestPermission();

      if (!permissionGranted) {
        if (!mounted) {
          return;
        }

        ScaffoldMessenger.of(
          context,
        ).showSnackBar(
          const SnackBar(
            content: Text(
              'Notification permission was not granted.',
            ),
          ),
        );

        return;
      }
    }

    await _historyService
        .setNotificationsEnabled(
      enabled,
    );

    if (!mounted) {
      return;
    }

    setState(() {
      _notificationsEnabled =
          enabled;
    });
  }

  Future<void> _openNotificationHistory() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) =>
            const NotificationHistoryPage(),
      ),
    );

    await _refreshHistoryCount();
  }

  // ==========================================================
  // RESULT TEXT
  // ==========================================================

  String _resultSubtitle() {
    final confidence =
        _lastConfidence;

    final percentage =
        confidence == null
            ? ''
            : '${(confidence * 100).toStringAsFixed(0)}% confidence';

    switch (_lastSeverity) {
      case AlertSeverity.critical:
        return percentage.isEmpty
            ? 'Potential danger detected. Check your surroundings immediately.'
            : 'Potential danger • $percentage';

      case AlertSeverity.warning:
        return percentage.isEmpty
            ? 'Important surrounding sound detected.'
            : 'Important sound • $percentage';

      case AlertSeverity.normal:
        return percentage.isEmpty
            ? 'Sound detected automatically.'
            : 'Detected automatically • $percentage';

      case null:
        return _displaySubtitle;
    }
  }

  String _formattedDetectionTime() {
    final time =
        _lastDetectedAt;

    if (time == null) {
      return '';
    }

    final hour =
        time.hour
            .toString()
            .padLeft(
              2,
              '0',
            );

    final minute =
        time.minute
            .toString()
            .padLeft(
              2,
              '0',
            );

    final second =
        time.second
            .toString()
            .padLeft(
              2,
              '0',
            );

    return '$hour:$minute:$second';
  }

  // ==========================================================
  // STATUS
  // ==========================================================

  Color get _statusColor {
    if (_mode ==
        VoiceAssistMode.error) {
      return danger;
    }

    if (_lastSeverity ==
        AlertSeverity.critical) {
      return danger;
    }

    if (_lastSeverity ==
        AlertSeverity.warning) {
      return orange;
    }

    if (_monitoringEnabled) {
      return success;
    }

    return purple;
  }

  IconData get _statusIcon {
    if (_mode ==
        VoiceAssistMode.error) {
      return Icons
          .error_outline_rounded;
    }

    if (_lastSeverity ==
        AlertSeverity.critical) {
      return Icons
          .warning_amber_rounded;
    }

    if (_lastSeverity ==
        AlertSeverity.warning) {
      return Icons
          .notifications_active_rounded;
    }

    if (_monitoringEnabled) {
      return Icons
          .graphic_eq_rounded;
    }

    if (_mode ==
        VoiceAssistMode.speechToText) {
      return Icons.mic_rounded;
    }

    return Icons
        .hearing_rounded;
  }

  // ==========================================================
  // BUILD
  // ==========================================================

  @override
  Widget build(
    BuildContext context,
  ) {
    return Scaffold(
      backgroundColor:
          Colors.white,
      body: SafeArea(
        child:
            SingleChildScrollView(
          padding:
              const EdgeInsets
                  .fromLTRB(
            18,
            14,
            18,
            28,
          ),
          child: Column(
            children: [
              _buildHeader(),

              const SizedBox(
                height: 16,
              ),

              /*
               * THIS is the large card you circled.
               * It now displays real AI detections.
               */
              _buildListeningCard(),

              const SizedBox(
                height: 18,
              ),

              _buildMonitoringCard(),

              const SizedBox(
                height: 14,
              ),

              _buildSpeechCard(),

              const SizedBox(
                height: 18,
              ),

              _buildNotificationControl(),

              const SizedBox(
                height: 14,
              ),

              _buildPrivacyMessage(),
            ],
          ),
        ),
      ),
    );
  }

  // ==========================================================
  // HEADER
  // ==========================================================

  Widget _buildHeader() {
    return Row(
      children: [
        const SizedBox(
          width: 46,
        ),

        Expanded(
          child: Column(
            children: [
              ShaderMask(
                shaderCallback: (
                  bounds,
                ) {
                  return const LinearGradient(
                    colors: [
                      purple,
                      pink,
                      orange,
                    ],
                  ).createShader(
                    bounds,
                  );
                },
                child:
                    const Text(
                  'Voice Assist',
                  style:
                      TextStyle(
                    color:
                        Colors.white,
                    fontSize: 27,
                    fontWeight:
                        FontWeight.w900,
                  ),
                ),
              ),

              const SizedBox(
                height: 4,
              ),

              const Text(
                'Hear important sounds through AI',
                textAlign:
                    TextAlign.center,
                style:
                    TextStyle(
                  color:
                      Color(
                    0xFF7B8494,
                  ),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        Stack(
          clipBehavior:
              Clip.none,
          children: [
            IconButton(
              tooltip:
                  'Notification history',
              onPressed:
                  _openNotificationHistory,
              icon:
                  const Icon(
                Icons
                    .notifications_none_rounded,
                color:
                    darkText,
                size: 29,
              ),
            ),

            if (_savedNotificationCount >
                0)
              Positioned(
                right: 2,
                top: 1,
                child:
                    Container(
                  constraints:
                      const BoxConstraints(
                    minWidth: 20,
                    minHeight: 20,
                  ),
                  padding:
                      const EdgeInsets.symmetric(
                    horizontal: 5,
                  ),
                  decoration:
                      const BoxDecoration(
                    color:
                        Colors.red,
                    shape:
                        BoxShape.circle,
                  ),
                  alignment:
                      Alignment.center,
                  child:
                      Text(
                    _savedNotificationCount >
                            99
                        ? '99+'
                        : '$_savedNotificationCount',
                    style:
                        const TextStyle(
                      color:
                          Colors.white,
                      fontSize: 10,
                      fontWeight:
                          FontWeight.w900,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }

  // ==========================================================
  // MAIN RESULT CARD
  // ==========================================================

  Widget _buildListeningCard() {
    final hasResult =
        _lastDetectedSound !=
            null;

    final critical =
        _lastSeverity ==
            AlertSeverity.critical;

    final warning =
        _lastSeverity ==
            AlertSeverity.warning;

    final borderColor =
        critical
            ? danger
            : warning
                ? orange
                : _statusColor;

    return AnimatedContainer(
      duration:
          const Duration(
        milliseconds: 350,
      ),
      width:
          double.infinity,
      padding:
          const EdgeInsets.all(
        18,
      ),
      decoration:
          BoxDecoration(
        gradient:
            critical
                ? const LinearGradient(
                    colors: [
                      Color(
                        0xFFFFF1F1,
                      ),
                      Color(
                        0xFFFFE2E2,
                      ),
                    ],
                    begin:
                        Alignment.topLeft,
                    end:
                        Alignment.bottomRight,
                  )
                : warning
                    ? const LinearGradient(
                        colors: [
                          Color(
                            0xFFFFFBF5,
                          ),
                          Color(
                            0xFFFFF1E5,
                          ),
                        ],
                        begin:
                            Alignment.topLeft,
                        end:
                            Alignment.bottomRight,
                      )
                    : const LinearGradient(
                        colors: [
                          Color(
                            0xFFFBF9FF,
                          ),
                          Color(
                            0xFFFFFAFC,
                          ),
                        ],
                        begin:
                            Alignment.topLeft,
                        end:
                            Alignment.bottomRight,
                      ),
        borderRadius:
            BorderRadius.circular(
          26,
        ),
        border:
            Border.all(
          color:
              borderColor
                  .withValues(
            alpha:
                critical
                    ? 0.60
                    : 0.18,
          ),
          width:
              critical
                  ? 2
                  : 1,
        ),
        boxShadow: [
          BoxShadow(
            color:
                borderColor
                    .withValues(
              alpha:
                  critical
                      ? 0.20
                      : 0.06,
            ),
            blurRadius:
                critical
                    ? 24
                    : 14,
            spreadRadius:
                critical
                    ? 1
                    : 0,
            offset:
                const Offset(
              0,
              6,
            ),
          ),
        ],
      ),
      child: Row(
        children: [
          // ==================================================
          // LEFT CIRCLE
          // ==================================================

          Container(
            width: 92,
            height: 92,
            decoration:
                BoxDecoration(
              shape:
                  BoxShape.circle,
              gradient:
                  LinearGradient(
                colors:
                    critical
                        ? const [
                            Color(
                              0xFFFF1744,
                            ),
                            danger,
                            Color(
                              0xFFFF6B4A,
                            ),
                          ]
                        : warning
                            ? const [
                                orange,
                                Color(
                                  0xFFFFB347,
                                ),
                                pink,
                              ]
                            : const [
                                purple,
                                pink,
                                orange,
                              ],
                begin:
                    Alignment.topLeft,
                end:
                    Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color:
                      borderColor
                          .withValues(
                    alpha: 0.22,
                  ),
                  blurRadius: 20,
                ),
              ],
            ),
            child:
                Container(
              margin:
                  const EdgeInsets.all(
                5,
              ),
              decoration:
                  const BoxDecoration(
                color:
                    Colors.white,
                shape:
                    BoxShape.circle,
              ),
              child:
                  Icon(
                _statusIcon,
                color:
                    _statusColor,
                size: 41,
              ),
            ),
          ),

          const SizedBox(
            width: 17,
          ),

          // ==================================================
          // RESULT
          // ==================================================

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                if (critical)
                  Container(
                    margin:
                        const EdgeInsets.only(
                      bottom: 7,
                    ),
                    padding:
                        const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 5,
                    ),
                    decoration:
                        BoxDecoration(
                      color:
                          danger,
                      borderRadius:
                          BorderRadius.circular(
                        30,
                      ),
                    ),
                    child:
                        const Text(
                      'CRITICAL ALERT',
                      style:
                          TextStyle(
                        color:
                            Colors.white,
                        fontSize: 9,
                        letterSpacing:
                            0.9,
                        fontWeight:
                            FontWeight.w900,
                      ),
                    ),
                  ),

                if (warning)
                  Container(
                    margin:
                        const EdgeInsets.only(
                      bottom: 7,
                    ),
                    padding:
                        const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 5,
                    ),
                    decoration:
                        BoxDecoration(
                      color:
                          orange.withValues(
                        alpha: 0.14,
                      ),
                      borderRadius:
                          BorderRadius.circular(
                        30,
                      ),
                    ),
                    child:
                        const Text(
                      'IMPORTANT SOUND',
                      style:
                          TextStyle(
                        color:
                            orange,
                        fontSize: 9,
                        letterSpacing:
                            0.7,
                        fontWeight:
                            FontWeight.w900,
                      ),
                    ),
                  ),

                Text(
                  hasResult
                      ? _lastDetectedSound!
                      : _displayTitle,
                  maxLines: 2,
                  overflow:
                      TextOverflow.ellipsis,
                  style:
                      TextStyle(
                    color:
                        critical
                            ? dangerDark
                            : darkText,
                    fontSize:
                        hasResult
                            ? 22
                            : 20,
                    fontWeight:
                        FontWeight.w900,
                    height: 1.12,
                  ),
                ),

                const SizedBox(
                  height: 7,
                ),

                Text(
                  hasResult
                      ? _resultSubtitle()
                      : _displaySubtitle,
                  maxLines: 3,
                  overflow:
                      TextOverflow.ellipsis,
                  style:
                      TextStyle(
                    color:
                        critical
                            ? danger
                            : warning
                                ? const Color(
                                    0xFFD66F24,
                                  )
                                : const Color(
                                    0xFF7B8494,
                                  ),
                    fontSize: 12,
                    height: 1.4,
                    fontWeight:
                        critical
                            ? FontWeight.w700
                            : FontWeight.normal,
                  ),
                ),

                if (hasResult &&
                    _lastDetectedAt !=
                        null) ...[
                  const SizedBox(
                    height: 6,
                  ),
                  Text(
                    'Detected at ${_formattedDetectionTime()}',
                    style:
                        TextStyle(
                      color:
                          borderColor
                              .withValues(
                        alpha: 0.80,
                      ),
                      fontSize: 10,
                      fontWeight:
                          FontWeight.w600,
                    ),
                  ),
                ],

                if (_monitoringEnabled) ...[
                  const SizedBox(
                    height: 10,
                  ),

                  Container(
                    padding:
                        const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 6,
                    ),
                    decoration:
                        BoxDecoration(
                      color:
                          critical
                              ? danger.withValues(
                                  alpha: 0.10,
                                )
                              : success.withValues(
                                  alpha: 0.10,
                                ),
                      borderRadius:
                          BorderRadius.circular(
                        50,
                      ),
                    ),
                    child: Row(
                      mainAxisSize:
                          MainAxisSize.min,
                      children: [
                        Container(
                          width: 7,
                          height: 7,
                          decoration:
                              BoxDecoration(
                            color:
                                critical
                                    ? danger
                                    : success,
                            shape:
                                BoxShape.circle,
                          ),
                        ),

                        const SizedBox(
                          width: 6,
                        ),

                        Text(
                          critical
                              ? 'MONITORING CONTINUES'
                              : 'LIVE MONITORING',
                          style:
                              TextStyle(
                            color:
                                critical
                                    ? danger
                                    : const Color(
                                        0xFF329567,
                                      ),
                            fontSize: 9,
                            letterSpacing:
                                0.7,
                            fontWeight:
                                FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),

          const SizedBox(
            width: 7,
          ),

          // ==================================================
          // RIGHT ICON
          // ==================================================

          Icon(
            critical
                ? Icons
                    .emergency_rounded
                : warning
                    ? Icons
                        .notifications_active_rounded
                    : Icons
                        .graphic_eq_rounded,
            size: 34,
            color:
                critical
                    ? danger
                    : warning
                        ? orange
                        : pink,
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // MONITORING CARD
  // ==========================================================

  Widget _buildMonitoringCard() {
    final active =
        _monitoringEnabled;

    return AnimatedContainer(
      duration:
          const Duration(
        milliseconds: 300,
      ),
      width:
          double.infinity,
      padding:
          const EdgeInsets.all(
        18,
      ),
      decoration:
          BoxDecoration(
        gradient:
            LinearGradient(
          colors:
              active
                  ? const [
                      Color(
                        0xFF5D35F5,
                      ),
                      Color(
                        0xFF9A4FF2,
                      ),
                      Color(
                        0xFFFF668E,
                      ),
                    ]
                  : const [
                      Color(
                        0xFFF7F3FF,
                      ),
                      Color(
                        0xFFFFF5F1,
                      ),
                    ],
          begin:
              Alignment.topLeft,
          end:
              Alignment.bottomRight,
        ),
        borderRadius:
            BorderRadius.circular(
          25,
        ),
        border:
            Border.all(
          color:
              active
                  ? Colors.transparent
                  : const Color(
                      0xFFEAE2FF,
                    ),
        ),
        boxShadow: [
          BoxShadow(
            color:
                active
                    ? purple.withValues(
                        alpha: 0.23,
                      )
                    : Colors.black.withValues(
                        alpha: 0.04,
                      ),
            blurRadius:
                active
                    ? 22
                    : 12,
            offset:
                const Offset(
              0,
              7,
            ),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration:
                BoxDecoration(
              color:
                  active
                      ? Colors.white.withValues(
                          alpha: 0.18,
                        )
                      : purple.withValues(
                          alpha: 0.10,
                        ),
              borderRadius:
                  BorderRadius.circular(
                20,
              ),
              border:
                  Border.all(
                color:
                    active
                        ? Colors.white.withValues(
                            alpha: 0.23,
                          )
                        : Colors.transparent,
              ),
            ),
            child:
                Icon(
              active
                  ? Icons
                      .graphic_eq_rounded
                  : Icons
                      .hearing_rounded,
              color:
                  active
                      ? Colors.white
                      : purple,
              size: 35,
            ),
          ),

          const SizedBox(
            width: 15,
          ),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  'Sound Monitoring',
                  style:
                      TextStyle(
                    color:
                        active
                            ? Colors.white
                            : darkText,
                    fontSize: 18,
                    fontWeight:
                        FontWeight.w900,
                  ),
                ),

                const SizedBox(
                  height: 5,
                ),

                Text(
                  active
                      ? 'AI keeps listening even while you use another app.'
                      : 'Turn on continuous environmental sound detection.',
                  style:
                      TextStyle(
                    color:
                        active
                            ? Colors.white.withValues(
                                alpha: 0.83,
                              )
                            : const Color(
                                0xFF7B8494,
                              ),
                    fontSize: 11.5,
                    height: 1.35,
                  ),
                ),

                if (active) ...[
                  const SizedBox(
                    height: 9,
                  ),

                  Row(
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration:
                            const BoxDecoration(
                          color:
                              Color(
                            0xFF7DFFBC,
                          ),
                          shape:
                              BoxShape.circle,
                        ),
                      ),

                      const SizedBox(
                        width: 6,
                      ),

                      Text(
                        'MICROPHONE ACTIVE',
                        style:
                            TextStyle(
                          color:
                              Colors.white.withValues(
                            alpha: 0.90,
                          ),
                          fontSize: 9,
                          letterSpacing:
                              0.75,
                          fontWeight:
                              FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),

          const SizedBox(
            width: 8,
          ),

          _monitoringChanging
              ? SizedBox(
                  width: 36,
                  height: 36,
                  child:
                      CircularProgressIndicator(
                    strokeWidth: 3,
                    color:
                        active
                            ? Colors.white
                            : purple,
                  ),
                )
              : Switch(
                  value:
                      active,
                  onChanged:
                      _toggleMonitoring,
                  activeTrackColor:
                      Colors.white.withValues(
                    alpha: 0.38,
                  ),
                  activeThumbColor:
                      Colors.white,
                  inactiveTrackColor:
                      purple.withValues(
                    alpha: 0.12,
                  ),
                  inactiveThumbColor:
                      purple,
                ),
        ],
      ),
    );
  }

  // ==========================================================
  // SPEECH TO TEXT CARD
  // ==========================================================

  Widget _buildSpeechCard() {
    final active =
        _mode ==
            VoiceAssistMode.speechToText;

    final disabled =
        _monitoringEnabled;

    return Opacity(
      opacity:
          disabled
              ? 0.58
              : 1,
      child: Material(
        color:
            Colors.transparent,
        child: InkWell(
          onTap:
              _startSpeechToText,
          borderRadius:
              BorderRadius.circular(
            25,
          ),
          child:
              AnimatedContainer(
            duration:
                const Duration(
              milliseconds: 250,
            ),
            width:
                double.infinity,
            padding:
                const EdgeInsets.all(
              18,
            ),
            decoration:
                BoxDecoration(
              gradient:
                  const LinearGradient(
                colors: [
                  Color(
                    0xFFFF7847,
                  ),
                  Color(
                    0xFFFF9D56,
                  ),
                  Color(
                    0xFFFFC367,
                  ),
                ],
                begin:
                    Alignment.topLeft,
                end:
                    Alignment.bottomRight,
              ),
              borderRadius:
                  BorderRadius.circular(
                25,
              ),
              boxShadow: [
                BoxShadow(
                  color:
                      orange.withValues(
                    alpha:
                        active
                            ? 0.28
                            : 0.16,
                  ),
                  blurRadius:
                      active
                          ? 22
                          : 14,
                  offset:
                      const Offset(
                    0,
                    7,
                  ),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  width: 62,
                  height: 62,
                  decoration:
                      BoxDecoration(
                    color:
                        Colors.white.withValues(
                      alpha: 0.18,
                    ),
                    borderRadius:
                        BorderRadius.circular(
                      20,
                    ),
                    border:
                        Border.all(
                      color:
                          Colors.white.withValues(
                        alpha: 0.25,
                      ),
                    ),
                  ),
                  child:
                      const Icon(
                    Icons
                        .mic_none_rounded,
                    color:
                        Colors.white,
                    size: 34,
                  ),
                ),

                const SizedBox(
                  width: 15,
                ),

                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding:
                            const EdgeInsets.symmetric(
                          horizontal: 9,
                          vertical: 4,
                        ),
                        decoration:
                            BoxDecoration(
                          color:
                              Colors.white.withValues(
                            alpha: 0.17,
                          ),
                          borderRadius:
                              BorderRadius.circular(
                            30,
                          ),
                        ),
                        child:
                            Text(
                          active
                              ? 'LISTENING'
                              : 'LIVE TEXT',
                          style:
                              const TextStyle(
                            color:
                                Colors.white,
                            fontSize: 9,
                            letterSpacing:
                                0.8,
                            fontWeight:
                                FontWeight.w900,
                          ),
                        ),
                      ),

                      const SizedBox(
                        height: 8,
                      ),

                      const Text(
                        'Speech to Text',
                        style:
                            TextStyle(
                          color:
                              Colors.white,
                          fontSize: 18,
                          fontWeight:
                              FontWeight.w900,
                        ),
                      ),

                      const SizedBox(
                        height: 4,
                      ),

                      Text(
                        disabled
                            ? 'Turn off Sound Monitoring first.'
                            : active
                                ? 'Listening to speech...'
                                : 'Convert spoken conversations into readable text.',
                        style:
                            TextStyle(
                          color:
                              Colors.white.withValues(
                            alpha: 0.85,
                          ),
                          fontSize: 11.5,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(
                  width: 7,
                ),

                Container(
                  width: 38,
                  height: 38,
                  decoration:
                      BoxDecoration(
                    color:
                        Colors.white.withValues(
                      alpha: 0.16,
                    ),
                    shape:
                        BoxShape.circle,
                  ),
                  child:
                      Icon(
                    active
                        ? Icons
                            .graphic_eq_rounded
                        : Icons
                            .arrow_forward_rounded,
                    color:
                        Colors.white,
                    size: 21,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ==========================================================
  // NOTIFICATIONS
  // ==========================================================

  Widget _buildNotificationControl() {
    return Container(
      width:
          double.infinity,
      padding:
          const EdgeInsets.all(
        16,
      ),
      decoration:
          BoxDecoration(
        color:
            Colors.white,
        borderRadius:
            BorderRadius.circular(
          22,
        ),
        border:
            Border.all(
          color:
              const Color(
            0xFFECECF3,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color:
                Colors.black.withValues(
              alpha: 0.04,
            ),
            blurRadius: 11,
            offset:
                const Offset(
              0,
              5,
            ),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration:
                BoxDecoration(
              gradient:
                  const LinearGradient(
                colors: [
                  purple,
                  pink,
                ],
              ),
              borderRadius:
                  BorderRadius.circular(
                16,
              ),
            ),
            child:
                const Icon(
              Icons
                  .notifications_active_rounded,
              color:
                  Colors.white,
            ),
          ),

          const SizedBox(
            width: 14,
          ),

          const Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  'Sound Notifications',
                  style:
                      TextStyle(
                    color:
                        darkText,
                    fontSize: 16,
                    fontWeight:
                        FontWeight.w900,
                  ),
                ),

                SizedBox(
                  height: 4,
                ),

                Text(
                  'Alert me when AI detects a reliable important sound',
                  style:
                      TextStyle(
                    color:
                        Color(
                      0xFF7B8494,
                    ),
                    fontSize: 11.5,
                  ),
                ),
              ],
            ),
          ),

          Switch(
            value:
                _notificationsEnabled,
            onChanged:
                _toggleNotifications,
            activeTrackColor:
                purple,
            activeThumbColor:
                Colors.white,
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // PRIVACY
  // ==========================================================

  Widget _buildPrivacyMessage() {
    return Container(
      width:
          double.infinity,
      padding:
          const EdgeInsets.symmetric(
        horizontal: 14,
        vertical: 12,
      ),
      decoration:
          BoxDecoration(
        color:
            const Color(
          0xFFF8F9FC,
        ),
        borderRadius:
            BorderRadius.circular(
          16,
        ),
      ),
      child:
          const Row(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Icon(
            Icons
                .privacy_tip_outlined,
            size: 18,
            color:
                Color(
              0xFF7B8494,
            ),
          ),

          SizedBox(
            width: 9,
          ),

          Expanded(
            child: Text(
              'Audio is analyzed temporarily. '
              'The monitoring service deletes each recording after analysis; '
              'only detected alert information is saved to history.',
              style:
                  TextStyle(
                color:
                    Color(
                  0xFF7B8494,
                ),
                fontSize: 10.5,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}