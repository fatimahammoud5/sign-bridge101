import 'package:flutter/material.dart';

import 'sound_prediction.dart';

class AlertRecord {
  final String id;
  final String title;
  final String description;
  final double confidence;
  final AlertSeverity severity;
  final DateTime createdAt;

  const AlertRecord({
    required this.id,
    required this.title,
    required this.description,
    required this.confidence,
    required this.severity,
    required this.createdAt,
  });

  double get confidencePercentage => confidence * 100.0;

  String get formattedConfidence {
    return '${confidencePercentage.toStringAsFixed(1)}%';
  }

  Color get color {
    switch (severity) {
      case AlertSeverity.normal:
        return const Color(0xFF7B2FF7);

      case AlertSeverity.warning:
        return const Color(0xFFFF8C42);

      case AlertSeverity.critical:
        return const Color(0xFFE53935);
    }
  }

  Color get backgroundColor {
    return color.withValues(alpha: 0.09);
  }

  IconData get icon {
    switch (severity) {
      case AlertSeverity.normal:
        return Icons.hearing_rounded;

      case AlertSeverity.warning:
        return Icons.warning_amber_rounded;

      case AlertSeverity.critical:
        return Icons.emergency_rounded;
    }
  }

  String get severityName {
    switch (severity) {
      case AlertSeverity.normal:
        return 'Normal';

      case AlertSeverity.warning:
        return 'Warning';

      case AlertSeverity.critical:
        return 'Critical';
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'confidence': confidence,
      'severity': severity.name,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  factory AlertRecord.fromJson(Map<String, dynamic> json) {
    final severityName =
        json['severity']?.toString() ?? AlertSeverity.normal.name;

    return AlertRecord(
      id: json['id']?.toString() ??
          DateTime.now().millisecondsSinceEpoch.toString(),
      title: json['title']?.toString() ?? 'Detected sound',
      description: json['description']?.toString() ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      severity: AlertSeverity.values.firstWhere(
        (item) => item.name == severityName,
        orElse: () => AlertSeverity.normal,
      ),
      createdAt:
          DateTime.tryParse(json['createdAt']?.toString() ?? '') ??
              DateTime.now(),
    );
  }
}