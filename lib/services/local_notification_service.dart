import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../models/alert_record.dart';
import '../models/sound_prediction.dart';

class LocalNotificationService {
  LocalNotificationService._();

  static final LocalNotificationService instance =
      LocalNotificationService._();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;

  // ==========================================================
  // INITIALIZE
  // ==========================================================

  Future<void> initialize() async {
    if (_initialized) {
      return;
    }

    const androidSettings =
        AndroidInitializationSettings(
      '@mipmap/ic_launcher',
    );

    const iosSettings =
        DarwinInitializationSettings();

    const settings =
        InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _plugin.initialize(
      settings: settings,
      onDidReceiveNotificationResponse: (
        response,
      ) {
        debugPrint(
          'NOTIFICATION CLICKED: ${response.payload}',
        );
      },
    );

    // Create Android channels.
    if (Platform.isAndroid) {
      final androidPlugin =
          _plugin.resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();

      // Normal notifications.
      await androidPlugin?.createNotificationChannel(
        const AndroidNotificationChannel(
          'voice_assist_normal',
          'Voice Assist Notifications',
          description:
              'Environmental sound notifications from Voice Assist.',
          importance: Importance.high,
          playSound: true,
          enableVibration: true,
        ),
      );

      // WARNING channel.
      await androidPlugin?.createNotificationChannel(
        const AndroidNotificationChannel(
          'voice_assist_warning',
          'Important Sound Alerts',
          description:
              'Important environmental sound alerts.',
          importance: Importance.high,
          playSound: true,
          enableVibration: true,
        ),
      );

      // CRITICAL channel.
      //
      // IMPORTANT:
      // Separate channel is necessary because Android remembers
      // notification-channel importance after creation.
      await androidPlugin?.createNotificationChannel(
        const AndroidNotificationChannel(
          'voice_assist_critical',
          'Critical Safety Alerts',
          description:
              'Urgent alerts for potentially dangerous sounds.',
          importance: Importance.max,
          playSound: true,
          enableVibration: true,
          showBadge: true,
        ),
      );
    }

    _initialized = true;

    debugPrint(
      'LOCAL NOTIFICATION SERVICE READY',
    );
  }

  // ==========================================================
  // PERMISSION
  // ==========================================================

  Future<bool> requestPermission() async {
    await initialize();

    if (Platform.isAndroid) {
      final androidPlugin =
          _plugin.resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();

      final result =
          await androidPlugin
              ?.requestNotificationsPermission();

      return result ?? true;
    }

    if (Platform.isIOS) {
      final iosPlugin =
          _plugin.resolvePlatformSpecificImplementation<
              IOSFlutterLocalNotificationsPlugin>();

      final result =
          await iosPlugin?.requestPermissions(
        alert: true,
        badge: true,
        sound: true,
      );

      return result ?? false;
    }

    return true;
  }

  // ==========================================================
  // SHOW SOUND ALERT
  // ==========================================================

  Future<void> showSoundAlert(
    AlertRecord record,
  ) async {
    await initialize();

    final details =
        _notificationDetailsFor(
      record.severity,
    );

    final String title;
    final String body;

    switch (record.severity) {
      case AlertSeverity.critical:
        title =
            '🚨 DANGER: ${record.title}';

        body =
            'Potentially dangerous sound detected. '
            'Check your surroundings immediately.';

        break;

      case AlertSeverity.warning:
        title =
            '⚠️ Important sound: ${record.title}';

        body =
            record.description;

        break;

      case AlertSeverity.normal:
        title =
            '🔔 ${record.title}';

        body =
            record.description;

        break;
    }

    await _plugin.show(
      id: DateTime.now()
          .millisecondsSinceEpoch
          .remainder(
            2147483647,
          ),
      title: title,
      body: body,
      notificationDetails: details,
      payload:
          'sound_alert:${record.id}',
    );

    debugPrint(
      'LOCAL NOTIFICATION SENT: '
      '${record.title} / ${record.severity.name}',
    );
  }

  // ==========================================================
  // DETAILS BY SEVERITY
  // ==========================================================

  NotificationDetails
      _notificationDetailsFor(
    AlertSeverity severity,
  ) {
    switch (severity) {
      // ------------------------------------------------------
      // CRITICAL
      // ------------------------------------------------------
      case AlertSeverity.critical:
        return const NotificationDetails(
          android:
              AndroidNotificationDetails(
            'voice_assist_critical',
            'Critical Safety Alerts',
            channelDescription:
                'Urgent alerts for potentially dangerous sounds.',

            importance:
                Importance.max,

            priority:
                Priority.max,

            category:
                AndroidNotificationCategory.alarm,

            visibility:
                NotificationVisibility.public,

            playSound:
                true,

            enableVibration:
                true,

            color:
                Color(
              0xFFE53935,
            ),

            colorized:
                true,

            ticker:
                'Critical sound detected',

            styleInformation:
                BigTextStyleInformation(
              'A potentially dangerous sound was detected. '
              'Check your surroundings immediately.',
            ),
          ),
          iOS:
              DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
            interruptionLevel:
                InterruptionLevel.timeSensitive,
          ),
        );

      // ------------------------------------------------------
      // WARNING
      // ------------------------------------------------------
      case AlertSeverity.warning:
        return const NotificationDetails(
          android:
              AndroidNotificationDetails(
            'voice_assist_warning',
            'Important Sound Alerts',
            channelDescription:
                'Important environmental sound alerts.',
            importance:
                Importance.high,
            priority:
                Priority.high,
            category:
                AndroidNotificationCategory.reminder,
            visibility:
                NotificationVisibility.public,
            playSound:
                true,
            enableVibration:
                true,
            color:
                Color(
              0xFFFF8C42,
            ),
          ),
          iOS:
              DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        );

      // ------------------------------------------------------
      // NORMAL
      // ------------------------------------------------------
      case AlertSeverity.normal:
        return const NotificationDetails(
          android:
              AndroidNotificationDetails(
            'voice_assist_normal',
            'Voice Assist Notifications',
            channelDescription:
                'Environmental sound notifications from Voice Assist.',
            importance:
                Importance.high,
            priority:
                Priority.high,
            visibility:
                NotificationVisibility.public,
            playSound:
                true,
            enableVibration:
                true,
            color:
                Color(
              0xFF7B2FF7,
            ),
          ),
          iOS:
              DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        );
    }
  }

  // ==========================================================
  // OPTIONAL TEST
  // ==========================================================

  Future<void> showCriticalTestNotification() async {
    await initialize();

    const details =
        NotificationDetails(
      android:
          AndroidNotificationDetails(
        'voice_assist_critical',
        'Critical Safety Alerts',
        channelDescription:
            'Urgent alerts for potentially dangerous sounds.',
        importance:
            Importance.max,
        priority:
            Priority.max,
        category:
            AndroidNotificationCategory.alarm,
        visibility:
            NotificationVisibility.public,
        playSound:
            true,
        enableVibration:
            true,
        color:
            Color(
          0xFFE53935,
        ),
        colorized:
            true,
      ),
      iOS:
          DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
        interruptionLevel:
            InterruptionLevel.timeSensitive,
      ),
    );

    await _plugin.show(
      id: 998877,
      title:
          '🚨 Critical safety alert',
      body:
          'Test: dangerous sound notification is working.',
      notificationDetails:
          details,
      payload:
          'critical_test',
    );
  }
}