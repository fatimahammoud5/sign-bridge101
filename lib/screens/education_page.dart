import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'education_lesson_page.dart';

class EducationPage extends StatefulWidget {
  const EducationPage({super.key});

  @override
  State<EducationPage> createState() => _EducationPageState();
}

class _EducationPageState extends State<EducationPage> {
  static const Color pageBackground = Color(0xFFF8F7FC);

  bool loading = true;

  final Map<int, bool> completed = {};
  final Map<int, bool> unlocked = {};
  final Map<int, double> progress = {};

  // ============================================================
  // LEVEL COLORS
  // ============================================================

  static const List<_LevelPalette> palettes = [
    // LEVEL 1 - BLUE
    _LevelPalette(
      cardStart: Color(0xFFEAF7FF),
      cardEnd: Color(0xFFC8ECFF),
      panelStart: Color(0xFF45A2F3),
      panelEnd: Color(0xFF72C4F5),
      accent: Color(0xFF368FDF),
      border: Color(0xFFAFDBF5),
    ),

    // LEVEL 2 - ORANGE
    _LevelPalette(
      cardStart: Color(0xFFFFF3EC),
      cardEnd: Color(0xFFFFDDD0),
      panelStart: Color(0xFFFF8D62),
      panelEnd: Color(0xFFFFAD79),
      accent: Color(0xFFF06F46),
      border: Color(0xFFF7C9B5),
    ),

    // LEVEL 3 - PURPLE
    _LevelPalette(
      cardStart: Color(0xFFF4EEFF),
      cardEnd: Color(0xFFE3D7FF),
      panelStart: Color(0xFF8B72E7),
      panelEnd: Color(0xFFB094F6),
      accent: Color(0xFF765AD0),
      border: Color(0xFFD5C5F7),
    ),

    // LEVEL 4 - GREEN
    _LevelPalette(
      cardStart: Color(0xFFE9FAF5),
      cardEnd: Color(0xFFCAF1E5),
      panelStart: Color(0xFF36B99C),
      panelEnd: Color(0xFF67D3B6),
      accent: Color(0xFF259D84),
      border: Color(0xFFB5E5D8),
    ),

    // LEVEL 5 - GOLD
    _LevelPalette(
      cardStart: Color(0xFFFFF8E7),
      cardEnd: Color(0xFFFFEAB7),
      panelStart: Color(0xFFF4B447),
      panelEnd: Color(0xFFFFCE69),
      accent: Color(0xFFD99A2E),
      border: Color(0xFFF1D99B),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _loadProgress();
  }

  // ============================================================
  // LOAD PROGRESS
  // ============================================================

  Future<void> _loadProgress() async {
    final prefs = await SharedPreferences.getInstance();

    final newCompleted = <int, bool>{};
    final newUnlocked = <int, bool>{1: true};
    final newProgress = <int, double>{};

    for (final level in educationLevels) {
      final number = level.level;

      newCompleted[number] =
          prefs.getBool('edu_l${number}_completed_once') ??
              prefs.getBool('l${number}_completed_once') ??
              false;

      if (number == 1) {
        newUnlocked[number] = true;
      } else {
        newUnlocked[number] =
            prefs.getBool('edu_l${number}_unlocked') ??
                prefs.getBool('l${number}_unlocked') ??
                false;
      }

      newProgress[number] = _calculateProgress(
        prefs,
        level,
      );
    }

    if (!mounted) return;

    setState(() {
      completed
        ..clear()
        ..addAll(newCompleted);

      unlocked
        ..clear()
        ..addAll(newUnlocked);

      progress
        ..clear()
        ..addAll(newProgress);

      loading = false;
    });
  }

  // ============================================================
  // CALCULATE PROGRESS
  // ============================================================

  double _calculateProgress(
    SharedPreferences prefs,
    EducationLevelContent level,
  ) {
    final prefix = 'edu_l${level.level}';

    final stage = (prefs.getInt('${prefix}_stage') ?? 0)
        .clamp(0, 4)
        .toInt();

    // Completed
    if (stage == 4) {
      return 1.0;
    }

    final learnCount = level.learnItems.length;
    final guessCount = level.guessItems.length;

    const challengeCount = 3;

    final totalPool = learnCount + guessCount;

    final finalCount =
        totalPool < 5 ? totalPool : 5;

    final total =
        learnCount +
        guessCount +
        challengeCount +
        finalCount;

    if (total <= 0) {
      return 0.0;
    }

    final learnIndex = learnCount > 0
        ? (prefs.getInt('${prefix}_learn_index') ?? 0)
            .clamp(
              0,
              learnCount - 1,
            )
            .toInt()
        : 0;

    final guessIndex = guessCount > 0
        ? (prefs.getInt('${prefix}_guess_index') ?? 0)
            .clamp(
              0,
              guessCount - 1,
            )
            .toInt()
        : 0;

    final challengeIndex =
        (prefs.getInt('${prefix}_challenge_index') ?? 0)
            .clamp(
              0,
              challengeCount - 1,
            )
            .toInt();

    final finalIndex = finalCount > 0
        ? (prefs.getInt('${prefix}_final_index') ?? 0)
            .clamp(
              0,
              finalCount - 1,
            )
            .toInt()
        : 0;

    int done = 0;

    switch (stage) {
      case 0:
        done = learnIndex;
        break;

      case 1:
        done =
            learnCount +
            guessIndex;
        break;

      case 2:
        done =
            learnCount +
            guessCount +
            challengeIndex;
        break;

      case 3:
        done =
            learnCount +
            guessCount +
            challengeCount +
            finalIndex;
        break;
    }

    return (done / total)
        .clamp(0.0, 1.0)
        .toDouble();
  }

  // ============================================================
  // OPEN LEVEL
  // ============================================================

  Future<void> _openLevel(
    EducationLevelContent level,
  ) async {
    final isUnlocked =
        unlocked[level.level] ?? false;

    if (!isUnlocked) {
      return;
    }

    await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => EducationLessonPage(
          content: level,
        ),
      ),
    );

    await _loadProgress();
  }

  // ============================================================
  // PAGE
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: pageBackground,
      body: SafeArea(
        child: loading
            ? const Center(
                child: CircularProgressIndicator(),
              )
            : RefreshIndicator(
                onRefresh: _loadProgress,
                child: ListView(
                  physics:
                      const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.only(
                    bottom: 35,
                  ),
                  children: [
                    _buildHeader(),

                    const SizedBox(height: 24),

                    _buildJourney(),
                  ],
                ),
              ),
      ),
    );
  }

  // ============================================================
  // HEADER
  // ============================================================

  Widget _buildHeader() {
    final completedCount = educationLevels
        .where(
          (level) =>
              completed[level.level] ?? false,
        )
        .length;

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        20,
        22,
        20,
        4,
      ),
      child: Container(
        width: double.infinity,
        height: 174,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF6759DC)
                  .withOpacity(0.18),
              blurRadius: 24,
              offset: const Offset(0, 9),
            ),
          ],
        ),
        child: Stack(
          children: [
            // MAIN PURPLE GRADIENT
            const Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFF6759E8),
                      Color(0xFF7766EC),
                      Color(0xFF8E7CF1),
                    ],
                  ),
                ),
              ),
            ),

            // BLUE WAVE
            Positioned(
              left: -80,
              bottom: -105,
              child: Container(
                width: 310,
                height: 210,
                decoration: BoxDecoration(
                  color: const Color(0xFF55B6F2)
                      .withOpacity(0.33),
                  borderRadius:
                      const BorderRadius.only(
                    topRight: Radius.elliptical(
                      210,
                      130,
                    ),
                    topLeft: Radius.elliptical(
                      100,
                      70,
                    ),
                  ),
                ),
              ),
            ),

            // ORANGE WAVE
            Positioned(
              right: -95,
              top: -80,
              child: Container(
                width: 280,
                height: 195,
                decoration: BoxDecoration(
                  color: const Color(0xFFFF8E73)
                      .withOpacity(0.26),
                  borderRadius:
                      const BorderRadius.only(
                    bottomLeft: Radius.elliptical(
                      210,
                      130,
                    ),
                  ),
                ),
              ),
            ),

            // SOFT DECORATIVE CIRCLE
            Positioned(
              right: 24,
              bottom: -38,
              child: Container(
                width: 125,
                height: 125,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color:
                      Colors.white.withOpacity(
                    0.07,
                  ),
                ),
              ),
            ),

            // CONTENT
            Padding(
              padding: const EdgeInsets.fromLTRB(
                20,
                20,
                18,
                18,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment:
                          CrossAxisAlignment.start,
                      mainAxisAlignment:
                          MainAxisAlignment.center,
                      children: [
                        Container(
                          padding:
                              const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white
                                .withOpacity(0.15),
                            borderRadius:
                                BorderRadius.circular(
                              20,
                            ),
                          ),
                          child: const Row(
                            mainAxisSize:
                                MainAxisSize.min,
                            children: [
                              Text(
                                '🤟',
                                style: TextStyle(
                                  fontSize: 18,
                                ),
                              ),
                              SizedBox(width: 6),
                              Text(
                                'ASL EDUCATION',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  letterSpacing: 1,
                                  fontWeight:
                                      FontWeight.w900,
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 12),

                        const Text(
                          'Your Learning Journey',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 25,
                            height: 1.08,
                            fontWeight:
                                FontWeight.w900,
                          ),
                        ),

                        const SizedBox(height: 7),

                        const Text(
                          'Learn visually • Practice • Progress',
                          style: TextStyle(
                            color:
                                Color(0xFFEDEAFF),
                            fontSize: 13,
                            fontWeight:
                                FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 14),

                  Container(
                    width: 72,
                    height: 72,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: Colors.white
                          .withOpacity(0.16),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white
                            .withOpacity(0.22),
                      ),
                    ),
                    child: Column(
                      mainAxisAlignment:
                          MainAxisAlignment.center,
                      children: [
                        Text(
                          '$completedCount',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 23,
                            height: 1,
                            fontWeight:
                                FontWeight.w900,
                          ),
                        ),

                        const SizedBox(height: 3),

                        Text(
                          'of ${educationLevels.length}',
                          style: const TextStyle(
                            color:
                                Color(0xFFE9E6FF),
                            fontSize: 10,
                            fontWeight:
                                FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // JOURNEY
  // ============================================================

  Widget _buildJourney() {
    final totalCards =
        educationLevels.length + 1;

    return CustomPaint(
      painter: _JourneyPathPainter(
        count: totalCards,
      ),
      child: Column(
        children: [
          for (int index = 0;
              index < educationLevels.length;
              index++)
            _journeyPosition(
              index: index,
              child: _buildLevelCard(
                educationLevels[index],
                palettes[index],
              ),
            ),

          _journeyPosition(
            index: educationLevels.length,
            isLast: true,
            child: _buildLevel5Card(
              palettes[4],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // ALTERNATING POSITION
  // ============================================================

  Widget _journeyPosition({
    required int index,
    required Widget child,
    bool isLast = false,
  }) {
    final leftSide =
        index.isEven;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.only(
        left:
            leftSide ? 20 : 70,
        right:
            leftSide ? 70 : 20,
        bottom:
            isLast ? 10 : 46,
      ),
      child: child,
    );
  }

  // ============================================================
  // LEVEL CARD
  //
  // ONLY:
  // 1. LEVEL NAME
  // 2. PROGRESS BAR
  // 3. VISUAL ICON / LOCK
  // ============================================================

  Widget _buildLevelCard(
    EducationLevelContent level,
    _LevelPalette palette,
  ) {
    final isUnlocked =
        unlocked[level.level] ?? false;

    final isCompleted =
        completed[level.level] ?? false;

    final levelProgress =
        isCompleted
            ? 1.0
            : progress[level.level] ??
                0.0;

    return InkWell(
      onTap: isUnlocked
          ? () => _openLevel(level)
          : null,
      borderRadius:
          BorderRadius.circular(30),
      child: Container(
        height: 155,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isUnlocked
                ? [
                    palette.cardStart,
                    palette.cardEnd,
                  ]
                : [
                    Color.lerp(
                      palette.cardStart,
                      const Color(
                        0xFFE8E8EC,
                      ),
                      0.55,
                    )!,
                    Color.lerp(
                      palette.cardEnd,
                      const Color(
                        0xFFF1F1F4,
                      ),
                      0.68,
                    )!,
                  ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius:
              BorderRadius.circular(30),
          border: Border.all(
            color: isUnlocked
                ? palette.border
                : const Color(
                    0xFFD9DAE0,
                  ),
            width: 1.4,
          ),
          boxShadow: [
            BoxShadow(
              color: palette.accent
                  .withOpacity(
                isUnlocked
                    ? 0.12
                    : 0.04,
              ),
              blurRadius: 22,
              offset:
                  const Offset(
                0,
                9,
              ),
            ),
          ],
        ),
        child: Stack(
          children: [
            // DECORATIVE CIRCLE
            Positioned(
              right: -35,
              bottom: -60,
              child: Container(
                width: 160,
                height: 160,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: palette.accent
                      .withOpacity(
                    isUnlocked
                        ? 0.065
                        : 0.025,
                  ),
                ),
              ),
            ),

            Padding(
              padding:
                  const EdgeInsets.all(
                18,
              ),
              child: Row(
                children: [
                  // ==========================================
                  // ICON PANEL
                  // ==========================================

                  Container(
                    width: 82,
                    height:
                        double.infinity,
                    alignment:
                        Alignment.center,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: isUnlocked
                            ? [
                                palette.panelStart,
                                palette.panelEnd,
                              ]
                            : [
                                const Color(
                                  0xFFA6ABB4,
                                ),
                                const Color(
                                  0xFF858C98,
                                ),
                              ],
                        begin:
                            Alignment.topLeft,
                        end:
                            Alignment.bottomRight,
                      ),
                      borderRadius:
                          BorderRadius.circular(
                        23,
                      ),
                    ),
                    child: isUnlocked
                        ? Text(
                            level.emoji,
                            style:
                                const TextStyle(
                              fontSize: 38,
                            ),
                          )
                        : const Icon(
                            Icons.lock_rounded,
                            size: 35,
                            color:
                                Colors.white,
                          ),
                  ),

                  const SizedBox(
                    width: 18,
                  ),

                  // ==========================================
                  // ONLY NAME + PROGRESS
                  // ==========================================

                  Expanded(
                    child: Column(
                      crossAxisAlignment:
                          CrossAxisAlignment.start,
                      mainAxisAlignment:
                          MainAxisAlignment.center,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                level.title,
                                maxLines: 2,
                                overflow:
                                    TextOverflow
                                        .ellipsis,
                                style: TextStyle(
                                  fontSize: 21,
                                  height: 1.1,
                                  fontWeight:
                                      FontWeight
                                          .w900,
                                  color: isUnlocked
                                      ? const Color(
                                          0xFF202A42,
                                        )
                                      : const Color(
                                          0xFF777C86,
                                        ),
                                ),
                              ),
                            ),

                            const SizedBox(
                              width: 8,
                            ),

                            if (isCompleted)
                              const Icon(
                                Icons
                                    .check_circle_rounded,
                                color:
                                    Color(
                                  0xFF21A66B,
                                ),
                                size: 27,
                              )
                            else if (isUnlocked)
                              Icon(
                                Icons
                                    .arrow_forward_rounded,
                                color:
                                    palette.accent,
                                size: 27,
                              )
                            else
                              const Icon(
                                Icons
                                    .lock_outline_rounded,
                                color:
                                    Color(
                                  0xFF989CA5,
                                ),
                                size: 24,
                              ),
                          ],
                        ),

                        const SizedBox(
                          height: 25,
                        ),

                        _buildProgressBar(
                          palette:
                              palette,
                          progress:
                              levelProgress,
                          completed:
                              isCompleted,
                          unlocked:
                              isUnlocked,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // PROGRESS BAR
  // ============================================================

  Widget _buildProgressBar({
    required _LevelPalette palette,
    required double progress,
    required bool completed,
    required bool unlocked,
  }) {
    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius:
                BorderRadius.circular(
              50,
            ),
            child:
                LinearProgressIndicator(
              minHeight: 8,
              value:
                  unlocked
                      ? progress
                      : 0,
              backgroundColor:
                  Colors.white
                      .withOpacity(
                0.68,
              ),
              valueColor:
                  AlwaysStoppedAnimation<
                      Color>(
                completed
                    ? const Color(
                        0xFF20A466,
                      )
                    : palette.accent,
              ),
            ),
          ),
        ),

        const SizedBox(
          width: 10,
        ),

        Text(
          '${((unlocked ? progress : 0.0) * 100).round()}%',
          style: TextStyle(
            fontSize: 12,
            color: completed
                ? const Color(
                    0xFF1E9661,
                  )
                : unlocked
                    ? palette.accent
                    : const Color(
                        0xFF999DA6,
                      ),
            fontWeight:
                FontWeight.w900,
          ),
        ),
      ],
    );
  }

  // ============================================================
  // LEVEL 5
  //
  // ALSO ONLY:
  // NAME + PROGRESS BAR
  // ============================================================

  Widget _buildLevel5Card(
    _LevelPalette palette,
  ) {
    return Container(
      height: 155,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Color.lerp(
              palette.cardStart,
              const Color(
                0xFFEAEAEF,
              ),
              0.48,
            )!,
            Color.lerp(
              palette.cardEnd,
              const Color(
                0xFFF1F1F4,
              ),
              0.55,
            )!,
          ],
          begin:
              Alignment.topLeft,
          end:
              Alignment.bottomRight,
        ),
        borderRadius:
            BorderRadius.circular(30),
        border: Border.all(
          color:
              const Color(
            0xFFDEDEE3,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color:
                Colors.black.withOpacity(
              0.03,
            ),
            blurRadius: 18,
            offset:
                const Offset(
              0,
              8,
            ),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            right: -35,
            bottom: -60,
            child: Container(
              width: 160,
              height: 160,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: palette.accent
                    .withOpacity(
                  0.025,
                ),
              ),
            ),
          ),

          Padding(
            padding:
                const EdgeInsets.all(
              18,
            ),
            child: Row(
              children: [
                Container(
                  width: 82,
                  height:
                      double.infinity,
                  alignment:
                      Alignment.center,
                  decoration:
                      BoxDecoration(
                    gradient:
                        const LinearGradient(
                      colors: [
                        Color(
                          0xFFA7ABB3,
                        ),
                        Color(
                          0xFF858B95,
                        ),
                      ],
                      begin:
                          Alignment.topLeft,
                      end:
                          Alignment
                              .bottomRight,
                    ),
                    borderRadius:
                        BorderRadius.circular(
                      23,
                    ),
                  ),
                  child: const Icon(
                    Icons.lock_rounded,
                    color:
                        Colors.white,
                    size: 35,
                  ),
                ),

                const SizedBox(
                  width: 18,
                ),

                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    mainAxisAlignment:
                        MainAxisAlignment.center,
                    children: [
                      const Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Next Topic',
                              style:
                                  TextStyle(
                                color:
                                    Color(
                                  0xFF727781,
                                ),
                                fontSize: 21,
                                fontWeight:
                                    FontWeight
                                        .w900,
                              ),
                            ),
                          ),

                          Icon(
                            Icons
                                .lock_outline_rounded,
                            color:
                                Color(
                              0xFF969AA3,
                            ),
                            size: 24,
                          ),
                        ],
                      ),

                      const SizedBox(
                        height: 25,
                      ),

                      Row(
                        children: [
                          Expanded(
                            child:
                                ClipRRect(
                              borderRadius:
                                  BorderRadius
                                      .circular(
                                50,
                              ),
                              child:
                                  const LinearProgressIndicator(
                                minHeight:
                                    8,
                                value: 0,
                                backgroundColor:
                                    Colors
                                        .white,
                                valueColor:
                                    AlwaysStoppedAnimation<
                                        Color>(
                                  Color(
                                    0xFFAAAEB7,
                                  ),
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(
                            width: 10,
                          ),

                          const Text(
                            '0%',
                            style:
                                TextStyle(
                              color:
                                  Color(
                                0xFF999DA6,
                              ),
                              fontSize: 12,
                              fontWeight:
                                  FontWeight
                                      .w900,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// LEVEL PALETTE
// ============================================================

class _LevelPalette {
  final Color cardStart;
  final Color cardEnd;

  final Color panelStart;
  final Color panelEnd;

  final Color accent;
  final Color border;

  const _LevelPalette({
    required this.cardStart,
    required this.cardEnd,
    required this.panelStart,
    required this.panelEnd,
    required this.accent,
    required this.border,
  });
}

// ============================================================
// WAVY PATH
// ============================================================

class _JourneyPathPainter
    extends CustomPainter {
  final int count;

  const _JourneyPathPainter({
    required this.count,
  });

  @override
  void paint(
    Canvas canvas,
    Size size,
  ) {
    if (count < 2) {
      return;
    }

    // Card height 155 + gap 46
    const double step = 201;

    const double firstY = 77;

    final points = <Offset>[];

    for (int index = 0;
        index < count;
        index++) {
      final left =
          index.isEven;

      points.add(
        Offset(
          left
              ? size.width * 0.78
              : size.width * 0.22,
          firstY +
              index * step,
        ),
      );
    }

    final path = Path();

    path.moveTo(
      points.first.dx,
      points.first.dy,
    );

    for (int index = 0;
        index <
            points.length - 1;
        index++) {
      final current =
          points[index];

      final next =
          points[index + 1];

      final middleY =
          (current.dy +
                  next.dy) /
              2;

      path.cubicTo(
        current.dx,
        middleY,
        next.dx,
        middleY,
        next.dx,
        next.dy,
      );
    }

    // WHITE BASE
    final shadowPaint = Paint()
      ..color =
          Colors.white.withOpacity(
        0.92,
      )
      ..style =
          PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap =
          StrokeCap.round;

    // GLOW
    final glowPaint = Paint()
      ..color =
          const Color(
        0xFF795DF0,
      ).withOpacity(
        0.12,
      )
      ..style =
          PaintingStyle.stroke
      ..strokeWidth = 10
      ..strokeCap =
          StrokeCap.round;

    // COLORFUL PATH
    final pathPaint = Paint()
      ..shader =
          const LinearGradient(
        begin:
            Alignment.topCenter,
        end:
            Alignment.bottomCenter,
        colors: [
          Color(0xFF4FAAF1),
          Color(0xFF7565E8),
          Color(0xFFF28678),
          Color(0xFF8264E7),
          Color(0xFF40BDA3),
        ],
        stops: [
          0.0,
          0.25,
          0.50,
          0.75,
          1.0,
        ],
      ).createShader(
        Rect.fromLTWH(
          0,
          0,
          size.width,
          size.height,
        ),
      )
      ..style =
          PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap =
          StrokeCap.round;

    canvas.drawPath(
      path,
      shadowPaint,
    );

    canvas.drawPath(
      path,
      glowPaint,
    );

    canvas.drawPath(
      path,
      pathPaint,
    );

    // ==========================================================
    // POINT COLORS
    // ==========================================================

    const dotColors = [
      Color(0xFF4FAAF1),
      Color(0xFFF28678),
      Color(0xFF8264E7),
      Color(0xFF40BDA3),
      Color(0xFFF1B348),
    ];

    for (int index = 0;
        index < points.length;
        index++) {
      // WHITE OUTER DOT
      canvas.drawCircle(
        points[index],
        11,
        Paint()
          ..color =
              Colors.white,
      );

      // COLORED INNER DOT
      canvas.drawCircle(
        points[index],
        7,
        Paint()
          ..color =
              dotColors[
                  index %
                      dotColors.length],
      );
    }
  }

  @override
  bool shouldRepaint(
    covariant _JourneyPathPainter oldDelegate,
  ) {
    return oldDelegate.count != count;
  }
}