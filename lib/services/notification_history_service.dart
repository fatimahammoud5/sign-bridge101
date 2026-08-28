import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/alert_record.dart';

class NotificationHistoryService {
  NotificationHistoryService._();

  static final NotificationHistoryService instance =
      NotificationHistoryService._();

  static const String _historyKey =
      'voice_assist_notification_history';

  static const String _notificationsEnabledKey =
      'voice_assist_notifications_enabled';

  static const int _maxHistoryItems = 200;

  /*
   * SharedPreferencesAsync does NOT use the old
   * per-isolate cache.
   *
   * This is important because Sound Monitoring
   * writes history from a background isolate.
   */
  final SharedPreferencesAsync _preferences =
      SharedPreferencesAsync();

  /*
   * Used only to tell the open UI that it should
   * refresh its list/count.
   *
   * The actual data always comes from persistent storage.
   */
  final ValueNotifier<int> historyVersion =
      ValueNotifier<int>(0);

  // ==========================================================
  // GET HISTORY
  // ==========================================================

  Future<List<AlertRecord>> getHistory() async {
    try {
      final jsonString =
          await _preferences.getString(
        _historyKey,
      );

      if (jsonString == null ||
          jsonString.trim().isEmpty) {
        return <AlertRecord>[];
      }

      final decoded =
          jsonDecode(jsonString);

      if (decoded is! List) {
        debugPrint(
          'NOTIFICATION HISTORY: invalid stored data.',
        );

        return <AlertRecord>[];
      }

      final records =
          <AlertRecord>[];

      for (final item in decoded) {
        try {
          if (item is Map) {
            final map =
                Map<String, dynamic>.from(
              item,
            );

            records.add(
              AlertRecord.fromJson(
                map,
              ),
            );
          }
        } catch (error) {
          debugPrint(
            'NOTIFICATION HISTORY: '
            'could not decode one record: $error',
          );
        }
      }

      records.sort(
        (a, b) =>
            b.createdAt.compareTo(
          a.createdAt,
        ),
      );

      return records;
    } catch (error, stackTrace) {
      debugPrint(
        'NOTIFICATION HISTORY READ ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      return <AlertRecord>[];
    }
  }

  // ==========================================================
  // ADD RECORD
  // ==========================================================

  Future<void> addRecord(
    AlertRecord record,
  ) async {
    try {
      debugPrint(
        'NOTIFICATION HISTORY: adding ${record.title}',
      );

      /*
       * Always read fresh data from native storage.
       * This is safe when called from the foreground
       * service isolate.
       */
      final current =
          await getHistory();

      /*
       * Avoid duplicate ID.
       */
      current.removeWhere(
        (item) =>
            item.id == record.id,
      );

      current.insert(
        0,
        record,
      );

      /*
       * Keep history reasonably small.
       */
      if (current.length >
          _maxHistoryItems) {
        current.removeRange(
          _maxHistoryItems,
          current.length,
        );
      }

      final encoded =
          jsonEncode(
        current
            .map(
              (item) =>
                  item.toJson(),
            )
            .toList(),
      );

      await _preferences.setString(
        _historyKey,
        encoded,
      );

      debugPrint(
        'NOTIFICATION HISTORY: '
        'saved successfully. '
        'Total = ${current.length}',
      );

      /*
       * This notifier only updates listeners that
       * live in the SAME isolate.
       *
       * The UI also reloads from storage when opening
       * the history page, so background writes remain
       * visible.
       */
      historyVersion.value =
          historyVersion.value + 1;
    } catch (error, stackTrace) {
      debugPrint(
        'NOTIFICATION HISTORY SAVE ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      rethrow;
    }
  }

  // ==========================================================
  // DELETE ONE
  // ==========================================================

  Future<void> deleteRecord(
    String id,
  ) async {
    try {
      final current =
          await getHistory();

      current.removeWhere(
        (item) =>
            item.id == id,
      );

      await _saveHistory(
        current,
      );

      historyVersion.value =
          historyVersion.value + 1;
    } catch (error, stackTrace) {
      debugPrint(
        'NOTIFICATION HISTORY DELETE ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      rethrow;
    }
  }

  // ==========================================================
  // CLEAR ALL
  // ==========================================================

  Future<void> clearHistory() async {
    try {
      await _preferences.remove(
        _historyKey,
      );

      historyVersion.value =
          historyVersion.value + 1;

      debugPrint(
        'NOTIFICATION HISTORY: cleared.',
      );
    } catch (error, stackTrace) {
      debugPrint(
        'NOTIFICATION HISTORY CLEAR ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      rethrow;
    }
  }

  // ==========================================================
  // NOTIFICATION SETTING
  // ==========================================================

  Future<bool> notificationsEnabled() async {
    try {
      final value =
          await _preferences.getBool(
        _notificationsEnabledKey,
      );

      /*
       * Enabled by default.
       */
      return value ?? true;
    } catch (error) {
      debugPrint(
        'NOTIFICATION SETTING READ ERROR: $error',
      );

      return true;
    }
  }

  Future<void> setNotificationsEnabled(
    bool enabled,
  ) async {
    try {
      await _preferences.setBool(
        _notificationsEnabledKey,
        enabled,
      );

      debugPrint(
        'NOTIFICATIONS ENABLED = $enabled',
      );
    } catch (error, stackTrace) {
      debugPrint(
        'NOTIFICATION SETTING SAVE ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      rethrow;
    }
  }

  // ==========================================================
  // PRIVATE SAVE
  // ==========================================================

  Future<void> _saveHistory(
    List<AlertRecord> records,
  ) async {
    records.sort(
      (a, b) =>
          b.createdAt.compareTo(
        a.createdAt,
      ),
    );

    if (records.length >
        _maxHistoryItems) {
      records.removeRange(
        _maxHistoryItems,
        records.length,
      );
    }

    final encoded =
        jsonEncode(
      records
          .map(
            (item) =>
                item.toJson(),
          )
          .toList(),
    );

    await _preferences.setString(
      _historyKey,
      encoded,
    );
  }
}