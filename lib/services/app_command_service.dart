import 'dart:async';


// ============================================================
// SIGNBRIDGE APP COMMAND
// ============================================================
//
// This object represents ONE action understood by SignBridge AI.
//
// Examples:
//
// page   = dictionary
// action = open_word
// parameters = {
//   'word': 'WATER',
// }
//
// page   = education
// action = open_lesson
// parameters = {
//   'level': 1,
//   'lesson': 2,
// }
//
// page   = voice_assist
// action = start_sound_monitoring
//
// ============================================================

class SignBridgeAppCommand {
  final String page;

  final String action;

  final Map<String, dynamic>
      parameters;

  final bool requiresConfirmation;

  final String? requestId;


  const SignBridgeAppCommand({
    required this.page,
    required this.action,
    this.parameters =
        const <String, dynamic>{},
    this.requiresConfirmation = false,
    this.requestId,
  });


  // ==========================================================
  // FROM JSON
  // ==========================================================

  factory SignBridgeAppCommand.fromJson(
    Map<String, dynamic> json,
  ) {
    final dynamic rawParameters =
        json['parameters'];

    return SignBridgeAppCommand(
      page:
          (json['page'] ?? '')
              .toString()
              .trim()
              .toLowerCase(),

      action:
          (json['action'] ?? '')
              .toString()
              .trim()
              .toLowerCase(),

      parameters:
          rawParameters is Map
              ? Map<String, dynamic>.from(
                  rawParameters,
                )
              : <String, dynamic>{},

      requiresConfirmation:
          json['requires_confirmation'] ==
              true,

      requestId:
          json['request_id']
              ?.toString(),
    );
  }


  // ==========================================================
  // TO JSON
  // ==========================================================

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'page':
          page,

      'action':
          action,

      'parameters':
          parameters,

      'requires_confirmation':
          requiresConfirmation,

      if (requestId != null)
        'request_id':
            requestId,
    };
  }


  // ==========================================================
  // HELPERS
  // ==========================================================

  bool get isValid {
    return page.trim().isNotEmpty &&
        action.trim().isNotEmpty;
  }


  int? intParameter(
    String key,
  ) {
    final dynamic value =
        parameters[key];

    if (value == null) {
      return null;
    }

    if (value is int) {
      return value;
    }

    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(
      value.toString(),
    );
  }


  String? stringParameter(
    String key,
  ) {
    final dynamic value =
        parameters[key];

    if (value == null) {
      return null;
    }

    final String text =
        value
            .toString()
            .trim();

    if (text.isEmpty) {
      return null;
    }

    return text;
  }


  bool? boolParameter(
    String key,
  ) {
    final dynamic value =
        parameters[key];

    if (value is bool) {
      return value;
    }

    if (value == null) {
      return null;
    }

    final String text =
        value
            .toString()
            .trim()
            .toLowerCase();

    if (text == 'true' ||
        text == '1' ||
        text == 'yes') {
      return true;
    }

    if (text == 'false' ||
        text == '0' ||
        text == 'no') {
      return false;
    }

    return null;
  }
}


// ============================================================
// APP COMMAND SERVICE
// ============================================================
//
// Central command bus.
//
// Chatbot sends a command here.
//
// MainNavigationScreen listens for page navigation.
//
// DictionaryPage listens for dictionary commands.
//
// EducationPage listens for education commands.
//
// VoiceAssistPage listens for Voice Assist commands.
//
// GamesPage listens for game commands.
//
// No page needs to know how Gemini understood the sentence.
//
// ============================================================

class AppCommandService {
  AppCommandService._();


  static final AppCommandService instance =
      AppCommandService._();


  final StreamController<
      SignBridgeAppCommand>
      _controller =
      StreamController<
          SignBridgeAppCommand>
          .broadcast(
    sync: true,
  );


  Stream<SignBridgeAppCommand>
      get commands =>
          _controller.stream;


  // ==========================================================
  // SEND COMMAND
  // ==========================================================

  void dispatch(
    SignBridgeAppCommand command,
  ) {
    if (!command.isValid) {
      return;
    }

    _controller.add(
      command,
    );
  }


  // ==========================================================
  // SEND COMMAND FROM JSON
  // ==========================================================

  void dispatchJson(
    dynamic raw,
  ) {
    if (raw is! Map) {
      return;
    }

    final SignBridgeAppCommand
        command =
        SignBridgeAppCommand.fromJson(
      Map<String, dynamic>.from(
        raw,
      ),
    );

    dispatch(
      command,
    );
  }


  // ==========================================================
  // APP CAPABILITIES
  // ==========================================================
  //
  // These are NOT fixed user phrases.
  //
  // Gemini can understand:
  //
  // "open dictionary"
  // "take me to the dictionary"
  // "روح عالقاموس"
  // "بدي شوف كلمات الاشارة"
  //
  // and map all of them to the same capability.
  //
  // ==========================================================

  static const List<
      Map<String, dynamic>>
      capabilities =
      <Map<String, dynamic>>[

    // --------------------------------------------------------
    // TRANSLATE
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'translate',

      'actions':
          <String>[
        'open_page',
      ],
    },


    // --------------------------------------------------------
    // VOICE ASSIST
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'voice_assist',

      'actions':
          <String>[
        'open_page',
        'start_sound_monitoring',
        'stop_sound_monitoring',
        'start_speech_to_text',
        'stop_speech_to_text',
        'open_sound_history',
        'enable_sound_notifications',
        'disable_sound_notifications',
      ],
    },


    // --------------------------------------------------------
    // DICTIONARY
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'dictionary',

      'actions':
          <String>[
        'open_page',
        'search_word',
        'open_word',
        'select_letter',
        'clear_search',
      ],

      'parameters':
          <String>[
        'word',
        'letter',
      ],
    },


    // --------------------------------------------------------
    // EDUCATION
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'education',

      'actions':
          <String>[
        'open_page',
        'open_level',
        'open_lesson',
        'open_stage',
        'continue_learning',
      ],

      'parameters':
          <String>[
        'level',
        'lesson',
        'stage',
        'item',
      ],
    },


    // --------------------------------------------------------
    // GAMES
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'games',

      'actions':
          <String>[
        'open_page',
        'open_game',
      ],

      'parameters':
          <String>[
        'game',
        'game_index',
      ],
    },


    // --------------------------------------------------------
    // CHATBOT TOOLS
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'chatbot',

      'actions':
          <String>[
        'open_live_speech',
        'start_live_speech',
        'stop_live_speech',
        'generate_replies',
        'open_speak_for_me',
        'close_tool',
      ],
    },


    // --------------------------------------------------------
    // SOS
    // --------------------------------------------------------

    <String, dynamic>{
      'page':
          'sos',

      'actions':
          <String>[
        'open_page',
        'prepare_sos',
      ],

      // Sending the actual SOS must require confirmation.
      'confirmation_required_for':
          <String>[
        'prepare_sos',
      ],
    },
  ];


  // ==========================================================
  // DISPOSE
  // ==========================================================

  Future<void> dispose() async {
    await _controller.close();
  }
}