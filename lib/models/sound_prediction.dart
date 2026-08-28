enum AlertSeverity {
  normal,
  warning,
  critical,
}

class SoundPrediction {
  final String label;
  final double confidence;
  final AlertSeverity severity;
  final DateTime detectedAt;
  final bool isReliable;

  const SoundPrediction({
    required this.label,
    required this.confidence,
    required this.severity,
    required this.detectedAt,
    required this.isReliable,
  });

  double get confidencePercentage => confidence * 100.0;

  String get formattedConfidence {
    return '${confidencePercentage.toStringAsFixed(1)}%';
  }
}