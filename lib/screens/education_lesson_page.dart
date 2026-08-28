import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:video_player/video_player.dart';

// ============================================================
// MODELS
// ============================================================

class LessonVideoItem {
  final String label;
  final String asset;
  final List<String> visualCues;

  const LessonVideoItem({
    required this.label,
    required this.asset,
    this.visualCues = const [],
  });
}

class EducationLevelContent {
  final int level;
  final String title;
  final String subtitle;
  final String emoji;

  final List<LessonVideoItem> learnItems;
  final List<LessonVideoItem> guessItems;

  const EducationLevelContent({
    required this.level,
    required this.title,
    required this.subtitle,
    required this.emoji,
    required this.learnItems,
    required this.guessItems,
  });
}

class QuizQuestion {
  final LessonVideoItem target;
  final List<String> options;
  final int correctIndex;

  const QuizQuestion({
    required this.target,
    required this.options,
    required this.correctIndex,
  });
}

class ChallengeQuestion {
  final String prompt;
  final List<LessonVideoItem> options;
  final int correctIndex;

  const ChallengeQuestion({
    required this.prompt,
    required this.options,
    required this.correctIndex,
  });
}

// ============================================================
// LEVELS
// ============================================================

const List<EducationLevelContent> educationLevels = [
  // ==========================================================
  // LEVEL 1
  // ==========================================================

  EducationLevelContent(
    level: 1,
    title: 'Everyday Conversations',
    subtitle: 'Greetings, feelings and useful daily phrases',
    emoji: '👋',
    learnItems: [
      LessonVideoItem(
        label: 'Are you ready?',
        asset:
            'assets/videos/education/level1/learn/are_you_ready.mp4',
        visualCues: [
          '🙋',
          '✅',
          '❓',
        ],
      ),
      LessonVideoItem(
        label: 'How are you?',
        asset:
            'assets/videos/education/level1/learn/how_are_you.mp4',
        visualCues: [
          '👋',
          '🙂',
          '❓',
        ],
      ),
      LessonVideoItem(
        label: "I'm happy.",
        asset:
            'assets/videos/education/level1/learn/im_happy.mp4',
        visualCues: [
          '😊',
          '💛',
        ],
      ),
      LessonVideoItem(
        label: 'Hello, nice to meet you.',
        asset:
            'assets/videos/education/level1/learn/hello_nice_to_meet_you.mp4',
        visualCues: [
          '👋',
          '🤝',
          '🙂',
        ],
      ),
      LessonVideoItem(
        label: 'I need help.',
        asset:
            'assets/videos/education/level1/learn/i_need_help.mp4',
        visualCues: [
          '🙋',
          '🆘',
        ],
      ),
      LessonVideoItem(
        label: 'Yeah, same here.',
        asset:
            'assets/videos/education/level1/learn/same_here.mp4',
        visualCues: [
          '👍',
          '🤝',
        ],
      ),
      LessonVideoItem(
        label: 'You finished?',
        asset:
            'assets/videos/education/level1/learn/you_finished.mp4',
        visualCues: [
          '✅',
          '❓',
        ],
      ),
    ],
    guessItems: [
      LessonVideoItem(
        label: 'Please',
        asset:
            'assets/videos/education/level1/predict/please.mp4',
      ),
      LessonVideoItem(
        label: 'Thank you',
        asset:
            'assets/videos/education/level1/predict/thank_you.mp4',
      ),
      LessonVideoItem(
        label: 'Good / Well',
        asset:
            'assets/videos/education/level1/predict/good_well.mp4',
      ),
    ],
  ),

  // ==========================================================
  // LEVEL 2
  // ==========================================================

  EducationLevelContent(
    level: 2,
    title: 'Home & Food',
    subtitle: 'Everyday phrases about home, meals and drinks',
    emoji: '🏠',
    learnItems: [
      LessonVideoItem(
        label: 'The house cleaning is done.',
        asset:
            'assets/videos/education/level2/learn/house_cleaning_done.mp4',
        visualCues: [
          '🏠',
          '🧹',
          '✅',
        ],
      ),
      LessonVideoItem(
        label: 'Do you want some milk and cookies?',
        asset:
            'assets/videos/education/level2/learn/want_milk_and_cookies.mp4',
        visualCues: [
          '🥛',
          '🍪',
          '❓',
        ],
      ),
      LessonVideoItem(
        label: 'I like Sprite.',
        asset:
            'assets/videos/education/level2/learn/i_like_sprite.mp4',
        visualCues: [
          '🥤',
          '❤️',
        ],
      ),
      LessonVideoItem(
        label:
            "I'm done with my hamburger. Now I want some ice cream.",
        asset:
            'assets/videos/education/level2/learn/done_hamburger_want_ice_cream.mp4',
        visualCues: [
          '🍔',
          '✅',
          '➡️',
          '🍦',
        ],
      ),
    ],
    guessItems: [
      LessonVideoItem(
        label: 'Home',
        asset:
            'assets/videos/education/level2/predict/home.mp4',
      ),
      LessonVideoItem(
        label: 'Drink',
        asset:
            'assets/videos/education/level2/predict/drink.mp4',
      ),
      LessonVideoItem(
        label: 'Water',
        asset:
            'assets/videos/education/level2/predict/water.mp4',
      ),
    ],
  ),

  // ==========================================================
  // LEVEL 3
  // ==========================================================

  EducationLevelContent(
    level: 3,
    title: 'School & Colors',
    subtitle: 'School, learning and everyday colors',
    emoji: '🎓',
    learnItems: [
      LessonVideoItem(
        label: "I'm learning ASL.",
        asset:
            'assets/videos/education/level3/learn/im_learning_asl.mp4',
        visualCues: [
          '🤟',
          '📚',
          '🧠',
        ],
      ),
      LessonVideoItem(
        label: 'Can you give me the red book please?',
        asset:
            'assets/videos/education/level3/learn/give_me_red_book_please.mp4',
        visualCues: [
          '🔴',
          '📕',
          '🙏',
        ],
      ),
      LessonVideoItem(
        label: 'My favorite color is Teal.',
        asset:
            'assets/videos/education/level3/learn/favorite_color_teal.mp4',
        visualCues: [
          '❤️',
          '🎨',
          '🩵',
        ],
      ),
    ],
    guessItems: [
      LessonVideoItem(
        label: 'Book',
        asset:
            'assets/videos/education/level3/predict/book.mp4',
      ),
      LessonVideoItem(
        label: 'Blue',
        asset:
            'assets/videos/education/level3/predict/blue.mp4',
      ),
      LessonVideoItem(
        label: 'Teacher',
        asset:
            'assets/videos/education/level3/predict/teacher.mp4',
      ),
    ],
  ),

  // ==========================================================
  // LEVEL 4
  // ==========================================================

  EducationLevelContent(
    level: 4,
    title: 'Animals',
    subtitle: 'Animal signs and simple animal conversations',
    emoji: '🐾',
    learnItems: [
      LessonVideoItem(
        label: "What's your favorite animal?",
        asset:
            'assets/videos/education/level4/learn/favorite_animal.mp4',
        visualCues: [
          '❤️',
          '🐾',
          '❓',
        ],
      ),
      LessonVideoItem(
        label:
            'I saw so many birds on my walk around the lake.',
        asset:
            'assets/videos/education/level4/learn/birds_on_my_walk.mp4',
        visualCues: [
          '🐦',
          '🚶',
          '🌊',
        ],
      ),
      LessonVideoItem(
        label:
            'Wow! When I went to the Zoo I heard a Lion roaring.',
        asset:
            'assets/videos/education/level4/learn/lion_at_the_zoo.mp4',
        visualCues: [
          '🦁',
          '🦒',
          '📣',
        ],
      ),
    ],
    guessItems: [
      LessonVideoItem(
        label: 'Cat',
        asset:
            'assets/videos/education/level4/predict/cat.mp4',
      ),
      LessonVideoItem(
        label: 'Dog',
        asset:
            'assets/videos/education/level4/predict/dog.mp4',
      ),
      LessonVideoItem(
        label: 'Fish',
        asset:
            'assets/videos/education/level4/predict/fish.mp4',
      ),
    ],
  ),
];

// ============================================================
// STAGES
// ============================================================

enum LessonStage {
  learn,
  guess,
  challenge,
  finalQuiz,
  completed,
}

// ============================================================
// PAGE
// ============================================================

class EducationLessonPage extends StatefulWidget {
  final EducationLevelContent content;

  const EducationLessonPage({
    super.key,
    required this.content,
  });

  @override
  State<EducationLessonPage> createState() =>
      _EducationLessonPageState();
}

class _EducationLessonPageState
    extends State<EducationLessonPage> {
  static const Color primary =
      Color(0xFF6C63FF);

  static const Color softPrimary =
      Color(0xFFF0EFFF);

  static const Color background =
      Color(0xFFF8F8FC);

  SharedPreferences? prefs;

  VideoPlayerController? controller;

  LessonStage stage = LessonStage.learn;

  int furthestStage = 0;

  int learnIndex = 0;
  int guessIndex = 0;
  int challengeIndex = 0;
  int finalIndex = 0;

  int guessScore = 0;
  int challengeScore = 0;
  int finalScore = 0;

  int? selectedAnswer;

  bool answerLocked = false;

  bool loadingVideo = true;
  String? videoError;

  String get prefix =>
      'edu_l${widget.content.level}';

  List<LessonVideoItem> get pool => [
        ...widget.content.learnItems,
        ...widget.content.guessItems,
      ];

  bool get isReviewingPreviousStage =>
      stage.index < furthestStage;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    prefs =
        await SharedPreferences.getInstance();

    await _loadState();

    if (stage != LessonStage.challenge) {
      await _loadCurrentVideo();
    } else {
      if (mounted) {
        setState(() {
          loadingVideo = false;
        });
      }
    }
  }

  // ============================================================
  // LOAD / SAVE
  // ============================================================

  Future<void> _loadState() async {
    final storage = prefs!;

    final savedStage =
        (storage.getInt(
                  '${prefix}_stage',
                ) ??
                0)
            .clamp(0, 4)
            .toInt();

    final savedFurthest =
        (storage.getInt(
                  '${prefix}_furthest_stage',
                ) ??
                savedStage)
            .clamp(0, 4)
            .toInt();

    if (!mounted) return;

    setState(() {
      stage =
          LessonStage.values[savedStage];

      furthestStage =
          savedFurthest < savedStage
              ? savedStage
              : savedFurthest;

      learnIndex =
          (storage.getInt(
                    '${prefix}_learn_index',
                  ) ??
                  0)
              .clamp(
                0,
                widget.content.learnItems.length - 1,
              )
              .toInt();

      guessIndex =
          (storage.getInt(
                    '${prefix}_guess_index',
                  ) ??
                  0)
              .clamp(
                0,
                widget.content.guessItems.length - 1,
              )
              .toInt();

      challengeIndex =
          (storage.getInt(
                    '${prefix}_challenge_index',
                  ) ??
                  0)
              .clamp(
                0,
                challengeQuestions.length - 1,
              )
              .toInt();

      finalIndex =
          (storage.getInt(
                    '${prefix}_final_index',
                  ) ??
                  0)
              .clamp(
                0,
                finalQuestions.length - 1,
              )
              .toInt();

      guessScore =
          storage.getInt(
                '${prefix}_guess_score',
              ) ??
              0;

      challengeScore =
          storage.getInt(
                '${prefix}_challenge_score',
              ) ??
              0;

      finalScore =
          storage.getInt(
                '${prefix}_final_score',
              ) ??
              0;
    });
  }

  Future<void> _saveState() async {
    final storage = prefs;

    if (storage == null) return;

    await storage.setInt(
      '${prefix}_stage',
      stage.index,
    );

    await storage.setInt(
      '${prefix}_furthest_stage',
      furthestStage,
    );

    await storage.setInt(
      '${prefix}_learn_index',
      learnIndex,
    );

    await storage.setInt(
      '${prefix}_guess_index',
      guessIndex,
    );

    await storage.setInt(
      '${prefix}_challenge_index',
      challengeIndex,
    );

    await storage.setInt(
      '${prefix}_final_index',
      finalIndex,
    );

    await storage.setInt(
      '${prefix}_guess_score',
      guessScore,
    );

    await storage.setInt(
      '${prefix}_challenge_score',
      challengeScore,
    );

    await storage.setInt(
      '${prefix}_final_score',
      finalScore,
    );
  }

  void _markStageReached(
    LessonStage newStage,
  ) {
    stage = newStage;

    if (newStage.index > furthestStage) {
      furthestStage =
          newStage.index;
    }
  }

  // ============================================================
  // QUESTIONS
  // ============================================================

  List<QuizQuestion> get guessQuestions {
    final options =
        widget.content.guessItems
            .map(
              (item) => item.label,
            )
            .toList();

    return widget.content.guessItems
        .map(
          (item) => QuizQuestion(
            target: item,
            options: options,
            correctIndex:
                options.indexOf(
              item.label,
            ),
          ),
        )
        .toList();
  }

  List<ChallengeQuestion>
      get challengeQuestions {
    final all = pool;

    final targets =
        <LessonVideoItem>[
      widget.content.learnItems.first,

      widget.content.guessItems[1],

      widget.content.learnItems.length > 1
          ? widget.content.learnItems[1]
          : widget.content.learnItems.first,
    ];

    return List.generate(
      3,
      (questionNumber) {
        final target =
            targets[questionNumber];

        final targetIndex =
            all.indexOf(target);

        final options =
            <LessonVideoItem>[
          target,

          all[
              (targetIndex + 2) %
                  all.length],

          all[
              (targetIndex + 4) %
                  all.length],
        ];

        final rotation =
            questionNumber %
                options.length;

        final rotated = [
          ...options.skip(rotation),
          ...options.take(rotation),
        ];

        return ChallengeQuestion(
          prompt: target.label,
          options: rotated,
          correctIndex:
              rotated.indexOf(target),
        );
      },
    );
  }

  List<QuizQuestion> get finalQuestions {
    final all = pool;

    final count =
        all.length < 5
            ? all.length
            : 5;

    return List.generate(
      count,
      (index) {
        final target =
            all[
                (index * 2) %
                    all.length];

        final targetIndex =
            all.indexOf(target);

        final labels =
            <String>[
          target.label,

          all[
                  (targetIndex + 1) %
                      all.length]
              .label,

          all[
                  (targetIndex + 3) %
                      all.length]
              .label,
        ];

        final rotation =
            index %
                labels.length;

        final options = [
          ...labels.skip(rotation),
          ...labels.take(rotation),
        ];

        return QuizQuestion(
          target: target,
          options: options,
          correctIndex:
              options.indexOf(
            target.label,
          ),
        );
      },
    );
  }

  // ============================================================
  // MAIN VIDEO
  // ============================================================

  LessonVideoItem?
      get currentMainItem {
    switch (stage) {
      case LessonStage.learn:
        return widget
            .content
            .learnItems[learnIndex];

      case LessonStage.guess:
        return widget
            .content
            .guessItems[guessIndex];

      case LessonStage.finalQuiz:
        return finalQuestions[
                finalIndex]
            .target;

      case LessonStage.challenge:
      case LessonStage.completed:
        return null;
    }
  }

  Future<void> _loadCurrentVideo() async {
    final item =
        currentMainItem;

    final oldController =
        controller;

    controller = null;

    if (mounted) {
      setState(() {
        loadingVideo = true;
        videoError = null;
      });
    }

    if (oldController != null) {
      await oldController.dispose();
    }

    if (item == null) {
      if (mounted) {
        setState(() {
          loadingVideo = false;
        });
      }

      return;
    }

    try {
      final next =
          VideoPlayerController.asset(
        item.asset,
      );

      await next.initialize();

      await next.setLooping(
        true,
      );

      await next.setVolume(
        stage ==
                LessonStage.learn
            ? 1.0
            : 0.0,
      );

      await next.seekTo(
        Duration.zero,
      );

      await next.play();

      if (!mounted) {
        await next.dispose();
        return;
      }

      setState(() {
        controller = next;
        loadingVideo = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        loadingVideo = false;
        videoError =
            error.toString();
      });
    }
  }

  Future<void> _disposeMainVideo() async {
    final old =
        controller;

    controller = null;

    if (old != null) {
      await old.dispose();
    }
  }

  Future<void> _replay() async {
    final video =
        controller;

    if (video == null ||
        !video.value.isInitialized) {
      return;
    }

    await video.seekTo(
      Duration.zero,
    );

    await video.play();
  }

  // ============================================================
  // PREVIOUS ITEM
  // video / question inside same stage
  // ============================================================

  bool get canGoToPreviousItem {
    switch (stage) {
      case LessonStage.learn:
        return learnIndex > 0;

      case LessonStage.guess:
        return guessIndex > 0;

      case LessonStage.challenge:
        return challengeIndex > 0;

      case LessonStage.finalQuiz:
        return finalIndex > 0;

      case LessonStage.completed:
        return false;
    }
  }

  Future<void> _previousItem() async {
    if (answerLocked) {
      return;
    }

    switch (stage) {
      case LessonStage.learn:
        if (learnIndex <= 0) {
          return;
        }

        setState(() {
          learnIndex--;
        });

        await _saveState();
        await _loadCurrentVideo();
        break;

      case LessonStage.guess:
        if (guessIndex <= 0) {
          return;
        }

        setState(() {
          guessIndex--;

          selectedAnswer = null;
          answerLocked = false;
        });

        await _saveState();
        await _loadCurrentVideo();
        break;

      case LessonStage.challenge:
        if (challengeIndex <= 0) {
          return;
        }

        setState(() {
          challengeIndex--;

          selectedAnswer = null;
          answerLocked = false;
        });

        await _saveState();
        break;

      case LessonStage.finalQuiz:
        if (finalIndex <= 0) {
          return;
        }

        setState(() {
          finalIndex--;

          selectedAnswer = null;
          answerLocked = false;
        });

        await _saveState();
        await _loadCurrentVideo();
        break;

      case LessonStage.completed:
        break;
    }
  }

  Widget _previousItemButton() {
    if (!canGoToPreviousItem) {
      return const SizedBox.shrink();
    }

    String text;

    switch (stage) {
      case LessonStage.learn:
        text = 'Previous video';
        break;

      case LessonStage.guess:
      case LessonStage.challenge:
      case LessonStage.finalQuiz:
        text = 'Previous question';
        break;

      case LessonStage.completed:
        text = '';
        break;
    }

    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: _previousItem,
        icon: const Icon(
          Icons.skip_previous_rounded,
        ),
        label: Text(text),
        style: OutlinedButton.styleFrom(
          foregroundColor: primary,
          side: const BorderSide(
            color: Color(0xFFD7D4F4),
          ),
          padding:
              const EdgeInsets.symmetric(
            vertical: 13,
          ),
          shape: RoundedRectangleBorder(
            borderRadius:
                BorderRadius.circular(
              15,
            ),
          ),
        ),
      ),
    );
  }

  // ============================================================
  // RETURN TO CURRENT STAGE
  // ============================================================

  Future<void> _returnToCurrentStage() async {
    if (!isReviewingPreviousStage) {
      return;
    }

    final target =
        LessonStage.values[
            furthestStage];

    await _disposeMainVideo();

    if (!mounted) return;

    setState(() {
      stage = target;

      selectedAnswer = null;
      answerLocked = false;
    });

    await _saveState();

    if (stage !=
        LessonStage.challenge) {
      await _loadCurrentVideo();
    }
  }

  // ============================================================
  // PROGRESS
  // ============================================================

  double get progress {
    final learnCount =
        widget.content.learnItems.length;

    final guessCount =
        widget.content.guessItems.length;

    final challengeCount =
        challengeQuestions.length;

    final finalCount =
        finalQuestions.length;

    final total =
        learnCount +
        guessCount +
        challengeCount +
        finalCount;

    int done = 0;

    final progressStage =
        furthestStage > stage.index
            ? furthestStage
            : stage.index;

    switch (progressStage) {
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

      case 4:
        done = total;
        break;
    }

    if (total == 0) {
      return 0;
    }

    return (done / total)
        .clamp(
          0.0,
          1.0,
        )
        .toDouble();
  }

  String get stageTitle {
    switch (stage) {
      case LessonStage.learn:
        return 'Learn';

      case LessonStage.guess:
        return 'Can You Guess?';

      case LessonStage.challenge:
        return 'Quick Challenge';

      case LessonStage.finalQuiz:
        return 'Final Quiz';

      case LessonStage.completed:
        return 'Level Complete';
    }
  }

  // ============================================================
  // LEARN
  // ============================================================

  Future<void> _nextLearn() async {
    if (learnIndex <
        widget.content.learnItems.length -
            1) {
      setState(() {
        learnIndex++;
      });

      await _saveState();
      await _loadCurrentVideo();

      return;
    }

    if (isReviewingPreviousStage) {
      await _returnToCurrentStage();
      return;
    }

    setState(() {
      _markStageReached(
        LessonStage.guess,
      );

      guessIndex = 0;

      selectedAnswer = null;
      answerLocked = false;
    });

    await _saveState();
    await _loadCurrentVideo();
  }

  // ============================================================
  // GUESS
  // ============================================================

  Future<void> _answerGuess(
    int selected,
  ) async {
    if (answerLocked) {
      return;
    }

    final question =
        guessQuestions[guessIndex];

    final correct =
        selected ==
            question.correctIndex;

    setState(() {
      selectedAnswer = selected;
      answerLocked = true;

      if (correct) {
        guessScore++;
      }
    });

    await _saveState();

    await Future.delayed(
      const Duration(
        milliseconds: 1050,
      ),
    );

    if (!mounted) return;

    if (guessIndex <
        guessQuestions.length - 1) {
      setState(() {
        guessIndex++;

        selectedAnswer = null;
        answerLocked = false;
      });

      await _saveState();
      await _loadCurrentVideo();

      return;
    }

    if (isReviewingPreviousStage) {
      await _returnToCurrentStage();
      return;
    }

    await _disposeMainVideo();

    if (!mounted) return;

    setState(() {
      _markStageReached(
        LessonStage.challenge,
      );

      challengeIndex = 0;

      selectedAnswer = null;
      answerLocked = false;
    });

    await _saveState();
  }

  // ============================================================
  // CHALLENGE
  // ============================================================

  Future<void> _answerChallenge(
    int selected,
  ) async {
    if (answerLocked) {
      return;
    }

    final question =
        challengeQuestions[
            challengeIndex];

    final correct =
        selected ==
            question.correctIndex;

    setState(() {
      selectedAnswer = selected;
      answerLocked = true;

      if (correct) {
        challengeScore++;
      }
    });

    await _saveState();

    await Future.delayed(
      const Duration(
        milliseconds: 1050,
      ),
    );

    if (!mounted) return;

    if (challengeIndex <
        challengeQuestions.length - 1) {
      setState(() {
        challengeIndex++;

        selectedAnswer = null;
        answerLocked = false;
      });

      await _saveState();

      return;
    }

    if (isReviewingPreviousStage) {
      await _returnToCurrentStage();
      return;
    }

    setState(() {
      _markStageReached(
        LessonStage.finalQuiz,
      );

      finalIndex = 0;

      selectedAnswer = null;
      answerLocked = false;
    });

    await _saveState();
    await _loadCurrentVideo();
  }

  // ============================================================
  // FINAL
  // ============================================================

  Future<void> _answerFinal(
    int selected,
  ) async {
    if (answerLocked) {
      return;
    }

    final question =
        finalQuestions[finalIndex];

    final correct =
        selected ==
            question.correctIndex;

    setState(() {
      selectedAnswer = selected;
      answerLocked = true;

      if (correct) {
        finalScore++;
      }
    });

    await _saveState();

    await Future.delayed(
      const Duration(
        milliseconds: 1050,
      ),
    );

    if (!mounted) return;

    if (finalIndex <
        finalQuestions.length - 1) {
      setState(() {
        finalIndex++;

        selectedAnswer = null;
        answerLocked = false;
      });

      await _saveState();
      await _loadCurrentVideo();

      return;
    }

    if (isReviewingPreviousStage) {
      await _returnToCurrentStage();
      return;
    }

    await _completeLevel();
  }

  // ============================================================
  // COMPLETE
  // ============================================================

  Future<void> _completeLevel() async {
    final storage = prefs!;

    final currentScore =
        guessScore +
        challengeScore +
        finalScore;

    final maximum =
        guessQuestions.length +
        challengeQuestions.length +
        finalQuestions.length;

    final percent =
        maximum == 0
            ? 0
            : ((currentScore /
                        maximum) *
                    100)
                .round();

    final oldBest =
        storage.getInt(
              '${prefix}_best_score',
            ) ??
            storage.getInt(
              'l${widget.content.level}_best_score',
            ) ??
            0;

    final newBest =
        percent > oldBest
            ? percent
            : oldBest;

    await storage.setBool(
      '${prefix}_completed_once',
      true,
    );

    await storage.setInt(
      '${prefix}_best_score',
      newBest,
    );

    await storage.setBool(
      'l${widget.content.level}_completed_once',
      true,
    );

    await storage.setInt(
      'l${widget.content.level}_best_score',
      newBest,
    );

    if (widget.content.level <
        educationLevels.length) {
      final next =
          widget.content.level + 1;

      await storage.setBool(
        'edu_l${next}_unlocked',
        true,
      );

      await storage.setBool(
        'l${next}_unlocked',
        true,
      );
    }

    await _disposeMainVideo();

    if (!mounted) return;

    setState(() {
      _markStageReached(
        LessonStage.completed,
      );

      selectedAnswer = null;
      answerLocked = false;
    });

    await _saveState();
  }

  // ============================================================
  // RETRY
  // ============================================================

  Future<void> _retryLevel() async {
    await _disposeMainVideo();

    if (!mounted) return;

    setState(() {
      stage =
          LessonStage.learn;

      furthestStage = 0;

      learnIndex = 0;
      guessIndex = 0;
      challengeIndex = 0;
      finalIndex = 0;

      guessScore = 0;
      challengeScore = 0;
      finalScore = 0;

      selectedAnswer = null;
      answerLocked = false;
    });

    await _saveState();
    await _loadCurrentVideo();
  }

  // ============================================================
  // PREVIOUS STAGE
  // ============================================================

  Future<void> _previousStage() async {
    if (stage ==
        LessonStage.learn) {
      return;
    }

    await _disposeMainVideo();

    if (!mounted) return;

    setState(() {
      selectedAnswer = null;
      answerLocked = false;

      switch (stage) {
        case LessonStage.guess:
          stage =
              LessonStage.learn;

          learnIndex =
              widget.content.learnItems.length -
                  1;

          break;

        case LessonStage.challenge:
          stage =
              LessonStage.guess;

          guessIndex =
              widget.content.guessItems.length -
                  1;

          break;

        case LessonStage.finalQuiz:
          stage =
              LessonStage.challenge;

          challengeIndex =
              challengeQuestions.length -
                  1;

          break;

        case LessonStage.completed:
          stage =
              LessonStage.finalQuiz;

          finalIndex =
              finalQuestions.length -
                  1;

          break;

        case LessonStage.learn:
          break;
      }
    });

    await _saveState();

    if (stage !=
        LessonStage.challenge) {
      await _loadCurrentVideo();
    }
  }

  // ============================================================
  // EXIT
  // ============================================================

  Future<void> _exit() async {
    await _saveState();

    if (!mounted) return;

    Navigator.pop(
      context,
      true,
    );
  }

  @override
  void dispose() {
    controller?.dispose();

    super.dispose();
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(
    BuildContext context,
  ) {
    return Scaffold(
      backgroundColor: background,

      appBar: AppBar(
        elevation: 0,

        backgroundColor:
            Colors.white,

        foregroundColor:
            const Color(
          0xFF25233A,
        ),

        title: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Text(
              'Level ${widget.content.level} • ${widget.content.title}',
              style:
                  const TextStyle(
                fontSize: 16,
                fontWeight:
                    FontWeight.w900,
              ),
            ),

            Text(
              stageTitle,
              style: TextStyle(
                fontSize: 12,
                color:
                    Colors.grey.shade600,
                fontWeight:
                    FontWeight.w600,
              ),
            ),
          ],
        ),

        actions: [
          IconButton(
            tooltip: 'Exit level',
            onPressed: _exit,
            icon: const Icon(
              Icons.close_rounded,
            ),
          ),
        ],
      ),

      body: SafeArea(
        child: Column(
          children: [
            _progressHeader(),

            Expanded(
              child:
                  AnimatedSwitcher(
                duration:
                    const Duration(
                  milliseconds: 250,
                ),
                child:
                    _buildStage(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // PROGRESS HEADER
  // ============================================================

  Widget _progressHeader() {
    return Container(
      color: Colors.white,

      padding:
          const EdgeInsets.fromLTRB(
        20,
        10,
        20,
        14,
      ),

      child: Column(
        children: [
          Row(
            children: [
              Text(
                widget.content.emoji,
                style:
                    const TextStyle(
                  fontSize: 25,
                ),
              ),

              const SizedBox(
                width: 10,
              ),

              Expanded(
                child: ClipRRect(
                  borderRadius:
                      BorderRadius.circular(
                    20,
                  ),
                  child:
                      LinearProgressIndicator(
                    value: progress,
                    minHeight: 9,
                    backgroundColor:
                        const Color(
                      0xFFECEBF4,
                    ),
                    valueColor:
                        const AlwaysStoppedAnimation<
                            Color>(
                      primary,
                    ),
                  ),
                ),
              ),

              const SizedBox(
                width: 10,
              ),

              Text(
                '${(progress * 100).round()}%',
                style:
                    const TextStyle(
                  fontWeight:
                      FontWeight.w900,
                  color: primary,
                ),
              ),
            ],
          ),

          if (isReviewingPreviousStage) ...[
            const SizedBox(
              height: 10,
            ),

            Container(
              width: double.infinity,
              padding:
                  const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 9,
              ),
              decoration:
                  BoxDecoration(
                color:
                    const Color(
                  0xFFFFF7E8,
                ),
                borderRadius:
                    BorderRadius.circular(
                  12,
                ),
              ),
              child: const Row(
                children: [
                  Icon(
                    Icons.history_rounded,
                    size: 17,
                    color:
                        Color(
                      0xFFE19735,
                    ),
                  ),

                  SizedBox(width: 7),

                  Expanded(
                    child: Text(
                      'You are reviewing a previous stage. Your saved progress is safe.',
                      style:
                          TextStyle(
                        color:
                            Color(
                          0xFF8B652B,
                        ),
                        fontSize: 12,
                        fontWeight:
                            FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStage() {
    switch (stage) {
      case LessonStage.learn:
        return _buildLearn();

      case LessonStage.guess:
        return _buildGuess();

      case LessonStage.challenge:
        return _buildChallenge();

      case LessonStage.finalQuiz:
        return _buildFinal();

      case LessonStage.completed:
        return _buildCompleted();
    }
  }

  // ============================================================
  // LEARN UI
  // ============================================================

  Widget _buildLearn() {
    final item =
        widget.content.learnItems[
            learnIndex];

    return ListView(
      key: ValueKey(
        'learn_$learnIndex',
      ),

      padding:
          const EdgeInsets.fromLTRB(
        20,
        18,
        20,
        28,
      ),

      children: [
        _stageLabel(
          'STEP 1',
          'Watch and understand',
        ),

        const SizedBox(height: 16),

        _mainVideo(
          crop: false,
        ),

        const SizedBox(height: 17),

        Text(
          item.label,
          textAlign:
              TextAlign.center,
          style:
              const TextStyle(
            fontSize: 24,
            height: 1.3,
            fontWeight:
                FontWeight.w900,
            color:
                Color(
              0xFF25233A,
            ),
          ),
        ),

        if (item.visualCues.isNotEmpty) ...[
          const SizedBox(
            height: 15,
          ),

          const Text(
            'Visual meaning',
            textAlign:
                TextAlign.center,
            style:
                TextStyle(
              color:
                  Color(
                0xFF777389,
              ),
              fontWeight:
                  FontWeight.w700,
            ),
          ),

          const SizedBox(
            height: 11,
          ),

          _visualCues(
            item.visualCues,
          ),
        ],

        const SizedBox(height: 22),

        if (canGoToPreviousItem) ...[
          _previousItemButton(),

          const SizedBox(
            height: 10,
          ),
        ],

        Row(
          children: [
            Expanded(
              child:
                  OutlinedButton.icon(
                onPressed: _replay,
                icon: const Icon(
                  Icons.replay_rounded,
                ),
                label:
                    const Text(
                  'Replay',
                ),
                style:
                    _secondaryStyle(),
              ),
            ),

            const SizedBox(
              width: 12,
            ),

            Expanded(
              flex: 2,
              child:
                  ElevatedButton.icon(
                onPressed:
                    _nextLearn,
                icon:
                    const Icon(
                  Icons
                      .check_circle_outline_rounded,
                ),
                label: Text(
                  learnIndex ==
                          widget
                                  .content
                                  .learnItems
                                  .length -
                              1
                      ? isReviewingPreviousStage
                          ? 'Return to current stage'
                          : 'Got it • Start Guess'
                      : 'Got it • Next',
                ),
                style:
                    _primaryStyle(),
              ),
            ),
          ],
        ),

        if (isReviewingPreviousStage) ...[
          const SizedBox(
            height: 12,
          ),

          _returnToCurrentStageButton(),
        ],
      ],
    );
  }

  // ============================================================
  // GUESS UI
  // ============================================================

  Widget _buildGuess() {
    final question =
        guessQuestions[
            guessIndex];

    return ListView(
      key: ValueKey(
        'guess_$guessIndex',
      ),

      padding:
          const EdgeInsets.fromLTRB(
        20,
        18,
        20,
        28,
      ),

      children: [
        _stageLabel(
          'STEP 2',
          'Can you guess?',
        ),

        const SizedBox(
          height: 8,
        ),

        Text(
          'Question ${guessIndex + 1} of ${guessQuestions.length}',
          textAlign:
              TextAlign.center,
          style:
              const TextStyle(
            color:
                Color(
              0xFF777389,
            ),
            fontWeight:
                FontWeight.w700,
          ),
        ),

        const SizedBox(
          height: 6,
        ),

        const Text(
          'Watch carefully. Sound is off.',
          textAlign:
              TextAlign.center,
          style:
              TextStyle(
            color:
                Color(
              0xFF777389,
            ),
            fontWeight:
                FontWeight.w600,
          ),
        ),

        const SizedBox(
          height: 15,
        ),

        _mainVideo(
          crop: true,
        ),

        const SizedBox(
          height: 19,
        ),

        ...List.generate(
          question.options.length,
          (index) {
            return Padding(
              padding:
                  const EdgeInsets.only(
                bottom: 10,
              ),
              child:
                  _answerButton(
                text:
                    question.options[
                        index],
                index: index,
                correctIndex:
                    question.correctIndex,
                onTap: () =>
                    _answerGuess(
                  index,
                ),
              ),
            );
          },
        ),

        const SizedBox(
          height: 6,
        ),

        if (canGoToPreviousItem) ...[
          _previousItemButton(),

          const SizedBox(
            height: 8,
          ),
        ],

        _previousButton(),

        if (isReviewingPreviousStage)
          _returnToCurrentStageButton(),
      ],
    );
  }

  // ============================================================
  // QUICK CHALLENGE UI
  // ============================================================

  Widget _buildChallenge() {
    final question =
        challengeQuestions[
            challengeIndex];

    return ListView(
      key: ValueKey(
        'challenge_$challengeIndex',
      ),

      padding:
          const EdgeInsets.fromLTRB(
        20,
        18,
        20,
        28,
      ),

      children: [
        _stageLabel(
          'STEP 3',
          'Choose the correct video',
        ),

        const SizedBox(
          height: 10,
        ),

        Text(
          'Question ${challengeIndex + 1} of ${challengeQuestions.length}',
          textAlign:
              TextAlign.center,
          style:
              const TextStyle(
            color:
                Color(
              0xFF777389,
            ),
            fontWeight:
                FontWeight.w700,
          ),
        ),

        const SizedBox(
          height: 14,
        ),

        Container(
          padding:
              const EdgeInsets.all(
            18,
          ),
          decoration:
              BoxDecoration(
            color: softPrimary,
            borderRadius:
                BorderRadius.circular(
              22,
            ),
          ),
          child: Column(
            children: [
              const Text(
                'Find the video that means:',
                style:
                    TextStyle(
                  color:
                      Color(
                    0xFF777389,
                  ),
                  fontWeight:
                      FontWeight.w700,
                ),
              ),

              const SizedBox(
                height: 8,
              ),

              Text(
                question.prompt,
                textAlign:
                    TextAlign.center,
                style:
                    const TextStyle(
                  fontSize: 22,
                  fontWeight:
                      FontWeight.w900,
                  color:
                      Color(
                    0xFF25233A,
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(
          height: 12,
        ),

        const Row(
          mainAxisAlignment:
              MainAxisAlignment.center,
          children: [
            Icon(
              Icons.touch_app_rounded,
              size: 17,
              color:
                  Color(
                0xFF777389,
              ),
            ),

            SizedBox(
              width: 6,
            ),

            Flexible(
              child: Text(
                'Play the videos, then choose your answer.',
                textAlign:
                    TextAlign.center,
                style:
                    TextStyle(
                  color:
                      Color(
                    0xFF777389,
                  ),
                  fontSize: 13,
                  fontWeight:
                      FontWeight.w600,
                ),
              ),
            ),
          ],
        ),

        const SizedBox(
          height: 17,
        ),

        ChallengeVideoGroup(
          key: ValueKey(
            'challenge_group_$challengeIndex',
          ),
          options:
              question.options,
          selectedAnswer:
              selectedAnswer,
          correctIndex:
              question.correctIndex,
          answerLocked:
              answerLocked,
          onAnswer:
              _answerChallenge,
        ),

        if (canGoToPreviousItem) ...[
          _previousItemButton(),

          const SizedBox(
            height: 8,
          ),
        ],

        _previousButton(),

        if (isReviewingPreviousStage)
          _returnToCurrentStageButton(),
      ],
    );
  }

  // ============================================================
  // FINAL UI
  // ============================================================

  Widget _buildFinal() {
    final question =
        finalQuestions[
            finalIndex];

    return ListView(
      key: ValueKey(
        'final_$finalIndex',
      ),

      padding:
          const EdgeInsets.fromLTRB(
        20,
        18,
        20,
        28,
      ),

      children: [
        _stageLabel(
          'STEP 4',
          'Final mixed quiz',
        ),

        const SizedBox(
          height: 10,
        ),

        Text(
          'Question ${finalIndex + 1} of ${finalQuestions.length}',
          textAlign:
              TextAlign.center,
          style:
              const TextStyle(
            color:
                Color(
              0xFF777389,
            ),
            fontWeight:
                FontWeight.w700,
          ),
        ),

        const SizedBox(
          height: 15,
        ),

        _mainVideo(
          crop: true,
        ),

        const SizedBox(
          height: 19,
        ),

        ...List.generate(
          question.options.length,
          (index) {
            return Padding(
              padding:
                  const EdgeInsets.only(
                bottom: 10,
              ),
              child:
                  _answerButton(
                text:
                    question.options[
                        index],
                index: index,
                correctIndex:
                    question.correctIndex,
                onTap: () =>
                    _answerFinal(
                  index,
                ),
              ),
            );
          },
        ),

        const SizedBox(
          height: 6,
        ),

        if (canGoToPreviousItem) ...[
          _previousItemButton(),

          const SizedBox(
            height: 8,
          ),
        ],

        _previousButton(),

        if (isReviewingPreviousStage)
          _returnToCurrentStageButton(),
      ],
    );
  }

  // ============================================================
  // COMPLETED UI
  // ============================================================

  Widget _buildCompleted() {
    final maxScore =
        guessQuestions.length +
        challengeQuestions.length +
        finalQuestions.length;

    final currentScore =
        guessScore +
        challengeScore +
        finalScore;

    final currentPercent =
        maxScore == 0
            ? 0
            : ((currentScore /
                        maxScore) *
                    100)
                .round();

    final best =
        prefs?.getInt(
              '${prefix}_best_score',
            ) ??
            currentPercent;

    final hasNext =
        widget.content.level <
            educationLevels.length;

    return Center(
      key:
          const ValueKey(
        'completed',
      ),

      child:
          SingleChildScrollView(
        padding:
            const EdgeInsets.all(
          24,
        ),

        child: Container(
          width: double.infinity,

          padding:
              const EdgeInsets.all(
            24,
          ),

          decoration:
              BoxDecoration(
            color: Colors.white,

            borderRadius:
                BorderRadius.circular(
              28,
            ),

            boxShadow: [
              BoxShadow(
                color:
                    Colors.black
                        .withOpacity(
                  0.06,
                ),
                blurRadius: 24,
                offset:
                    const Offset(
                  0,
                  8,
                ),
              ),
            ],
          ),

          child: Column(
            children: [
              const Text(
                '🎉',
                style:
                    TextStyle(
                  fontSize: 64,
                ),
              ),

              const SizedBox(
                height: 12,
              ),

              Text(
                'Level ${widget.content.level} Completed!',
                textAlign:
                    TextAlign.center,
                style:
                    const TextStyle(
                  fontSize: 26,
                  fontWeight:
                      FontWeight.w900,
                  color:
                      Color(
                    0xFF25233A,
                  ),
                ),
              ),

              const SizedBox(
                height: 7,
              ),

              Text(
                widget.content.title,
                style:
                    const TextStyle(
                  color: primary,
                  fontSize: 18,
                  fontWeight:
                      FontWeight.w900,
                ),
              ),

              const SizedBox(
                height: 24,
              ),

              Row(
                children: [
                  Expanded(
                    child:
                        _scoreBox(
                      'This try',
                      '$currentPercent%',
                    ),
                  ),

                  const SizedBox(
                    width: 12,
                  ),

                  Expanded(
                    child:
                        _scoreBox(
                      'Best score',
                      '$best%',
                    ),
                  ),
                ],
              ),

              const SizedBox(
                height: 24,
              ),

              if (hasNext)
                SizedBox(
                  width:
                      double.infinity,
                  child:
                      ElevatedButton.icon(
                    onPressed:
                        _exit,
                    icon:
                        const Icon(
                      Icons
                          .lock_open_rounded,
                    ),
                    label: Text(
                      'Level ${widget.content.level + 1} Unlocked',
                    ),
                    style:
                        _primaryStyle(),
                  ),
                )
              else
                SizedBox(
                  width:
                      double.infinity,
                  child:
                      ElevatedButton.icon(
                    onPressed:
                        _exit,
                    icon:
                        const Icon(
                      Icons
                          .check_rounded,
                    ),
                    label:
                        const Text(
                      'Back to Education',
                    ),
                    style:
                        _primaryStyle(),
                  ),
                ),

              const SizedBox(
                height: 10,
              ),

              SizedBox(
                width:
                    double.infinity,
                child:
                    OutlinedButton.icon(
                  onPressed:
                      _retryLevel,
                  icon:
                      const Icon(
                    Icons
                        .refresh_rounded,
                  ),
                  label:
                      const Text(
                    'Retry this level',
                  ),
                  style:
                      _secondaryStyle(),
                ),
              ),

              const SizedBox(
                height: 4,
              ),

              TextButton.icon(
                onPressed:
                    _previousStage,
                icon:
                    const Icon(
                  Icons
                      .arrow_back_rounded,
                ),
                label:
                    const Text(
                  'Review final quiz',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ============================================================
  // MAIN VIDEO WIDGET
  // ============================================================

  Widget _mainVideo({
    required bool crop,
  }) {
    return Container(
      decoration:
          BoxDecoration(
        color: Colors.black,

        borderRadius:
            BorderRadius.circular(
          24,
        ),

        boxShadow: [
          BoxShadow(
            color:
                Colors.black
                    .withOpacity(
              0.12,
            ),
            blurRadius: 20,
            offset:
                const Offset(
              0,
              8,
            ),
          ),
        ],
      ),

      clipBehavior:
          Clip.antiAlias,

      child: AspectRatio(
        aspectRatio:
            16 / 9,
        child:
            _videoBody(
          crop: crop,
        ),
      ),
    );
  }

  Widget _videoBody({
    required bool crop,
  }) {
    if (loadingVideo) {
      return const Center(
        child:
            CircularProgressIndicator(
          color:
              Colors.white,
        ),
      );
    }

    if (videoError != null ||
        controller == null) {
      return Container(
        color:
            const Color(
          0xFF25233A,
        ),
        alignment:
            Alignment.center,
        padding:
            const EdgeInsets.all(
          20,
        ),
        child: Column(
          mainAxisAlignment:
              MainAxisAlignment.center,
          children: [
            const Icon(
              Icons
                  .video_file_outlined,
              color:
                  Colors.white,
              size: 42,
            ),

            const SizedBox(
              height: 10,
            ),

            const Text(
              'Video could not be loaded',
              style:
                  TextStyle(
                color:
                    Colors.white,
                fontWeight:
                    FontWeight.w800,
              ),
            ),

            TextButton(
              onPressed:
                  _loadCurrentVideo,
              child:
                  const Text(
                'Try again',
              ),
            ),
          ],
        ),
      );
    }

    final video =
        VideoPlayer(
      controller!,
    );

    if (!crop) {
      return FittedBox(
        fit:
            BoxFit.contain,
        child:
            SizedBox(
          width:
              controller!
                  .value
                  .size
                  .width,
          height:
              controller!
                  .value
                  .size
                  .height,
          child: video,
        ),
      );
    }

    return ClipRect(
      child:
          Transform.scale(
        scale: 1.30,

        alignment:
            const Alignment(
          0,
          -0.40,
        ),

        child:
            FittedBox(
          fit:
              BoxFit.cover,
          child:
              SizedBox(
            width:
                controller!
                    .value
                    .size
                    .width,
            height:
                controller!
                    .value
                    .size
                    .height,
            child: video,
          ),
        ),
      ),
    );
  }

  // ============================================================
  // VISUAL CUES
  // ============================================================

  Widget _visualCues(
    List<String> cues,
  ) {
    return Wrap(
      alignment:
          WrapAlignment.center,

      spacing: 10,
      runSpacing: 10,

      children:
          cues.map(
        (emoji) {
          return Container(
            width: 60,
            height: 60,

            alignment:
                Alignment.center,

            decoration:
                BoxDecoration(
              color:
                  Colors.white,

              borderRadius:
                  BorderRadius.circular(
                18,
              ),

              border:
                  Border.all(
                color:
                    const Color(
                  0xFFE5E3F0,
                ),
              ),

              boxShadow: [
                BoxShadow(
                  color:
                      Colors.black
                          .withOpacity(
                    0.04,
                  ),
                  blurRadius: 10,
                  offset:
                      const Offset(
                    0,
                    4,
                  ),
                ),
              ],
            ),

            child:
                Text(
              emoji,
              style:
                  const TextStyle(
                fontSize: 31,
              ),
            ),
          );
        },
      ).toList(),
    );
  }

  // ============================================================
  // ANSWER BUTTON
  // ============================================================

  Widget _answerButton({
    required String text,
    required int index,
    required int correctIndex,
    required VoidCallback onTap,
  }) {
    final selected =
        selectedAnswer ==
            index;

    final correct =
        correctIndex ==
            index;

    Color border =
        const Color(
      0xFFE2E0EA,
    );

    Color cardColor =
        Colors.white;

    Color foreground =
        const Color(
      0xFF343146,
    );

    IconData? icon;

    if (answerLocked &&
        correct) {
      border =
          const Color(
        0xFF20A464,
      );

      cardColor =
          const Color(
        0xFFEAF8F1,
      );

      foreground =
          const Color(
        0xFF16804D,
      );

      icon =
          Icons
              .check_circle_rounded;
    } else if (
        answerLocked &&
        selected &&
        !correct) {
      border =
          const Color(
        0xFFE15252,
      );

      cardColor =
          const Color(
        0xFFFFEEEE,
      );

      foreground =
          const Color(
        0xFFC43C3C,
      );

      icon =
          Icons
              .cancel_rounded;
    }

    return InkWell(
      borderRadius:
          BorderRadius.circular(
        18,
      ),

      onTap:
          answerLocked
              ? null
              : onTap,

      child:
          AnimatedContainer(
        duration:
            const Duration(
          milliseconds: 180,
        ),

        padding:
            const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 15,
        ),

        decoration:
            BoxDecoration(
          color:
              cardColor,

          borderRadius:
              BorderRadius.circular(
            18,
          ),

          border:
              Border.all(
            color: border,
            width: 2,
          ),
        ),

        child: Row(
          children: [
            Container(
              width: 30,
              height: 30,

              alignment:
                  Alignment.center,

              decoration:
                  BoxDecoration(
                shape:
                    BoxShape.circle,

                color:
                    foreground
                        .withOpacity(
                  0.08,
                ),
              ),

              child:
                  Text(
                String
                    .fromCharCode(
                  65 + index,
                ),
                style:
                    TextStyle(
                  color:
                      foreground,
                  fontWeight:
                      FontWeight.w900,
                ),
              ),
            ),

            const SizedBox(
              width: 12,
            ),

            Expanded(
              child:
                  Text(
                text,
                style:
                    TextStyle(
                  color:
                      foreground,
                  fontSize: 16,
                  fontWeight:
                      FontWeight.w800,
                ),
              ),
            ),

            if (icon != null)
              Icon(
                icon,
                color:
                    foreground,
              ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // RETURN BUTTON
  // ============================================================

  Widget _returnToCurrentStageButton() {
    if (!isReviewingPreviousStage) {
      return const SizedBox.shrink();
    }

    final target =
        LessonStage.values[
            furthestStage];

    String targetName;

    switch (target) {
      case LessonStage.learn:
        targetName =
            'Learn';
        break;

      case LessonStage.guess:
        targetName =
            'Can You Guess?';
        break;

      case LessonStage.challenge:
        targetName =
            'Quick Challenge';
        break;

      case LessonStage.finalQuiz:
        targetName =
            'Final Quiz';
        break;

      case LessonStage.completed:
        targetName =
            'Level Complete';
        break;
    }

    return Padding(
      padding:
          const EdgeInsets.only(
        top: 8,
      ),

      child:
          SizedBox(
        width:
            double.infinity,

        child:
            ElevatedButton.icon(
          onPressed:
              _returnToCurrentStage,

          icon:
              const Icon(
            Icons
                .forward_rounded,
          ),

          label:
              Text(
            'Return to $targetName',
          ),

          style:
              ElevatedButton.styleFrom(
            backgroundColor:
                const Color(
              0xFF25233A,
            ),
            foregroundColor:
                Colors.white,
            elevation: 0,
            padding:
                const EdgeInsets.symmetric(
              vertical: 14,
            ),
            shape:
                RoundedRectangleBorder(
              borderRadius:
                  BorderRadius.circular(
                16,
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ============================================================
  // SMALL UI
  // ============================================================

  Widget _stageLabel(
    String step,
    String text,
  ) {
    return Row(
      mainAxisAlignment:
          MainAxisAlignment.center,

      children: [
        Container(
          padding:
              const EdgeInsets.symmetric(
            horizontal: 10,
            vertical: 6,
          ),

          decoration:
              BoxDecoration(
            color:
                softPrimary,

            borderRadius:
                BorderRadius.circular(
              20,
            ),
          ),

          child:
              Text(
            step,
            style:
                const TextStyle(
              color: primary,
              fontSize: 11,
              letterSpacing: 0.6,
              fontWeight:
                  FontWeight.w900,
            ),
          ),
        ),

        const SizedBox(
          width: 9,
        ),

        Flexible(
          child:
              Text(
            text,
            style:
                const TextStyle(
              color:
                  Color(
                0xFF56536A,
              ),
              fontWeight:
                  FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }

  Widget _previousButton() {
    if (stage ==
        LessonStage.learn) {
      return const SizedBox.shrink();
    }

    return SizedBox(
      width:
          double.infinity,

      child:
          TextButton.icon(
        onPressed:
            _previousStage,

        icon:
            const Icon(
          Icons
              .arrow_back_rounded,
        ),

        label:
            const Text(
          'Previous stage',
        ),

        style:
            TextButton.styleFrom(
          foregroundColor:
              const Color(
            0xFF666278,
          ),
          padding:
              const EdgeInsets.symmetric(
            vertical: 13,
          ),
        ),
      ),
    );
  }

  Widget _scoreBox(
    String title,
    String value,
  ) {
    return Container(
      padding:
          const EdgeInsets.symmetric(
        vertical: 16,
      ),

      decoration:
          BoxDecoration(
        color:
            background,

        borderRadius:
            BorderRadius.circular(
          18,
        ),
      ),

      child:
          Column(
        children: [
          Text(
            value,
            style:
                const TextStyle(
              fontSize: 24,
              fontWeight:
                  FontWeight.w900,
              color:
                  primary,
            ),
          ),

          const SizedBox(
            height: 4,
          ),

          Text(
            title,
            style:
                const TextStyle(
              color:
                  Color(
                0xFF777389,
              ),
              fontWeight:
                  FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  ButtonStyle _primaryStyle() {
    return ElevatedButton.styleFrom(
      backgroundColor:
          primary,

      foregroundColor:
          Colors.white,

      elevation: 0,

      padding:
          const EdgeInsets.symmetric(
        horizontal: 18,
        vertical: 15,
      ),

      shape:
          RoundedRectangleBorder(
        borderRadius:
            BorderRadius.circular(
          16,
        ),
      ),

      textStyle:
          const TextStyle(
        fontWeight:
            FontWeight.w800,
      ),
    );
  }

  ButtonStyle _secondaryStyle() {
    return OutlinedButton.styleFrom(
      foregroundColor:
          primary,

      padding:
          const EdgeInsets.symmetric(
        horizontal: 16,
        vertical: 15,
      ),

      side:
          const BorderSide(
        color:
            Color(
          0xFFD7D4F4,
        ),
      ),

      shape:
          RoundedRectangleBorder(
        borderRadius:
            BorderRadius.circular(
          16,
        ),
      ),

      textStyle:
          const TextStyle(
        fontWeight:
            FontWeight.w800,
      ),
    );
  }
}

// ============================================================
// QUICK CHALLENGE VIDEO GROUP
// ============================================================

class ChallengeVideoGroup
    extends StatefulWidget {
  final List<LessonVideoItem> options;

  final int? selectedAnswer;

  final int correctIndex;

  final bool answerLocked;

  final ValueChanged<int> onAnswer;

  const ChallengeVideoGroup({
    super.key,
    required this.options,
    required this.selectedAnswer,
    required this.correctIndex,
    required this.answerLocked,
    required this.onAnswer,
  });

  @override
  State<ChallengeVideoGroup> createState() =>
      _ChallengeVideoGroupState();
}

class _ChallengeVideoGroupState
    extends State<ChallengeVideoGroup> {
  final List<VideoPlayerController?>
      _controllers = [];

  final List<bool>
      _loading = [];

  final List<bool>
      _failed = [];

  int? _playingIndex;

  @override
  void initState() {
    super.initState();

    for (int i = 0;
        i < widget.options.length;
        i++) {
      _controllers.add(
        null,
      );

      _loading.add(
        true,
      );

      _failed.add(
        false,
      );
    }

    _initializeAll();
  }

  Future<void> _initializeAll() async {
    for (int i = 0;
        i < widget.options.length;
        i++) {
      await _initializeVideo(
        i,
      );
    }
  }

  Future<void> _initializeVideo(
    int index,
  ) async {
    try {
      final next =
          VideoPlayerController.asset(
        widget.options[index].asset,
      );

      await next.initialize();

      await next.setVolume(
        0.0,
      );

      await next.setLooping(
        false,
      );

      await next.seekTo(
        Duration.zero,
      );

      await next.pause();

      if (!mounted) {
        await next.dispose();

        return;
      }

      setState(() {
        _controllers[index] =
            next;

        _loading[index] =
            false;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _loading[index] =
            false;

        _failed[index] =
            true;
      });
    }
  }

  Future<void> _playVideo(
    int index,
  ) async {
    final selected =
        _controllers[index];

    if (selected == null ||
        !selected.value.isInitialized) {
      return;
    }

    // Stop all other videos.
    for (int i = 0;
        i < _controllers.length;
        i++) {
      final video =
          _controllers[i];

      if (video == null) {
        continue;
      }

      if (i != index) {
        await video.pause();

        await video.seekTo(
          Duration.zero,
        );
      }
    }

    await selected.pause();

    await selected.seekTo(
      Duration.zero,
    );

    await selected.play();

    if (!mounted) return;

    setState(() {
      _playingIndex =
          index;
    });
  }

  Future<void> _pauseVideo(
    int index,
  ) async {
    final video =
        _controllers[index];

    if (video == null) {
      return;
    }

    await video.pause();

    if (!mounted) return;

    setState(() {
      if (_playingIndex ==
          index) {
        _playingIndex =
            null;
      }
    });
  }

  @override
  void dispose() {
    for (final video
        in _controllers) {
      video?.dispose();
    }

    super.dispose();
  }

  @override
  Widget build(
    BuildContext context,
  ) {
    return Column(
      children:
          List.generate(
        widget.options.length,
        (index) {
          final selected =
              widget.selectedAnswer ==
                  index;

          final correct =
              widget.correctIndex ==
                  index;

          Color border =
              const Color(
            0xFFE3E1EC,
          );

          Color cardColor =
              Colors.white;

          if (widget.answerLocked &&
              correct) {
            border =
                const Color(
              0xFF20A464,
            );

            cardColor =
                const Color(
              0xFFEAF8F1,
            );
          } else if (
              widget.answerLocked &&
              selected &&
              !correct) {
            border =
                const Color(
              0xFFE15252,
            );

            cardColor =
                const Color(
              0xFFFFEEEE,
            );
          }

          return Padding(
            padding:
                const EdgeInsets.only(
              bottom: 15,
            ),

            child:
                AnimatedContainer(
              duration:
                  const Duration(
                milliseconds: 180,
              ),

              padding:
                  const EdgeInsets.all(
                10,
              ),

              decoration:
                  BoxDecoration(
                color:
                    cardColor,

                borderRadius:
                    BorderRadius.circular(
                  21,
                ),

                border:
                    Border.all(
                  color: border,
                  width: 2,
                ),

                boxShadow: [
                  BoxShadow(
                    color:
                        Colors.black
                            .withOpacity(
                      0.035,
                    ),
                    blurRadius: 12,
                    offset:
                        const Offset(
                      0,
                      5,
                    ),
                  ),
                ],
              ),

              child:
                  Column(
                children: [
                  AspectRatio(
                    aspectRatio:
                        16 / 9,

                    child:
                        ClipRRect(
                      borderRadius:
                          BorderRadius.circular(
                        15,
                      ),

                      child:
                          Stack(
                        fit:
                            StackFit.expand,

                        children: [
                          _videoView(
                            index,
                          ),

                          if (_playingIndex !=
                              index)
                            Container(
                              color:
                                  Colors.black
                                      .withOpacity(
                                0.28,
                              ),
                            ),

                          Center(
                            child:
                                _buildPlayButton(
                              index,
                            ),
                          ),

                          Positioned(
                            top: 10,
                            left: 10,

                            child:
                                Container(
                              padding:
                                  const EdgeInsets.symmetric(
                                horizontal: 11,
                                vertical: 6,
                              ),

                              decoration:
                                  BoxDecoration(
                                color:
                                    Colors.black
                                        .withOpacity(
                                  0.62,
                                ),

                                borderRadius:
                                    BorderRadius.circular(
                                  20,
                                ),
                              ),

                              child:
                                  Text(
                                'VIDEO ${String.fromCharCode(65 + index)}',
                                style:
                                    const TextStyle(
                                  color:
                                      Colors.white,
                                  fontSize: 11,
                                  letterSpacing:
                                      0.5,
                                  fontWeight:
                                      FontWeight.w900,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(
                    height: 10,
                  ),

                  SizedBox(
                    width:
                        double.infinity,

                    child:
                        OutlinedButton(
                      onPressed:
                          widget.answerLocked
                              ? null
                              : () {
                                  widget.onAnswer(
                                    index,
                                  );
                                },

                      style:
                          OutlinedButton.styleFrom(
                        foregroundColor:
                            widget.answerLocked &&
                                    correct
                                ? const Color(
                                    0xFF16804D,
                                  )
                                : widget.answerLocked &&
                                        selected &&
                                        !correct
                                    ? const Color(
                                        0xFFC43C3C,
                                      )
                                    : const Color(
                                        0xFF4D4960,
                                      ),

                        side:
                            BorderSide(
                          color:
                              widget.answerLocked &&
                                      correct
                                  ? const Color(
                                      0xFF20A464,
                                    )
                                  : widget.answerLocked &&
                                          selected &&
                                          !correct
                                      ? const Color(
                                          0xFFE15252,
                                        )
                                      : const Color(
                                          0xFFDAD8E4,
                                        ),
                        ),

                        padding:
                            const EdgeInsets.symmetric(
                          vertical: 13,
                        ),

                        shape:
                            RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(
                            14,
                          ),
                        ),
                      ),

                      child:
                          Row(
                        mainAxisAlignment:
                            MainAxisAlignment.center,

                        children: [
                          if (widget.answerLocked &&
                              correct) ...[
                            const Icon(
                              Icons
                                  .check_circle_rounded,
                            ),

                            const SizedBox(
                              width: 7,
                            ),
                          ] else if (
                              widget.answerLocked &&
                              selected &&
                              !correct) ...[
                            const Icon(
                              Icons
                                  .cancel_rounded,
                            ),

                            const SizedBox(
                              width: 7,
                            ),
                          ],

                          Text(
                            'Choose Video ${String.fromCharCode(65 + index)}',
                            style:
                                const TextStyle(
                              fontWeight:
                                  FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _videoView(
    int index,
  ) {
    if (_loading[index]) {
      return Container(
        color:
            const Color(
          0xFF25233A,
        ),
        alignment:
            Alignment.center,
        child:
            const CircularProgressIndicator(
          color:
              Colors.white,
          strokeWidth: 2,
        ),
      );
    }

    if (_failed[index]) {
      return Container(
        color:
            const Color(
          0xFF25233A,
        ),
        alignment:
            Alignment.center,
        child:
            const Icon(
          Icons
              .videocam_off_outlined,
          color:
              Colors.white,
          size: 34,
        ),
      );
    }

    final video =
        _controllers[index];

    if (video == null ||
        !video.value.isInitialized) {
      return const SizedBox.shrink();
    }

    return ClipRect(
      child:
          Transform.scale(
        scale: 1.30,

        alignment:
            const Alignment(
          0,
          -0.40,
        ),

        child:
            FittedBox(
          fit:
              BoxFit.cover,

          child:
              SizedBox(
            width:
                video.value.size.width,

            height:
                video.value.size.height,

            child:
                VideoPlayer(
              video,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPlayButton(
    int index,
  ) {
    if (_loading[index] ||
        _failed[index]) {
      return const SizedBox.shrink();
    }

    final isPlaying =
        _playingIndex ==
                index &&
            (_controllers[index]
                    ?.value
                    .isPlaying ??
                false);

    return GestureDetector(
      behavior:
          HitTestBehavior.opaque,

      onTap: () {
        if (isPlaying) {
          _pauseVideo(
            index,
          );
        } else {
          _playVideo(
            index,
          );
        }
      },

      child:
          Container(
        width: 68,
        height: 68,

        decoration:
            BoxDecoration(
          color:
              Colors.white
                  .withOpacity(
            0.96,
          ),

          shape:
              BoxShape.circle,

          border:
              Border.all(
            color:
                Colors.white,
            width: 2,
          ),

          boxShadow: [
            BoxShadow(
              color:
                  Colors.black
                      .withOpacity(
                0.22,
              ),
              blurRadius: 18,
              offset:
                  const Offset(
                0,
                6,
              ),
            ),
          ],
        ),

        child:
            Icon(
          isPlaying
              ? Icons
                  .pause_rounded
              : Icons
                  .play_arrow_rounded,

          size: 42,

          color:
              const Color(
            0xFF6C63FF,
          ),
        ),
      ),
    );
  }
}