import 'package:flutter/foundation.dart';
import 'package:torch_light/torch_light.dart';

import '../models/sound_prediction.dart';

class FlashAlertService {
  FlashAlertService._();

  static final FlashAlertService instance =
      FlashAlertService._();

  bool _isFlashing = false;

  /// Flash pattern according to the detected sound severity.
  ///
  /// normal   -> no flash
  /// warning  -> 3 flashes
  /// critical -> 6 faster flashes
  Future<void> flashForSeverity(
    AlertSeverity severity,
  ) async {
    if (severity == AlertSeverity.normal) {
      return;
    }

    // Prevent two flash patterns from running at the same time.
    if (_isFlashing) {
      debugPrint(
        'FLASH ALERT: already flashing.',
      );
      return;
    }

    _isFlashing = true;

    try {
      final bool available =
          await TorchLight.isTorchAvailable();

      if (!available) {
        debugPrint(
          'FLASH ALERT: flashlight is not available.',
        );
        return;
      }

      switch (severity) {
        case AlertSeverity.normal:
          return;

        case AlertSeverity.warning:
          debugPrint(
            'FLASH ALERT: WARNING pattern started.',
          );

          await _flashPattern(
            flashes: 3,
            onDuration: const Duration(
              milliseconds: 200,
            ),
            offDuration: const Duration(
              milliseconds: 250,
            ),
          );

          break;

        case AlertSeverity.critical:
          debugPrint(
            'FLASH ALERT: CRITICAL pattern started.',
          );

          await _flashPattern(
            flashes: 6,
            onDuration: const Duration(
              milliseconds: 140,
            ),
            offDuration: const Duration(
              milliseconds: 140,
            ),
          );

          break;
      }

      debugPrint(
        'FLASH ALERT: pattern completed.',
      );
    } catch (error, stackTrace) {
      debugPrint(
        'FLASH ALERT ERROR: $error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );
    } finally {
      // Always try to leave the torch OFF.
      try {
        await TorchLight.disableTorch();
      } catch (_) {
        // Ignore because the torch may already be off
        // or unavailable.
      }

      _isFlashing = false;
    }
  }

  Future<void> _flashPattern({
    required int flashes,
    required Duration onDuration,
    required Duration offDuration,
  }) async {
    for (int index = 0; index < flashes; index++) {
      try {
        await TorchLight.enableTorch();

        await Future<void>.delayed(
          onDuration,
        );

        await TorchLight.disableTorch();

        if (index < flashes - 1) {
          await Future<void>.delayed(
            offDuration,
          );
        }
      } catch (error) {
        debugPrint(
          'FLASH ALERT: flash '
          '${index + 1}/$flashes failed: $error',
        );

        try {
          await TorchLight.disableTorch();
        } catch (_) {}

        break;
      }
    }
  }
}