import 'dart:math';
import 'dart:typed_data';

import 'package:csv/csv.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

import '../models/sound_prediction.dart';

class AIService {
  // ============================================================
  // MODEL SETTINGS
  // ============================================================

  static const int sampleRate = 16000;
  static const int inputLength = 15600;
  static const int classCount = 521;

  static const String modelPath =
      'assets/models/yamnet_classification.tflite';

  static const String labelsPath =
      'assets/models/yamnet_class_map.csv';

  Interpreter? _interpreter;

  List<String> _labels = [];
  List<String> _normalizedLabels = [];

  String? _lastLoadError;

  bool get isLoaded =>
      _interpreter != null &&
      _labels.length == classCount;

  String? get lastLoadError => _lastLoadError;

  // ============================================================
  // PRESENTATION-SAFE SOUND FAMILIES
  //
  // IMPORTANT:
  //
  // We intentionally DO NOT support generic labels such as:
  //
  // Animal
  // Vehicle
  // Noise
  // White noise
  // Mechanical fan
  // Inside, small room
  // Cacophony
  //
  // Those become "Uncertain sound".
  // ============================================================

  static const List<_FamilyRule> _rules = [
    // ----------------------------------------------------------
    // CAT
    //
    // Your real phone tests:
    // Cat / Meow / Caterwaul were consistently strong.
    // Generic Animal / Domestic animals must not steal the result.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Cat',
      exactLabels: [
        'cat',
        'meow',
        'purr',
        'caterwaul',
      ],
      minScore: 0.48,
      minPeak: 0.55,
      minMargin: 0.05,
      highConfidence: 0.82,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // DOG
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Dog Barking',
      exactLabels: [
        'dog',
        'bark',
        'bow-wow',
        'yip',
        'howl',
        'growling',
        'whimper (dog)',
      ],
      minScore: 0.48,
      minPeak: 0.55,
      minMargin: 0.05,
      highConfidence: 0.82,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // BIRD
    // ----------------------------------------------------------

        _FamilyRule(
      label: 'Bird',
      exactLabels: [
        'bird',
        'bird vocalization, bird call, bird song',
        'chirp, tweet',
        'squawk',
        'crow',
        'caw',
        'owl',
        'hoot',
        'pigeon, dove',
        'coo',
      ],

      // Real-phone results showed clear bird evidence
      // even when the combined family score was around 30-40%.
      minScore: 0.30,
      minPeak: 0.38,

      minMargin: 0.05,
      highConfidence: 0.82,

      // Bird can be clearly present in only one of the short windows.
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // BABY CRY
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Baby Crying',
      exactLabels: [
        'baby cry, infant cry',
        'crying, sobbing',
      ],
      minScore: 0.50,
      minPeak: 0.55,
      minMargin: 0.06,
      highConfidence: 0.82,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // SIREN
    //
    // Important:
    // "Alarm" itself is NOT enough.
    //
    // In your tests:
    // Alarm 93.7%
    // Siren 82.4%
    //
    // This family will correctly return Emergency Siren.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Emergency Siren',
      exactLabels: [
        'siren',
        'civil defense siren',
        'police car (siren)',
        'ambulance (siren)',
        'fire engine, fire truck (siren)',
      ],
      minScore: 0.52,
      minPeak: 0.60,
      minMargin: 0.05,
      highConfidence: 0.86,
      requiresPersistence: true,
    ),

    // ----------------------------------------------------------
    // FIRE / SMOKE ALARM
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Fire / Smoke Alarm',
      exactLabels: [
        'fire alarm',
        'smoke detector, smoke alarm',
      ],
      minScore: 0.55,
      minPeak: 0.65,
      minMargin: 0.07,
      highConfidence: 0.88,
      requiresPersistence: true,
    ),

    // ----------------------------------------------------------
    // CAR HORN
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Car Horn',
      exactLabels: [
        'vehicle horn, car horn, honking',
      ],
      minScore: 0.50,
      minPeak: 0.60,
      minMargin: 0.06,
      highConfidence: 0.85,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // GLASS
    // ----------------------------------------------------------

        _FamilyRule(
      label: 'Glass Breaking',

      // Actual YAMNet labels observed on the real phone.
      exactLabels: [
        'glass',
        'shatter',
        'breaking',
        'smash, crash',
      ],

      // Glass breaking is a short transient event.
      //
      // Real phone tests showed:
      // Glass = 50.0%
      // Glass = 33.2%
      // Glass = 26.2%
      // together with Shatter / Breaking / Smash, crash.
      //
      // Therefore we deliberately use a lower threshold than
      // continuous sounds such as Siren.
      minScore: 0.20,
      minPeak: 0.25,

      minMargin: 0.04,

      highConfidence: 0.65,

      // A glass break may exist mainly in one short window.
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // DOORBELL / KNOCK
    // ----------------------------------------------------------

        _FamilyRule(
      label: 'Door Alert',

      // Real labels detected by YAMNet
      // from the phone during the doorbell tests.
      exactLabels: [
        'doorbell',
        'ding-dong',
        'bell',
        'chime',
        'ding',
      ],

      // Doorbells are short transient sounds.
      //
      // Real phone tests produced:
      // Bell     = 10.9%
      // Chime    = 5.9%
      // Doorbell = 4.3%
      //
      // Therefore this family intentionally uses
      // a lower threshold than continuous sounds.
      minScore: 0.03,
      minPeak: 0.04,

      minMargin: 0.02,
      highConfidence: 0.25,

      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // HUMAN SCREAM
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Human Scream',
      exactLabels: [
        'screaming',
        'shout',
        'yell',
        'children shouting',
      ],
      minScore: 0.50,
      minPeak: 0.60,
      minMargin: 0.06,
      highConfidence: 0.85,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // AIRCRAFT
    //
    // Deliberately strict because your Drone samples sometimes
    // produced Helicopter / Aircraft.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Aircraft',
      exactLabels: [
        'aircraft',
        'aircraft engine',
        'fixed-wing aircraft, airplane',
        'jet engine',
        'helicopter',
      ],
      minScore: 0.60,
      minPeak: 0.70,
      minMargin: 0.08,
      highConfidence: 0.90,
      requiresPersistence: true,
    ),

    // ----------------------------------------------------------
    // DRONE / PROPELLER
    //
    // We ONLY call it Drone/Propeller when YAMNet actually
    // detects propeller evidence.
    //
    // Helicopter alone does NOT become Drone.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Drone / Propeller',
      exactLabels: [
        'propeller, airscrew',
      ],
      minScore: 0.60,
      minPeak: 0.70,
      minMargin: 0.08,
      highConfidence: 0.90,
      requiresPersistence: true,
    ),

    // ----------------------------------------------------------
    // EXPLOSION
    //
    // Strict on purpose. Your real phone Explosion test was weak,
    // so we prefer Uncertain instead of a false danger alert.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Explosion',
      exactLabels: [
        'explosion',
        'boom',
        'fireworks',
        'firecracker',
      ],
      minScore: 0.50,
      minPeak: 0.65,
      minMargin: 0.07,
      highConfidence: 0.88,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // GUNSHOT
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Gunshot',
      exactLabels: [
        'gunshot, gunfire',
        'machine gun',
        'fusillade',
        'artillery fire',
      ],
      minScore: 0.52,
      minPeak: 0.65,
      minMargin: 0.07,
      highConfidence: 0.88,
      requiresPersistence: false,
    ),

    // ----------------------------------------------------------
    // SPEECH
    //
    // Higher threshold because your Drone / Explosion tests
    // sometimes produced weak Speech predictions.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Speech',
      exactLabels: [
        'speech',
        'conversation',
        'narration, monologue',
      ],
      minScore: 0.72,
      minPeak: 0.78,
      minMargin: 0.10,
      highConfidence: 0.92,
      requiresPersistence: true,
    ),

    // ----------------------------------------------------------
    // MUSIC
    //
    // Also deliberately strict because Drone playback produced
    // Music 50-71% in your real test.
    // ----------------------------------------------------------

    _FamilyRule(
      label: 'Music',
      exactLabels: [
        'music',
        'singing',
      ],
      minScore: 0.78,
      minPeak: 0.85,
      minMargin: 0.10,
      highConfidence: 0.93,
      requiresPersistence: true,
    ),
  ];

  // ============================================================
  // LOAD MODEL
  // ============================================================

  Future<void> loadModel() async {
    if (isLoaded) {
      return;
    }

    _lastLoadError = null;

    try {
      debugPrint(
        '==================================================',
      );

      debugPrint(
        'PRESENTATION AI: loading YAMNet...',
      );

      // ========================================================
      // LABELS
      // ========================================================

      final csvText =
          await rootBundle.loadString(
        labelsPath,
      );

      final rows =
          const CsvToListConverter().convert(
        csvText,
      );

      _labels = rows
          .skip(1)
          .where(
            (row) => row.length >= 3,
          )
          .map(
            (row) =>
                row[2]
                    .toString()
                    .trim(),
          )
          .where(
            (label) =>
                label.isNotEmpty,
          )
          .toList();

      if (_labels.length != classCount) {
        throw StateError(
          'Expected $classCount YAMNet labels, '
          'loaded ${_labels.length}.',
        );
      }

      _normalizedLabels = _labels
          .map(
            (label) =>
                label
                    .trim()
                    .toLowerCase(),
          )
          .toList();

      // ========================================================
      // MODEL
      // ========================================================

      final options =
          InterpreterOptions()
            ..threads = 4;

      _interpreter =
          await Interpreter.fromAsset(
        modelPath,
        options: options,
      );

      debugPrint(
        'PRESENTATION AI INPUT = '
        '${_interpreter!.getInputTensors().first.shape}',
      );

      debugPrint(
        'PRESENTATION AI OUTPUT = '
        '${_interpreter!.getOutputTensors().first.shape}',
      );

      debugPrint(
        'PRESENTATION AI: READY',
      );

      debugPrint(
        '==================================================',
      );
    } catch (error,stackTrace) {
      _lastLoadError =
          error.toString();

      debugPrint(
        'PRESENTATION AI LOAD ERROR: '
        '$error',
      );

      debugPrintStack(
        stackTrace: stackTrace,
      );

      dispose();

      rethrow;
    }
  }

  // ============================================================
  // MAIN ANALYSIS
  // ============================================================

  SoundPrediction analyzeAudio(
    List<double> samples,
  ) {
    if (!isLoaded) {
      throw StateError(
        _lastLoadError ??
            'AI model is not ready.',
      );
    }

    if (samples.isEmpty) {
      return _uncertain(
        'No sound detected',
      );
    }

    final timer =
        Stopwatch()
          ..start();

    // ========================================================
    // NORMALIZE INPUT
    // ========================================================

    final normalized =
        List<double>.generate(
      samples.length,
      (index) =>
          samples[index]
              .clamp(
                -1.0,
                1.0,
              )
              .toDouble(),
      growable: false,
    );

    final audioRms =
        _calculateRms(
      normalized,
    );

    debugPrint(
      'PRESENTATION RMS = '
      '${audioRms.toStringAsFixed(5)}',
    );

    // Do not reject normal room audio too early.
    // Family rejection below is the main protection.
    if (audioRms < 0.0060) {
      timer.stop();

      return _uncertain(
        'No significant sound detected',
      );
    }

    // ========================================================
    // SELECT ONLY STRONGEST AUDIO REGIONS
    // ========================================================

    final windows =
        _selectStrongestWindows(
      normalized,
    );

    if (windows.isEmpty) {
      timer.stop();

      return _uncertain(
        'Uncertain sound',
      );
    }

    debugPrint(
      'PRESENTATION WINDOWS = '
      '${windows.length}',
    );

    final allScores =
        <List<double>>[];

    // ========================================================
    // YAMNET INFERENCE
    // ========================================================

    for (
      int index = 0;
      index < windows.length;
      index++
    ) {
      final inferenceTimer =
          Stopwatch()
            ..start();

      final scores =
          _runModel(
        windows[index].samples,
      );

      inferenceTimer.stop();

      allScores.add(
        scores,
      );

      final top =
          _topResults(
        scores,
        7,
      );

      debugPrint(
        'PRESENTATION WINDOW ${index + 1} '
        'RMS=${windows[index].energy.toStringAsFixed(4)} '
        'AI=${inferenceTimer.elapsedMilliseconds}ms',
      );

      debugPrint(
        'RAW TOP ${index + 1}: '
        '${top.map(
              (result) =>
                  '${result.label} '
                  '${(result.score * 100).toStringAsFixed(1)}%',
            ).join(' | ')}',
      );
    }

    // ========================================================
    // FAMILY EVIDENCE
    // ========================================================

    final candidates =
        <_FamilyCandidate>[];

    for (
      final rule
          in _rules
    ) {
      final candidate =
          _evaluateFamily(
        rule,
        allScores,
      );

      candidates.add(
        candidate,
      );
    }

    candidates.sort(
      (a, b) =>
          b.score.compareTo(
        a.score,
      ),
    );

    debugPrint(
      '--------------------------------------------------',
    );

    debugPrint(
      'FAMILY TOP: '
      '${candidates.take(6).map(
            (candidate) =>
                '${candidate.rule.label} '
                '${(candidate.score * 100).toStringAsFixed(1)}% '
                '[peak ${(candidate.peak * 100).toStringAsFixed(1)}%]',
          ).join(' | ')}',
    );

    // ========================================================
    // KEEP ONLY FAMILIES THAT PASS THEIR OWN RULES
    // ========================================================

    final acceptedCandidates =
        candidates
            .where(
              (candidate) =>
                  _passesBasicRules(
                candidate,
                allScores.length,
              ),
            )
            .toList();

    if (acceptedCandidates.isEmpty) {
      timer.stop();

      debugPrint(
        'PRESENTATION FINAL = '
        'Uncertain sound',
      );

      debugPrint(
        'PRESENTATION TOTAL = '
        '${timer.elapsedMilliseconds}ms',
      );

      debugPrint(
        '==================================================',
      );

      return _uncertain(
        'Uncertain sound',
      );
    }

    acceptedCandidates.sort(
      (a, b) =>
          b.score.compareTo(
        a.score,
      ),
    );

    final best =
        acceptedCandidates.first;

    final second =
        acceptedCandidates.length > 1
            ? acceptedCandidates[1]
            : null;

    final margin =
        second == null
            ? best.score
            : best.score -
                second.score;

    debugPrint(
      'BEST FAMILY = '
      '${best.rule.label} '
      'score=${best.score.toStringAsFixed(3)} '
      'peak=${best.peak.toStringAsFixed(3)} '
      'mean=${best.mean.toStringAsFixed(3)} '
      'support=${best.support}/${allScores.length} '
      'margin=${margin.toStringAsFixed(3)}',
    );

    // ========================================================
    // FINAL FAMILY-VS-FAMILY AMBIGUITY REJECTION
    // ========================================================

    if (second != null &&
        margin <
            best.rule.minMargin &&
        best.score <
            best.rule.highConfidence) {
      timer.stop();

      debugPrint(
        'PRESENTATION REJECTED: '
        'two supported sounds are too close.',
      );

      return _uncertain(
        'Uncertain sound',
      );
    }

    timer.stop();

    debugPrint(
      '==================================================',
    );

    debugPrint(
      'PRESENTATION FINAL = '
      '${best.rule.label} '
      '${(best.score * 100).toStringAsFixed(1)}%',
    );

    debugPrint(
      'PRESENTATION TOTAL = '
      '${timer.elapsedMilliseconds}ms',
    );

    debugPrint(
      '==================================================',
    );

    return SoundPrediction(
      label:
          best.rule.label,
      confidence:
          best.score,
      severity:
          classifySeverity(
        best.rule.label,
      ),
      detectedAt:
          DateTime.now(),
      isReliable:
          true,
    );
  }

  // ============================================================
  // COMPATIBILITY WITH OLDER PAGE
  // ============================================================

  String predictSound(
    List<double> samples,
  ) {
    return analyzeAudio(
      samples,
    ).label;
  }

  // ============================================================
  // FAMILY EVALUATION
  // ============================================================

  _FamilyCandidate _evaluateFamily(
    _FamilyRule rule,
    List<List<double>> allScores,
  ) {
    final windowEvidence =
        <double>[];

    for (
      final scores
          in allScores
    ) {
      double strongest =
          0.0;

      for (
        int classIndex = 0;
        classIndex < classCount;
        classIndex++
      ) {
        final normalizedLabel =
            _normalizedLabels[
          classIndex
        ];

        if (!rule.exactLabels.contains(
          normalizedLabel,
        )) {
          continue;
        }

        final score =
            scores[
          classIndex
        ];

        if (score >
            strongest) {
          strongest =
              score;
        }
      }

      windowEvidence.add(
        strongest,
      );
    }

    if (windowEvidence.isEmpty) {
      return _FamilyCandidate(
        rule:
            rule,
        score:
            0.0,
        peak:
            0.0,
        mean:
            0.0,
        support:
            0,
      );
    }

    final peak =
        windowEvidence.reduce(
      max,
    );

    final mean =
        windowEvidence.fold<double>(
              0.0,
              (sum, value) =>
                  sum + value,
            ) /
            windowEvidence.length;

    // Peak matters because some important sounds are transient.
    // Mean matters because repeated evidence is safer.
    final score =
        (
          peak * 0.65 +
          mean * 0.35
        ).clamp(
          0.0,
          1.0,
        ).toDouble();

    final supportThreshold =
        max(
      0.12,
      rule.minPeak * 0.40,
    );

    int support =
        0;

    for (
      final evidence
          in windowEvidence
    ) {
      if (evidence >=
          supportThreshold) {
        support++;
      }
    }

    return _FamilyCandidate(
      rule:
          rule,
      score:
          score,
      peak:
          peak,
      mean:
          mean,
      support:
          support,
    );
  }

  // ============================================================
  // BASIC ACCEPTANCE
  // ============================================================

  bool _passesBasicRules(
    _FamilyCandidate candidate,
    int windowCount,
  ) {
    final rule =
        candidate.rule;

    if (candidate.score <
        rule.minScore) {
      return false;
    }

    if (candidate.peak <
        rule.minPeak) {
      return false;
    }

    if (rule.requiresPersistence &&
        windowCount > 1) {
      // Normally require evidence in at least two windows.
      //
      // But if one window is exceptionally strong,
      // do not miss the sound completely.
      if (candidate.support < 2 &&
          candidate.peak <
              rule.highConfidence) {
        return false;
      }
    }

    return true;
  }

  // ============================================================
  // STRONGEST WINDOW SELECTION
  // ============================================================

  List<_AudioWindow>
      _selectStrongestWindows(
    List<double> audio,
  ) {
    if (audio.length <=
        inputLength) {
      final window =
          _padOrTrim(
        audio,
      );

      return [
        _AudioWindow(
          samples:
              window,
          energy:
              _calculateRms(
            window,
          ),
          start:
              0,
        ),
      ];
    }

    final hop =
        inputLength ~/ 2;

    final candidates =
        <_AudioWindow>[];

    int start =
        0;

    while (
        start < audio.length) {
      final remaining =
          audio.length -
              start;

      if (remaining <
          inputLength ~/ 2) {
        break;
      }

      final end =
          min(
        start + inputLength,
        audio.length,
      );

      final window =
          _padOrTrim(
        audio.sublist(
          start,
          end,
        ),
      );

      candidates.add(
        _AudioWindow(
          samples:
              window,
          energy:
              _calculateRms(
            window,
          ),
          start:
              start,
        ),
      );

      start += hop;
    }

    if (candidates.isEmpty) {
      final window =
          _padOrTrim(
        audio,
      );

      return [
        _AudioWindow(
          samples:
              window,
          energy:
              _calculateRms(
            window,
          ),
          start:
              0,
        ),
      ];
    }

    candidates.sort(
      (a, b) =>
          b.energy.compareTo(
        a.energy,
      ),
    );

    final selected =
        <_AudioWindow>[
      candidates.first,
    ];

    for (
      int index = 1;
      index < candidates.length;
      index++
    ) {
      final candidate =
          candidates[index];

      final distance =
          (
            candidate.start -
            selected.first.start
          ).abs();

      if (distance <
          inputLength ~/ 2) {
        continue;
      }

      // Ignore a second region that is almost silent
      // compared with the strongest region.
      if (candidate.energy <
          selected.first.energy *
              0.25) {
        continue;
      }

      selected.add(
        candidate,
      );

      break;
    }

    return selected
        .take(2)
        .toList();
  }

  // ============================================================
  // PAD / TRIM
  // ============================================================

  List<double> _padOrTrim(
    List<double> audio,
  ) {
    if (audio.length ==
        inputLength) {
      return List<double>.from(
        audio,
      );
    }

    if (audio.length >
        inputLength) {
      return List<double>.from(
        audio.sublist(
          0,
          inputLength,
        ),
      );
    }

    final result =
        List<double>.filled(
      inputLength,
      0.0,
    );

    for (
      int index = 0;
      index < audio.length;
      index++
    ) {
      result[index] =
          audio[index];
    }

    return result;
  }

  // ============================================================
  // YAMNET
  // ============================================================

  List<double> _runModel(
    List<double> audio,
  ) {
    final interpreter =
        _interpreter;

    if (interpreter == null) {
      throw StateError(
        'YAMNet is not loaded.',
      );
    }

    if (audio.length !=
        inputLength) {
      throw ArgumentError(
        'Expected $inputLength samples.',
      );
    }

    final input =
        Float32List.fromList(
      audio,
    );

    final output =
        List.generate(
      1,
      (_) =>
          List<double>.filled(
        classCount,
        0.0,
      ),
    );

    interpreter.run(
      input,
      output,
    );

    return output.first;
  }

  // ============================================================
  // DEBUG TOP RESULTS
  // ============================================================

  List<_ScoreResult> _topResults(
    List<double> scores,
    int count,
  ) {
    final indexes =
        List<int>.generate(
      min(
        scores.length,
        _labels.length,
      ),
      (index) =>
          index,
    );

    indexes.sort(
      (a, b) =>
          scores[b].compareTo(
        scores[a],
      ),
    );

    return indexes
        .take(count)
        .map(
          (index) =>
              _ScoreResult(
            label:
                _labels[index],
            score:
                scores[index]
                    .clamp(
                      0.0,
                      1.0,
                    )
                    .toDouble(),
          ),
        )
        .toList();
  }

  // ============================================================
  // SEVERITY
  // ============================================================

  AlertSeverity classifySeverity(
    String label,
  ) {
    final normalized =
        label
            .trim()
            .toLowerCase();

    const critical = [
      'explosion',
      'gunshot',
      'fire / smoke alarm',
      'glass breaking',
    ];

    const warning = [
      'emergency siren',
      'aircraft',
      'drone / propeller',
      'dog barking',
      'baby crying',
      'human scream',
      'door alert',
      'car horn',
    ];

    for (
      final value
          in critical
    ) {
      if (normalized.contains(
        value,
      )) {
        return AlertSeverity.critical;
      }
    }

    for (
      final value
          in warning
    ) {
      if (normalized.contains(
        value,
      )) {
        return AlertSeverity.warning;
      }
    }

    return AlertSeverity.normal;
  }

  // ============================================================
  // RMS
  // ============================================================

  double _calculateRms(
    List<double> samples,
  ) {
    if (samples.isEmpty) {
      return 0.0;
    }

    double sum =
        0.0;

    for (
      final sample
          in samples
    ) {
      sum +=
          sample * sample;
    }

    return sqrt(
      sum /
          samples.length,
    );
  }

  // ============================================================
  // UNCERTAIN
  // ============================================================

  SoundPrediction _uncertain(
    String label,
  ) {
    return SoundPrediction(
      label:
          label,
      confidence:
          0.0,
      severity:
          AlertSeverity.normal,
      detectedAt:
          DateTime.now(),
      isReliable:
          false,
    );
  }

  // ============================================================
  // DISPOSE
  // ============================================================

  void dispose() {
    try {
      _interpreter
          ?.close();
    } catch (_) {}

    _interpreter =
        null;

    _labels = [];
    _normalizedLabels = [];
  }
}

// ================================================================
// INTERNAL MODELS
// ================================================================

class _FamilyRule {
  final String label;

  final List<String>
      exactLabels;

  final double minScore;
  final double minPeak;
  final double minMargin;
  final double highConfidence;

  final bool
      requiresPersistence;

  const _FamilyRule({
    required this.label,
    required this.exactLabels,
    required this.minScore,
    required this.minPeak,
    required this.minMargin,
    required this.highConfidence,
    required this.requiresPersistence,
  });
}

class _FamilyCandidate {
  final _FamilyRule rule;

  final double score;
  final double peak;
  final double mean;

  final int support;

  const _FamilyCandidate({
    required this.rule,
    required this.score,
    required this.peak,
    required this.mean,
    required this.support,
  });
}

class _AudioWindow {
  final List<double> samples;

  final double energy;

  final int start;

  const _AudioWindow({
    required this.samples,
    required this.energy,
    required this.start,
  });
}

class _ScoreResult {
  final String label;
  final double score;

  const _ScoreResult({
    required this.label,
    required this.score,
  });
}