import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../services/signbridge_context_service.dart';

import 'dictionary_page.dart';
import 'education_page.dart';
import 'games_page.dart';
import 'translate_page.dart';
import 'voice_assist_page.dart';


// ============================================================
// CHATBOT PAGE
// ============================================================

class ChatbotPage extends StatefulWidget {
  const ChatbotPage({
    super.key,
  });

  @override
  State<ChatbotPage> createState() =>
      _ChatbotPageState();
}


// ============================================================
// CHATBOT STATE
// ============================================================

class _ChatbotPageState
    extends State<ChatbotPage> {

  // ============================================================
  // IMPORTANT:
  // Change ONLY this IP if your PC IP changes.
  // ============================================================

  static const String apiBaseUrl =
      'http://192.168.0.118:5000';


  // ============================================================
  // COLORS
  // ============================================================

  static const Color blue =
      Color(0xFF087BFF);

  static const Color cyan =
      Color(0xFF00BDEB);

  static const Color green =
      Color(0xFF00D89D);

  static const Color darkBlue =
      Color(0xFF041E47);

  static const Color darkText =
      Color(0xFF16243A);

  static const Color softText =
      Color(0xFF69758A);

  static const Color background =
      Color(0xFFF3F8FC);


  // ============================================================
  // SCAFFOLD
  // ============================================================

  final GlobalKey<ScaffoldState>
      _scaffoldKey =
      GlobalKey<ScaffoldState>();


  // ============================================================
  // CONTROLLERS
  // ============================================================

  final TextEditingController
      _textController =
      TextEditingController();

  final ScrollController
      _scrollController =
      ScrollController();


  // ============================================================
  // SPEECH
  // ============================================================

  late stt.SpeechToText _speech;

  // Speech recognition is initialized as soon as the page opens.
  late Future<void> _speechInitFuture;

  bool _speechReady = false;

  bool _isListening = false;

  bool _liveSpeechWanted = false;

  // Keep the previous sentence visible until the first word
  // of the new recording actually arrives.
  bool _replaceSpeechOnNextResult = false;

  String _liveTranscript = '';

  String _lastHeardText = '';

  Timer? _speechRestartTimer;
  bool _speechStoppingManually = false;
  bool _speechStarting = false;


  // ============================================================
  // TTS
  // ============================================================

  final FlutterTts _tts =
      FlutterTts();

  String? _speakingId;

  bool _isTtsSpeaking = false;


  // ============================================================
  // CHAT
  // ============================================================

  bool _isChatSending = false;

  final List<_ChatMessage>
      _messages = [];


  // ============================================================
  // SMART REPLIES
  // ============================================================

  bool _isGeneratingReplies = false;

  String? _smartReplyError;

  List<String> _smartReplies = [];


  // ============================================================
  // SPEAK FOR ME
  // ============================================================

  bool _speakForMeMode = false;

  bool _signBridgeMode = false;

  bool _isPreparingSpeech = false;

  String? _speakForMeResult;

  bool _speakFallbackUsed = false;


  // ============================================================
  // SAVED CHATS
  // ============================================================

  final List<_ChatSession>
      _savedChats = [];

  String _currentChatId = '';

  String _currentChatTitle =
      'New chat';


  // ============================================================
  // INIT
  // ============================================================

  @override
  void initState() {
    super.initState();

    _speech = stt.SpeechToText();

    // Prepare Android SpeechRecognizer immediately when this page opens.
    // This avoids re-initializing it after the user taps Live speech.
    _speechInitFuture = _initializeSpeech();

    _initializeTts();

    FlutterForegroundTask.addTaskDataCallback(
      _onSignBridgeMonitoringData,
    );

    _loadSavedChats();
  }


  // ============================================================
  // DISPOSE
  // ============================================================

  @override
  void dispose() {
    _speechRestartTimer?.cancel();
    _speechStoppingManually = true;

    FlutterForegroundTask.removeTaskDataCallback(
      _onSignBridgeMonitoringData,
    );

    _speech.stop();

    _tts.stop();

    _textController.dispose();

    _scrollController.dispose();

    super.dispose();
  }


  // ============================================================
  // WELCOME MESSAGE
  // ============================================================

 _ChatMessage get _welcomeMessage =>
    const _ChatMessage(
      text:
          "Hello 👋 I'm SignBridge AI.\n\n"
          "Ask me anything, use Live Speech to read nearby "
          "conversation, or use Speak for Me when you want "
          "the phone to speak on your behalf.",
      isUser: false,
      isWelcome: true,
    );


  // ============================================================
  // SPEECH INITIALIZATION
  // ============================================================

  Future<void> _initializeSpeech() async {

    try {

      final bool ready =
          await _speech.initialize(

        onStatus: (
          String status,
        ) {

          debugPrint(
            'SPEECH STATUS: $status',
          );

          if (!mounted) {
            return;
          }

          if (status == 'listening') {
            if (!_isListening) {
              setState(() {
                _isListening = true;
              });
            }
            return;
          }

          if (status == 'done' ||
              status == 'notListening') {

            if (_isListening) {
              setState(() {
                _isListening = false;
              });
            }

            if (_liveSpeechWanted &&
                !_speechStoppingManually) {
              _scheduleSpeechRestart();
            }
          }
        },

        onError: (error) {

          final String message =
              error.errorMsg.toString();

          debugPrint(
            'SPEECH ERROR: $message',
          );

          if (!mounted) {
            return;
          }

          final String low = message.toLowerCase();
          final bool fatal =
              low.contains('language_unavailable') ||
              low.contains('permission') ||
              low.contains('not_available');

          setState(() {
            _isListening = false;
            if (fatal) {
              _liveSpeechWanted = false;
            }
          });

          if (!fatal &&
              _liveSpeechWanted &&
              !_speechStoppingManually) {
            _scheduleSpeechRestart();
          }
        },
      );

      // Store readiness even if the widget was disposed meanwhile.
      _speechReady = ready;

      if (!mounted) {
        return;
      }

      setState(() {
        _speechReady = ready;
      });

      debugPrint(
        'SPEECH READY: $ready',
      );

    } catch (error) {

      _speechReady = false;

      debugPrint(
        'SPEECH INIT ERROR: $error',
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _isListening = false;
        _liveSpeechWanted = false;
      });
    }
  }


  // ============================================================
  // KEEP LIVE SPEECH ALIVE DURING SILENCE
  // ============================================================

  void _scheduleSpeechRestart() {
    _speechRestartTimer?.cancel();

    if (!mounted ||
        !_liveSpeechWanted ||
        _speechStoppingManually) {
      return;
    }

    _speechRestartTimer = Timer(
      const Duration(milliseconds: 250),
      () async {
        if (!mounted ||
            !_liveSpeechWanted ||
            _speechStoppingManually ||
            _isListening ||
            _speechStarting) {
          return;
        }

        await _startListening(
          isAutoRestart: true,
        );
      },
    );
  }


  // ============================================================
  // SOUND CONTEXT FROM VOICE ASSIST
  // ============================================================

  void _onSignBridgeMonitoringData(
    Object data,
  ) {
    if (data is! Map) {
      return;
    }

    if (data['type']?.toString() !=
            'sound_result' ||
        data['reliable'] != true) {
      return;
    }

    final String label =
        data['label']?.toString().trim() ?? '';

    if (label.isEmpty) {
      return;
    }

    final double? confidence =
        (data['confidence'] as num?)?.toDouble();

    final String? severity =
        data['severity']?.toString();

    unawaited(
      SignBridgeContextService.saveLastSound(
        label: label,
        confidence: confidence,
        severity: severity,
        reliable: true,
      ),
    );
  }


  // ============================================================
  // TTS INITIALIZATION
  // ============================================================

  Future<void> _initializeTts() async {

    try {

      await _tts.setSpeechRate(
        0.47,
      );

      await _tts.setPitch(
        1.0,
      );

      await _tts.setVolume(
        1.0,
      );

      _tts.setStartHandler(() {

        if (!mounted) {
          return;
        }

        setState(() {
          _isTtsSpeaking = true;
        });
      });

      _tts.setCompletionHandler(() {
        _clearSpeakingVisual();
      });

      _tts.setCancelHandler(() {
        _clearSpeakingVisual();
      });

      // IMPORTANT:
      // Do not force String type here.
      _tts.setErrorHandler((message) {

        debugPrint(
          'TTS ERROR: $message',
        );

        _clearSpeakingVisual();
      });

    } catch (error) {

      debugPrint(
        'TTS INIT ERROR: $error',
      );
    }
  }


  // ============================================================
  // CLEAR SPEAKING VISUAL
  // ============================================================

  void _clearSpeakingVisual() {

    if (!mounted) {
      return;
    }

    setState(() {
      _isTtsSpeaking = false;
      _speakingId = null;
    });
  }


  // ============================================================
  // SPEAK TEXT
  // ============================================================

  Future<void> _speakText(
    String text, {
    required String id,
  }) async {

    final String clean =
        text.trim();

    if (clean.isEmpty) {
      return;
    }

    await _tts.stop();

    final bool hasArabic =
        RegExp(
          r'[\u0600-\u06FF]',
        ).hasMatch(
          clean,
        );

    try {

      if (hasArabic) {

        await _tts.setLanguage(
          'ar-SA',
        );

      } else {

        await _tts.setLanguage(
          'en-US',
        );
      }

    } catch (_) {
      // Keep default phone voice.
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _speakingId = id;
      _isTtsSpeaking = true;
    });

    try {

      await _tts.speak(
        clean,
      );

    } catch (error) {

      debugPrint(
        'TTS SPEAK ERROR: $error',
      );

      _clearSpeakingVisual();

      _showMessage(
        'Could not play the voice.',
      );
    }
  }


  // ============================================================
  // LIVE SPEECH
  // ============================================================

  Future<void> _toggleLiveConversation() async {

    // If the microphone is currently listening, this tap stops only
    // the microphone. The Live Speech card stays open so replies can
    // still be generated from what was heard.
    if (_isListening) {
      await _stopListening(
        keepToolActive: true,
      );
      return;
    }

    // Opening Live Speech closes every other temporary tool.
    if (_speakForMeMode) {
      await _setSpeakForMeMode(
        false,
      );
    }

    if (!mounted) {
      return;
    }

    _speechRestartTimer?.cancel();
    _speechStoppingManually = false;

    setState(() {
      _signBridgeMode = false;

      // Activate the tool.
      _liveSpeechWanted = true;
      _isListening = true;

      // Keep the previous sentence visible until the first new word
      // arrives if the user starts another listening session while
      // this same tool is still open.
      _replaceSpeechOnNextResult = true;

      _smartReplies = [];
      _smartReplyError = null;

      _speakForMeResult = null;
      _speakFallbackUsed = false;
    });

    await _startListening();
  }


  // ============================================================
  // START LISTENING
  // ============================================================

  Future<void> _startListening({
    bool isAutoRestart = false,
  }) async {

    if (_speechStarting ||
        _speechStoppingManually ||
        !_liveSpeechWanted) {
      return;
    }

    _speechStarting = true;

    try {
      if (!_speechReady) {
        await _speechInitFuture;
      }

      if (!_speechReady) {
        if (!mounted) return;
        setState(() {
          _liveSpeechWanted = false;
          _isListening = false;
        });
        _showMessage(
          'Speech recognition is not available.',
        );
        return;
      }

      if (_speech.isListening) {
        return;
      }

      if (_isTtsSpeaking) {
        _tts.stop();
        if (mounted) {
          setState(() {
            _isTtsSpeaking = false;
            _speakingId = null;
          });
        }
      }

      if (!mounted ||
          !_liveSpeechWanted ||
          _speechStoppingManually) {
        return;
      }

      setState(() {
        _isListening = true;
      });

      debugPrint(
        isAutoRestart
            ? 'RESTARTING LIVE SPEECH AFTER SILENCE'
            : 'STARTING LIVE SPEECH',
      );

      await _speech.listen(
        listenFor:
            const Duration(
          minutes: 2,
        ),
        pauseFor:
            const Duration(
          seconds: 5,
        ),
        partialResults: true,
        cancelOnError: false,
        listenMode:
            stt.ListenMode.dictation,
        onResult: (result) {
          if (!mounted) return;

          final String text =
              result.recognizedWords.trim();

          if (text.isEmpty) return;

          setState(() {
            if (_replaceSpeechOnNextResult) {
              _liveTranscript = '';
              _lastHeardText = '';
              _replaceSpeechOnNextResult = false;
            }

            _liveTranscript = text;
            _lastHeardText = text;
            _smartReplies = [];
            _smartReplyError = null;
          });

          unawaited(
            SignBridgeContextService
                .saveRecentSpeech(text),
          );

          debugPrint(
            'LIVE PARTIAL: $text',
          );
        },
      );
    } catch (error) {
      debugPrint(
        'START LISTENING ERROR: $error',
      );

      if (!mounted) return;

      setState(() {
        _isListening = false;
      });

      if (_liveSpeechWanted &&
          !_speechStoppingManually) {
        _scheduleSpeechRestart();
      }
    } finally {
      _speechStarting = false;
    }
  }


  // ============================================================
  // STOP LISTENING
  // ============================================================

  Future<void> _stopListening({
    bool keepToolActive = true,
  }) async {

    _speechStoppingManually = true;
    _speechRestartTimer?.cancel();

    try {
      await _speech.stop();
    } catch (_) {}

    if (!mounted) {
      return;
    }

    setState(() {
      _isListening = false;

      if (!keepToolActive) {
        _liveSpeechWanted = false;
      }

      _replaceSpeechOnNextResult = false;

      if (_liveTranscript
          .trim()
          .isNotEmpty) {

        _lastHeardText =
            _liveTranscript.trim();
      }
    });
  }


  // ============================================================
  // CLEAR LIVE SPEECH
  // ============================================================

  Future<void> _clearLiveSpeech() async {

    _speechStoppingManually = true;
    _speechRestartTimer?.cancel();

    final String savedSpeech =
        _liveTranscript.trim().isNotEmpty
            ? _liveTranscript.trim()
            : _lastHeardText.trim();

    if (savedSpeech.isNotEmpty) {
      // Keep the last speech available to SignBridge AI even though
      // the temporary Live Speech UI is about to disappear.
      unawaited(
        SignBridgeContextService.saveRecentSpeech(
          savedSpeech,
        ),
      );
    }

    if (_isListening ||
        _liveSpeechWanted) {

      await _stopListening(
        keepToolActive: false,
      );
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _liveSpeechWanted = false;
      _isListening = false;

      _liveTranscript = '';
      _lastHeardText = '';

      _replaceSpeechOnNextResult = false;

      _smartReplies = [];
      _smartReplyError = null;
      _isGeneratingReplies = false;
    });
  }


  // ============================================================
  // GENERATE REPLIES
  // ============================================================

  Future<void> _generateRepliesFromCurrentSpeech() async {
    final String heard = _liveTranscript.trim().isNotEmpty
        ? _liveTranscript.trim()
        : _lastHeardText.trim();

    if (heard.isEmpty) {
      _showMessage('Listen to some speech first.');
      return;
    }

    if (_isListening) {
      await _stopListening(
        keepToolActive: true,
      );
    }

    if (!mounted) return;

    setState(() {
      _lastHeardText = heard;
      _liveTranscript = heard;
      _isGeneratingReplies = true;
      _smartReplyError = null;
      _smartReplies = [];
    });

    unawaited(SignBridgeContextService.saveRecentSpeech(heard));

    try {
      Map<String, dynamic>? decoded;
      Object? firstError;

      try {
        final http.Response response = await http
            .post(
              Uri.parse('$apiBaseUrl/api/chatbot/smart-replies'),
              headers: const {'Content-Type': 'application/json'},
              body: jsonEncode({'heard_text': heard}),
            )
            .timeout(const Duration(seconds: 30));

        final dynamic raw = jsonDecode(response.body);
        if (raw is Map) {
          decoded = Map<String, dynamic>.from(raw);
        }

        if (response.statusCode != 200 || decoded?['success'] != true) {
          throw Exception(decoded?['message'] ?? 'Smart Reply request failed.');
        }
      } catch (error) {
        firstError = error;
        debugPrint('SMART REPLIES PRIMARY ERROR: $error');
        decoded = null;
      }

      if (decoded == null) {
        final http.Response response = await http
            .post(
              Uri.parse('$apiBaseUrl/api/chatbot/message'),
              headers: const {'Content-Type': 'application/json'},
              body: jsonEncode({
                'message': heard,
                'mode': 'smart_reply',
                'history': const [],
                'app_context': await SignBridgeContextService.buildAppContext(
                  recentSpeech: heard,
                ),
              }),
            )
            .timeout(const Duration(seconds: 35));

        final dynamic raw = jsonDecode(response.body);
        if (raw is! Map) {
          throw Exception('Invalid Smart Reply server response.');
        }

        decoded = Map<String, dynamic>.from(raw);
        if (response.statusCode != 200 || decoded['success'] != true) {
          throw Exception(
            decoded['message'] ?? firstError?.toString() ?? 'Could not generate replies.',
          );
        }
      }

      final List<String> replies = [];
      final dynamic rawReplies = decoded['replies'];

      if (rawReplies is List) {
        for (final dynamic item in rawReplies) {
          final String value = item.toString().trim();
          if (value.isNotEmpty && !replies.contains(value)) {
            replies.add(value);
          }
          if (replies.length == 6) break;
        }
      }

      if (replies.isEmpty) {
        final String rawText = (decoded['reply'] ?? '').toString().trim();
        for (final String rawLine in rawText.split('\n')) {
          String line = rawLine.trim();
          line = line.replaceFirst(
            RegExp(r'^\s*(?:\d+\s*[.):-]\s*|[-•*]\s*)'),
            '',
          ).trim();
          if (line.isNotEmpty && !replies.contains(line)) {
            replies.add(line);
          }
          if (replies.length == 6) break;
        }
      }

      if (replies.length != 6) {
        throw Exception(
          'AI returned ${replies.length} replies. Six distinct replies are required.',
        );
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _smartReplies =
            List<String>.from(
          replies,
        );
      });
    } catch (error) {
      debugPrint('SMART REPLIES ERROR: $error');
      if (!mounted) return;
      String message = error.toString().replaceFirst('Exception: ', '').trim();
      if (message.length > 180) {
        message = '${message.substring(0, 180)}...';
      }
      setState(() {
        _smartReplyError = 'Could not generate replies.\n$message';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isGeneratingReplies = false;
        });
      }
    }
  }


  // ============================================================
  // SPEAK FOR ME MODE
  // ============================================================

  Future<void> _setSpeakForMeMode(
    bool enabled,
  ) async {

    // Opening Speak for Me closes Live Speech completely.
    if (enabled &&
        (_isListening ||
            _liveSpeechWanted)) {

      await _clearLiveSpeech();
    }

    // Stop current TTS when switching modes.
    await _tts.stop();

    if (!mounted) {
      return;
    }

    setState(() {
      _speakForMeMode = enabled;

      if (enabled) {
        _signBridgeMode = false;
      }

      // Speak for Me is temporary. Its old input/result must never
      // remain after the tool is closed or another tool is opened.
      _textController.clear();

      _speakForMeResult = null;
      _speakFallbackUsed = false;
      _isPreparingSpeech = false;

      _speakingId = null;
      _isTtsSpeaking = false;
    });
  }


  // ============================================================
  // PREPARE SPEAK FOR ME
  // ============================================================

  // ============================================================
// SPEAK FOR ME
// SPEAK EXACTLY WHAT THE USER TYPES
// ============================================================

Future<void> _prepareSpeakForMe() async {
  final String text =
      _textController.text.trim();

  if (text.isEmpty ||
      _isPreparingSpeech) {
    return;
  }

  FocusScope.of(context).unfocus();

  setState(() {
    _isPreparingSpeech = true;

    // Keep EXACTLY what the user typed.
    _speakForMeResult = text;

    // No AI fallback because AI is not used here.
    _speakFallbackUsed = false;

    // Clear input after saving the sentence.
    _textController.clear();
  });

  try {
    // Speak the exact same sentence.
    await _speakText(
      text,
      id: 'speak_for_me_result',
    );
  } catch (error) {
    debugPrint(
      'SPEAK FOR ME ERROR: $error',
    );

    _showMessage(
      'Could not play the voice.',
    );
  } finally {
    if (mounted) {
      setState(() {
        _isPreparingSpeech = false;
      });
    }
  }
}


  // ============================================================
  // SAFE APP CONTROL
  // ============================================================

  bool _hasNavigationVerb(String lower) {
    const List<String> verbs = [
      'open', 'go to', 'take me to', 'navigate to', 'show me',
      'افتح', 'افتحي', 'ادخل', 'دخلني', 'اذهب', 'اذهبي',
      'روح', 'روحي', 'خذني', 'خدني', 'وديني',
    ];
    return verbs.any(lower.contains);
  }

  String? _extractDictionaryWord(String text) {
    final List<RegExp> patterns = [
      RegExp(
        "(?:word|كلمة)\\s+[\"']?([^\"'،,.!?]+?)[\"']?\\s+(?:in\\s+(?:the\\s+)?dictionary|في\\s+(?:ال)?قاموس)",
        caseSensitive: false,
      ),
      RegExp(
        "(?:open|show|find|look up|search for)\\s+(?:the\\s+)?(?:word\\s+)?[\"']?(.+?)[\"']?\\s+(?:in|inside)\\s+(?:the\\s+)?dictionary",
        caseSensitive: false,
      ),
      
    ];

    for (final RegExp pattern in patterns) {
      final RegExpMatch? match = pattern.firstMatch(text.trim());
      if (match == null) continue;
      final String value = (match.group(1) ?? '').trim();
      if (value.isNotEmpty && value.length <= 60) return value;
    }
    return null;
  }

  Future<void> _recordLocalCommand(
    String userText,
    String reply,
  ) async {
    if (!mounted) return;

    setState(() {
      _signBridgeMode = true;
      _messages.add(_ChatMessage(text: userText, isUser: true));
      _messages.add(_ChatMessage(text: reply, isUser: false));
      _textController.clear();
      if (_currentChatTitle == 'New chat') {
        _currentChatTitle = _makeChatTitle(userText);
      }
    });

    await _saveCurrentChat();
    _scrollToBottom();
  }

  Future<bool> _tryHandleAppCommand(String text) async {
    final String lower = text.toLowerCase().trim();
    if (!_hasNavigationVerb(lower)) return false;

    if (_isListening || _liveSpeechWanted) {
      await _clearLiveSpeech();
    }
    if (_speakForMeMode) {
      await _setSpeakForMeMode(false);
    }
    if (!mounted) return true;

    final bool dictionary =
        lower.contains('dictionary') ||
        lower.contains('القاموس') ||
        lower.contains('قاموس');

    if (dictionary) {
      final String? word = _extractDictionaryWord(text);
      await _recordLocalCommand(
        text,
        word == null
            ? 'Opening the Dictionary.'
            : 'Opening "$word" in the Dictionary.',
      );
      if (!mounted) return true;
      await Navigator.push(
  context,
  MaterialPageRoute(
    builder: (_) => const DictionaryPage(),
  ),
);
      return true;
    }

    if (lower.contains('education') ||
        lower.contains('learning') ||
        lower.contains('التعليم') || lower.contains('التعلم')) {
      await _recordLocalCommand(text, 'Opening Education.');
      if (!mounted) return true;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => const EducationPage()));
      return true;
    }

    if (lower.contains('voice assist') || lower.contains('sound analysis') ||
        lower.contains('تحليل الصوت') || lower.contains('مساعد الصوت')) {
      await _recordLocalCommand(text, 'Opening Voice Assist.');
      if (!mounted) return true;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => const VoiceAssistPage()));
      return true;
    }

    if (lower.contains('games') || lower.contains('game') ||
        lower.contains('الألعاب') || lower.contains('العاب')) {
      await _recordLocalCommand(text, 'Opening Games.');
      if (!mounted) return true;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => const GamesPage()));
      return true;
    }

    if (lower.contains('translate') || lower.contains('translation') ||
        lower.contains('الترجمة') || lower.contains('ترجمة')) {
      await _recordLocalCommand(text, 'Opening Translate.');
      if (!mounted) return true;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => const TranslatePage()));
      return true;
    }

    return false;
  }


  // ============================================================
  // NORMAL CHAT
  // ============================================================

  Future<void> _sendNormalChat() async {

    final String text =
        _textController.text
            .trim();

    if (text.isEmpty ||
        _isChatSending) {

      return;
    }

    if (await _tryHandleAppCommand(text)) {
      return;
    }

    // Any normal typed question belongs to the SignBridge AI tool.
    // If Live Speech is still visible, close its temporary cards first.
    // The last speech is saved by _clearLiveSpeech(), so AI context is not lost.
    if (_isListening ||
        _liveSpeechWanted) {
      await _clearLiveSpeech();
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _signBridgeMode = true;
    });

    FocusScope.of(context)
        .unfocus();

    final List<_ChatMessage> usableHistory =
        _messages
            .where(
              (message) =>
                  !message.isWelcome &&
                  !message.text.contains('RESOURCE_EXHAUSTED') &&
                  !message.text.contains('could not answer this request'),
            )
            .toList();

    final List<_ChatMessage> recentHistory =
        usableHistory.length > 8
            ? usableHistory.sublist(usableHistory.length - 8)
            : usableHistory;

    final List<Map<String, String>> history =
        recentHistory
            .map(
              (message) => {
                'role': message.isUser ? 'user' : 'assistant',
                'content': message.text,
              },
            )
            .toList();

    final _ChatMessage
        userMessage =
        _ChatMessage(
      text: text,
      isUser: true,
    );

    setState(() {

      _messages.add(
        userMessage,
      );

      _textController.clear();

      _isChatSending = true;

      if (_currentChatTitle ==
          'New chat') {

        _currentChatTitle =
            _makeChatTitle(
          text,
        );
      }
    });

    await _saveCurrentChat();

    _scrollToBottom();

    try {

      final http.Response response =
          await http
              .post(
                Uri.parse(
                  '$apiBaseUrl'
                  '/api/chatbot/message',
                ),

                headers: {
                  'Content-Type':
                      'application/json',
                },

                body: jsonEncode(
                  {
                    'message':
                        text,

                    'mode':
                        'signbridge',

                    'history':
                        history,

                    'app_context':
                        await SignBridgeContextService.buildAppContext(
                      recentSpeech:
                          _lastHeardText,
                    ),
                  },
                ),
              )
              .timeout(
                const Duration(
                  seconds: 40,
                ),
              );

      final dynamic decoded =
          jsonDecode(
        response.body,
      );

      if (decoded is! Map) {

        throw Exception(
          'Invalid AI response.',
        );
      }

      if (response.statusCode != 200 ||
          decoded['success'] != true) {

        throw Exception(
          decoded['message'] ??
              'AI request failed.',
        );
      }

      final String reply =
          (decoded['reply'] ?? '')
              .toString()
              .trim();

      if (reply.isEmpty) {

        throw Exception(
          'AI returned an empty message.',
        );
      }

      if (!mounted) {
        return;
      }

      setState(() {

        _messages.add(
          _ChatMessage(
            text:
                _cleanAiText(
              reply,
            ),

            isUser: false,
          ),
        );
      });

      await _saveCurrentChat();

      _scrollToBottom();

    } catch (error) {

      debugPrint(
        'NORMAL CHAT ERROR: $error',
      );

      if (!mounted) {
        return;
      }

      String errorText =
          error
              .toString()
              .replaceFirst(
                'Exception: ',
                '',
              )
              .trim();

      if (errorText.length > 180) {
        errorText =
            '${errorText.substring(0, 180)}...';
      }

      setState(() {
        _messages.add(
          _ChatMessage(
            text:
                'SignBridge AI could not answer this request. '
                '$errorText',
            isUser: false,
          ),
        );
      });

      _scrollToBottom();

    } finally {

      if (mounted) {

        setState(() {
          _isChatSending = false;
        });
      }
    }
  }


  // ============================================================
  // SEND BUTTON
  // ============================================================

  Future<void> _sendInput() async {

    if (_speakForMeMode) {

      await _prepareSpeakForMe();

    } else {

      await _sendNormalChat();
    }
  }


  // ============================================================
  // CLEAN AI MARKDOWN
  // ============================================================

  String _cleanAiText(
    String text,
  ) {

    return text
        .replaceAll(
          '**',
          '',
        )
        .trim();
  }


  // ============================================================
  // COPY
  // ============================================================

  Future<void> _copyText(
    String text,
  ) async {

    await Clipboard.setData(
      ClipboardData(
        text: text,
      ),
    );

    _showMessage(
      'Copied',
    );
  }


  // ============================================================
  // SIGNBRIDGE GUIDE / INTELLIGENT SHORTCUTS
  // ============================================================

  Future<void> _toggleSignBridgeMode() async {

    final bool willEnable =
        !_signBridgeMode;

    if (willEnable) {
      // SignBridge is mutually exclusive with the two temporary tools.
      // Their UI disappears, but chat messages are never removed.
      if (_isListening ||
          _liveSpeechWanted) {

        await _clearLiveSpeech();
      }

      if (_speakForMeMode) {
        await _setSpeakForMeMode(
          false,
        );
      }
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _signBridgeMode =
          willEnable;

      // Do not clear _messages. SignBridge conversations persist.
      _textController.clear();
    });

    _showMessage(
      _signBridgeMode
          ? 'SignBridge AI active — ask anything.'
          : 'SignBridge AI tool closed.',
    );
  }


  // ============================================================
  // SAVED CHAT STORAGE
  // ============================================================

  Future<void> _loadSavedChats() async {

    final SharedPreferences prefs =
        await SharedPreferences
            .getInstance();

    final String? stored =
        prefs.getString(
      'signbridge_ai_chats',
    );

    if (stored != null &&
        stored.isNotEmpty) {

      try {

        final dynamic decoded =
            jsonDecode(
          stored,
        );

        if (decoded is List) {

          _savedChats.clear();

          for (final item in decoded) {

            if (item is Map) {

              _savedChats.add(
                _ChatSession
                    .fromJson(
                  Map<String, dynamic>
                      .from(
                    item,
                  ),
                ),
              );
            }
          }
        }

      } catch (error) {

        debugPrint(
          'LOAD CHATS ERROR: $error',
        );
      }
    }

    if (!mounted) {
      return;
    }

    if (_savedChats.isNotEmpty) {

      _savedChats.sort(
        (a, b) =>
            b.updatedAt
                .compareTo(
          a.updatedAt,
        ),
      );

      _openSavedChat(
        _savedChats.first,
        closeDrawer: false,
      );

    } else {

      _createNewChat(
        closeDrawer: false,
      );
    }
  }


  // ============================================================
  // NEW CHAT
  // ============================================================

  void _createNewChat({
    bool closeDrawer = true,
  }) {

    if (closeDrawer) {

      Navigator.maybePop(
        context,
      );
    }

    setState(() {

      _currentChatId =
          DateTime.now()
              .microsecondsSinceEpoch
              .toString();

      _currentChatTitle =
          'New chat';

      _messages
        ..clear()
        ..add(
          _welcomeMessage,
        );

      _smartReplies = [];

      _smartReplyError = null;

      _textController.clear();

      _speakForMeMode = false;

      _signBridgeMode = false;

      _liveSpeechWanted = false;
      _isListening = false;
      _liveTranscript = '';
      _lastHeardText = '';
      _smartReplies = [];
      _smartReplyError = null;

      _speakForMeResult = null;
    });
  }


  // ============================================================
  // SAVE CURRENT CHAT
  // ============================================================

  Future<void> _saveCurrentChat() async {

    if (_currentChatId.isEmpty) {
      return;
    }

    final int index =
        _savedChats.indexWhere(
      (chat) =>
          chat.id ==
          _currentChatId,
    );

    final _ChatSession session =
        _ChatSession(
      id:
          _currentChatId,

      title:
          _currentChatTitle,

      updatedAt:
          DateTime.now()
              .millisecondsSinceEpoch,

      messages:
          List<_ChatMessage>.from(
        _messages,
      ),
    );

    if (index >= 0) {

      _savedChats[index] =
          session;

    } else {

      _savedChats.add(
        session,
      );
    }

    _savedChats.sort(
      (a, b) =>
          b.updatedAt
              .compareTo(
        a.updatedAt,
      ),
    );

    await _persistChats();
  }


  // ============================================================
  // PERSIST CHATS
  // ============================================================

  Future<void> _persistChats() async {

    final SharedPreferences prefs =
        await SharedPreferences
            .getInstance();

    final String encoded =
        jsonEncode(
      _savedChats
          .map(
            (chat) =>
                chat.toJson(),
          )
          .toList(),
    );

    await prefs.setString(
      'signbridge_ai_chats',
      encoded,
    );

    if (mounted) {
      setState(() {});
    }
  }


  // ============================================================
  // OPEN CHAT
  // ============================================================

  void _openSavedChat(
    _ChatSession chat, {
    bool closeDrawer = true,
  }) async {

    if (closeDrawer) {

      Navigator.pop(
        context,
      );
    }

    await _tts.stop();

    if (!mounted) {
      return;
    }

    setState(() {

      _currentChatId =
          chat.id;

      _currentChatTitle =
          chat.title;

      _messages
        ..clear()
        ..addAll(
          chat.messages,
        );

      if (_messages.isEmpty) {

        _messages.add(
          _welcomeMessage,
        );
      }

      _smartReplies = [];

      _smartReplyError = null;

      _speakForMeMode = false;

      _signBridgeMode = false;

      _liveSpeechWanted = false;
      _isListening = false;
      _liveTranscript = '';
      _lastHeardText = '';
      _smartReplies = [];
      _smartReplyError = null;

      _speakForMeResult = null;

      _textController.clear();
    });

    _scrollToBottom();
  }


  // ============================================================
  // DELETE CHAT
  // ============================================================

  Future<void> _deleteChat(
    _ChatSession chat,
  ) async {

    final bool? confirmed =
        await showDialog<bool>(
      context: context,

      builder: (
        BuildContext context,
      ) {

        return AlertDialog(
          title:
              const Text(
            'Delete conversation?',
          ),

          content: Text(
            '"${chat.title}" will be permanently deleted.',
          ),

          actions: [

            TextButton(
              onPressed: () =>
                  Navigator.pop(
                context,
                false,
              ),

              child:
                  const Text(
                'Cancel',
              ),
            ),

            FilledButton(
              onPressed: () =>
                  Navigator.pop(
                context,
                true,
              ),

              child:
                  const Text(
                'Delete',
              ),
            ),
          ],
        );
      },
    );

    if (confirmed != true) {
      return;
    }

    _savedChats.removeWhere(
      (item) =>
          item.id ==
          chat.id,
    );

    await _persistChats();

    if (_currentChatId ==
        chat.id) {

      _createNewChat(
        closeDrawer: false,
      );
    }
  }


  // ============================================================
  // CHAT TITLE
  // ============================================================

  String _makeChatTitle(
    String text,
  ) {

    String title =
        text
            .replaceAll(
              '\n',
              ' ',
            )
            .trim();

    if (title.length > 32) {

      title =
          '${title.substring(0, 32)}…';
    }

    return title;
  }


  // ============================================================
  // SCROLL
  // ============================================================

  void _scrollToBottom() {

    WidgetsBinding.instance
        .addPostFrameCallback(
      (_) {

        if (!_scrollController
            .hasClients) {

          return;
        }

        _scrollController.animateTo(
          _scrollController
              .position
              .maxScrollExtent,

          duration:
              const Duration(
            milliseconds: 280,
          ),

          curve:
              Curves.easeOut,
        );
      },
    );
  }


  // ============================================================
  // SNACKBAR
  // ============================================================

  void _showMessage(
    String text,
  ) {

    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(
      context,
    )
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content:
              Text(
            text,
          ),

          behavior:
              SnackBarBehavior
                  .floating,

          duration:
              const Duration(
            seconds: 2,
          ),
        ),
      );
  }


  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(
    BuildContext context,
  ) {

    return Scaffold(

      key:
          _scaffoldKey,

      backgroundColor:
          background,

      drawer:
          _buildDrawer(),

      body: SafeArea(
        child: Column(
          children: [

            _buildHeader(),

            Expanded(
              child: Stack(
                children: [

                  // =================================================
                  // SOFT BACKGROUND
                  // =================================================

                  Positioned(
                    top: -80,
                    left: -70,

                    child: Container(
                      width: 220,
                      height: 220,

                      decoration:
                          BoxDecoration(
                        shape:
                            BoxShape.circle,

                        color:
                            blue.withOpacity(
                          0.07,
                        ),
                      ),
                    ),
                  ),

                  Positioned(
                    bottom: 30,
                    right: -90,

                    child: Container(
                      width: 240,
                      height: 240,

                      decoration:
                          BoxDecoration(
                        shape:
                            BoxShape.circle,

                        color:
                            green.withOpacity(
                          0.07,
                        ),
                      ),
                    ),
                  ),

                  // =================================================
                  // CHAT
                  // =================================================

                  ListView(
                    controller:
                        _scrollController,

                    padding:
                        const EdgeInsets
                            .fromLTRB(
                      14,
                      12,
                      14,
                      150,
                    ),

                    children: [

                      ..._messages.map(
                        _buildChatMessage,
                      ),

                      if (_isChatSending)
                        _buildAiLoading(),

                      if (_liveSpeechWanted ||
                          _isListening)
                        _buildLiveSpeechCard(),

                      if ((_liveSpeechWanted ||
                              _isListening) &&
                          (_smartReplies
                                  .isNotEmpty ||
                              _smartReplyError !=
                                  null ||
                              _isGeneratingReplies))
                        _buildSmartRepliesCard(),
                    ],
                  ),
                ],
              ),
            ),

            // =====================================================
            // SPEAK FOR ME RESULT
            // =====================================================

            if (_speakForMeMode &&
                _speakForMeResult != null)
              _buildSpeakForMeResult(),

            // =====================================================
            // COMPACT TOOLS + INPUT
            // =====================================================

            _buildBottomArea(),
          ],
        ),
      ),
    );
  }


  // ============================================================
  // HEADER
  // ============================================================

  Widget _buildHeader() {

    return Padding(
      padding:
          const EdgeInsets
              .fromLTRB(
        10,
        8,
        12,
        7,
      ),

      child: Row(
        children: [

          IconButton(
            onPressed: () {

              _scaffoldKey
                  .currentState
                  ?.openDrawer();
            },

            icon:
                const Icon(
              Icons.menu_rounded,

              color:
                  darkBlue,
            ),
          ),

          Container(
            width: 42,
            height: 42,

            decoration:
                BoxDecoration(
              shape:
                  BoxShape.circle,

              gradient:
                  const LinearGradient(
                colors: [
                  blue,
                  cyan,
                  green,
                ],
              ),

              boxShadow: [
                BoxShadow(
                  color:
                      blue.withOpacity(
                    0.22,
                  ),

                  blurRadius: 13,
                ),
              ],
            ),

            child:
                const Icon(
              Icons.smart_toy_rounded,

              color:
                  Colors.white,

              size: 22,
            ),
          ),

          const SizedBox(
            width: 10,
          ),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,

              children: [

                const Text(
                  'SignBridge AI',

                  style:
                      TextStyle(
                    color:
                        darkBlue,

                    fontSize:
                        18,

                    fontWeight:
                        FontWeight.w900,
                  ),
                ),

                Text(
                  _speakForMeMode
                      ? 'Speak for Me'
                      : _isListening
                          ? 'Listening nearby…'
                          : _signBridgeMode
                              ? 'SignBridge knowledge + app context'
                              : 'Intelligent assistant',

                  style:
                      TextStyle(
                    color:
                        _isListening
                            ? const Color(
                                0xFF00A878,
                              )
                            : softText,

                    fontSize:
                        9.5,

                    fontWeight:
                        FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          Container(
            padding:
                const EdgeInsets
                    .symmetric(
              horizontal: 9,
              vertical: 6,
            ),

            decoration:
                BoxDecoration(
              color:
                  const Color(
                0xFFEAF7F3,
              ),

              borderRadius:
                  BorderRadius.circular(
                20,
              ),
            ),

            child: Row(
              mainAxisSize:
                  MainAxisSize.min,

              children: [

                const CircleAvatar(
                  radius: 3.5,

                  backgroundColor:
                      green,
                ),

                const SizedBox(
                  width: 5,
                ),

                Text(
                  _isChatSending
                      ? 'THINKING'
                      : 'READY',

                  style:
                      const TextStyle(
                    color:
                        Color(
                      0xFF008E69,
                    ),

                    fontSize:
                        8,

                    fontWeight:
                        FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }


  // ============================================================
  // DRAWER
  // ============================================================

  Widget _buildDrawer() {

    return Drawer(
      backgroundColor:
          const Color(
        0xFFF7FBFE,
      ),

      child: SafeArea(
        child: Column(
          children: [

            Padding(
              padding:
                  const EdgeInsets
                      .fromLTRB(
                15,
                13,
                15,
                10,
              ),

              child: Row(
                children: [

                  Container(
                    width: 40,
                    height: 40,

                    decoration:
                        const BoxDecoration(
                      shape:
                          BoxShape.circle,

                      gradient:
                          LinearGradient(
                        colors: [
                          blue,
                          cyan,
                          green,
                        ],
                      ),
                    ),

                    child:
                        const Icon(
                      Icons
                          .smart_toy_rounded,

                      color:
                          Colors.white,

                      size: 21,
                    ),
                  ),

                  const SizedBox(
                    width: 9,
                  ),

                  const Expanded(
                    child: Text(
                      'SignBridge AI',

                      style:
                          TextStyle(
                        color:
                            darkBlue,

                        fontSize:
                            17,

                        fontWeight:
                            FontWeight.w900,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            Padding(
              padding:
                  const EdgeInsets
                      .symmetric(
                horizontal: 13,
              ),

              child: SizedBox(
                width:
                    double.infinity,

                child:
                    FilledButton.icon(
                  onPressed: () {

                    _createNewChat();
                  },

                  icon:
                      const Icon(
                    Icons.add_rounded,
                  ),

                  label:
                      const Text(
                    'New chat',
                  ),

                  style:
                      FilledButton
                          .styleFrom(
                    backgroundColor:
                        blue,

                    padding:
                        const EdgeInsets
                            .symmetric(
                      vertical: 12,
                    ),

                    shape:
                        RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.circular(
                        15,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(
              height: 12,
            ),

            const Padding(
              padding:
                  EdgeInsets
                      .symmetric(
                horizontal: 16,
              ),

              child: Align(
                alignment:
                    Alignment.centerLeft,

                child: Text(
                  'Saved conversations',

                  style:
                      TextStyle(
                    color:
                        softText,

                    fontSize:
                        10,

                    fontWeight:
                        FontWeight.w800,
                  ),
                ),
              ),
            ),

            const SizedBox(
              height: 5,
            ),

            Expanded(
              child:
                  _savedChats.isEmpty
                      ? const Center(
                          child: Text(
                            'No saved conversations yet',

                            style:
                                TextStyle(
                              color:
                                  softText,

                              fontSize:
                                  11,
                            ),
                          ),
                        )
                      : ListView.builder(

                          padding:
                              const EdgeInsets
                                  .symmetric(
                            horizontal: 8,
                          ),

                          itemCount:
                              _savedChats.length,

                          itemBuilder: (
                            context,
                            index,
                          ) {

                            final chat =
                                _savedChats[index];

                            final bool selected =
                                chat.id ==
                                    _currentChatId;

                            return Container(
                              margin:
                                  const EdgeInsets
                                      .only(
                                bottom: 4,
                              ),

                              decoration:
                                  BoxDecoration(
                                color:
                                    selected
                                        ? const Color(
                                            0xFFEAF4FF,
                                          )
                                        : Colors.transparent,

                                borderRadius:
                                    BorderRadius.circular(
                                  13,
                                ),
                              ),

                              child: ListTile(
                                dense: true,

                                leading:
                                    Icon(
                                  Icons
                                      .chat_bubble_outline_rounded,

                                  color:
                                      selected
                                          ? blue
                                          : softText,

                                  size:
                                      19,
                                ),

                                title:
                                    Text(
                                  chat.title,

                                  maxLines:
                                      1,

                                  overflow:
                                      TextOverflow.ellipsis,

                                  style:
                                      TextStyle(
                                    color:
                                        selected
                                            ? darkBlue
                                            : darkText,

                                    fontSize:
                                        11,

                                    fontWeight:
                                        selected
                                            ? FontWeight.w800
                                            : FontWeight.w600,
                                  ),
                                ),

                                trailing:
                                    IconButton(
                                  tooltip:
                                      'Delete',

                                  icon:
                                      const Icon(
                                    Icons
                                        .delete_outline_rounded,

                                    size:
                                        18,

                                    color:
                                        softText,
                                  ),

                                  onPressed: () {

                                    _deleteChat(
                                      chat,
                                    );
                                  },
                                ),

                                onTap: () {

                                  _openSavedChat(
                                    chat,
                                  );
                                },
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }


  // ============================================================
  // CHAT MESSAGE
  // ============================================================

  Widget _buildChatMessage(
    _ChatMessage message,
  ) {

    final bool user =
        message.isUser;

    return Align(
      alignment:
          user
              ? Alignment.centerRight
              : Alignment.centerLeft,

      child: Container(
        constraints:
            BoxConstraints(
          maxWidth:
              MediaQuery.of(
                    context,
                  ).size.width *
                  0.80,
        ),

        margin:
            const EdgeInsets
                .only(
          bottom: 12,
        ),

        padding:
            const EdgeInsets
                .fromLTRB(
          13,
          11,
          13,
          8,
        ),

        decoration:
            BoxDecoration(
          gradient:
              user
                  ? const LinearGradient(
                      colors: [
                        blue,
                        Color(
                          0xFF00A8D9,
                        ),
                        green,
                      ],
                    )
                  : null,

          color:
              user
                  ? null
                  : Colors.white,

          borderRadius:
              BorderRadius.only(
            topLeft:
                const Radius.circular(
              18,
            ),

            topRight:
                const Radius.circular(
              18,
            ),

            bottomLeft:
                Radius.circular(
              user
                  ? 18
                  : 5,
            ),

            bottomRight:
                Radius.circular(
              user
                  ? 5
                  : 18,
            ),
          ),

          boxShadow: [
            BoxShadow(
              color:
                  Colors.black
                      .withOpacity(
                0.04,
              ),

              blurRadius:
                  12,
            ),
          ],
        ),

        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,

          children: [

            Text(
              message.text,

              style: TextStyle(
                color:
                    user
                        ? Colors.white
                        : darkText,

                fontSize:
                    13,

                height:
                    1.45,
              ),
            ),

            const SizedBox(
              height: 6,
            ),

            Align(
              alignment:
                  Alignment.centerRight,

              child: InkWell(
                onTap: () =>
                    _copyText(
                  message.text,
                ),

                child: Row(
                  mainAxisSize:
                      MainAxisSize.min,

                  children: [

                    Icon(
                      Icons.copy_rounded,

                      size:
                          13,

                      color:
                          user
                              ? Colors.white
                                  .withOpacity(
                                  0.80,
                                )
                              : blue,
                    ),

                    const SizedBox(
                      width:
                          4,
                    ),

                    Text(
                      'Copy',

                      style:
                          TextStyle(
                        color:
                            user
                                ? Colors.white
                                    .withOpacity(
                                    0.80,
                                  )
                                : blue,

                        fontSize:
                            8.5,

                        fontWeight:
                            FontWeight.w700,
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
  }


  // ============================================================
  // AI LOADING
  // ============================================================

  Widget _buildAiLoading() {

    return Align(
      alignment:
          Alignment.centerLeft,

      child: Container(
        margin:
            const EdgeInsets
                .only(
          bottom: 12,
        ),

        padding:
            const EdgeInsets
                .symmetric(
          horizontal: 13,
          vertical: 10,
        ),

        decoration:
            BoxDecoration(
          color:
              Colors.white,

          borderRadius:
              BorderRadius.circular(
            17,
          ),
        ),

        child:
            const Row(
          mainAxisSize:
              MainAxisSize.min,

          children: [

            SizedBox(
              width:
                  14,
              height:
                  14,

              child:
                  CircularProgressIndicator(
                strokeWidth:
                    1.8,

                color:
                    blue,
              ),
            ),

            SizedBox(
              width:
                  8,
            ),

            Text(
              'SignBridge AI is thinking…',

              style:
                  TextStyle(
                color:
                    softText,

                fontSize:
                    10,
              ),
            ),
          ],
        ),
      ),
    );
  }


  // ============================================================
  // LIVE SPEECH CARD
  // ============================================================

  Widget _buildLiveSpeechCard() {

    final String displayed =
        _liveTranscript
                .trim()
                .isNotEmpty
            ? _liveTranscript.trim()
            : _lastHeardText.trim();

    final bool hasSpeech =
        displayed.isNotEmpty;

    return Container(
      margin:
          const EdgeInsets
              .only(
        top: 5,
        bottom: 10,
      ),

      padding:
          const EdgeInsets.all(
        12,
      ),

      decoration:
          BoxDecoration(
        color:
            Colors.white
                .withOpacity(
          0.91,
        ),

        borderRadius:
            BorderRadius.circular(
          20,
        ),

        border:
            Border.all(
          color:
              const Color(
            0xFFDCEBF4,
          ),
        ),

        boxShadow: [
          BoxShadow(
            color:
                blue.withOpacity(
              0.05,
            ),

            blurRadius:
                15,
          ),
        ],
      ),

      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,

        children: [

          Row(
            children: [

              Icon(
                _isListening
                    ? Icons
                        .graphic_eq_rounded
                    : Icons
                        .hearing_rounded,

                color:
                    _isListening
                        ? green
                        : blue,

                size:
                    20,
              ),

              const SizedBox(
                width: 7,
              ),

              Text(
                _isListening
                    ? 'Listening nearby…'
                    : 'Recent speech',

                style:
                    const TextStyle(
                  color:
                      darkBlue,

                  fontSize:
                      11.5,

                  fontWeight:
                      FontWeight.w800,
                ),
              ),

              const Spacer(),

              if (_isListening)
                Container(
                  padding:
                      const EdgeInsets
                          .symmetric(
                    horizontal:
                        7,
                    vertical:
                        4,
                  ),

                  decoration:
                      BoxDecoration(
                    color:
                        const Color(
                      0xFFE7FBF2,
                    ),

                    borderRadius:
                        BorderRadius.circular(
                      20,
                    ),
                  ),

                  child:
                      const Text(
                    'LIVE',

                    style:
                        TextStyle(
                      color:
                          Color(
                        0xFF009C70,
                      ),

                      fontSize:
                          8,

                      fontWeight:
                          FontWeight.w900,
                    ),
                  ),
                ),

              IconButton(
                constraints:
                    const BoxConstraints(),

                padding:
                    const EdgeInsets
                        .only(
                  left:
                      8,
                ),

                tooltip:
                    'Clear',

                onPressed:
                    _clearLiveSpeech,

                icon:
                    const Icon(
                  Icons.close_rounded,

                  color:
                      softText,

                  size:
                      18,
                ),
              ),
            ],
          ),

          const SizedBox(
            height: 8,
          ),

          // =====================================================
          // HEARD SPEECH + BUTTON BESIDE IT
          // =====================================================

          Row(
            crossAxisAlignment:
                CrossAxisAlignment.center,

            children: [

              Expanded(
                child: Text(
                  hasSpeech
                      ? displayed
                      : 'Listening for speech…',

                  style:
                      TextStyle(
                    color:
                        hasSpeech
                            ? darkText
                            : softText,

                    fontSize:
                        12.5,

                    height:
                        1.4,

                    fontWeight:
                        hasSpeech
                            ? FontWeight.w600
                            : FontWeight.w400,
                  ),
                ),
              ),

              if (hasSpeech) ...[

                const SizedBox(
                  width: 8,
                ),

                InkWell(
                  onTap:
                      _isGeneratingReplies
                          ? null
                          : _generateRepliesFromCurrentSpeech,

                  borderRadius:
                      BorderRadius.circular(
                    13,
                  ),

                  child:
                      AnimatedContainer(
                    duration:
                        const Duration(
                      milliseconds:
                          180,
                    ),

                    padding:
                        const EdgeInsets
                            .symmetric(
                      horizontal:
                          9,
                      vertical:
                          7,
                    ),

                    decoration:
                        BoxDecoration(
                      gradient:
                          _isGeneratingReplies
                              ? null
                              : const LinearGradient(
                                  colors: [
                                    blue,
                                    cyan,
                                    green,
                                  ],
                                ),

                      color:
                          _isGeneratingReplies
                              ? const Color(
                                  0xFFEAF3FF,
                                )
                              : null,

                      borderRadius:
                          BorderRadius.circular(
                        13,
                      ),
                    ),

                    child: Row(
                      mainAxisSize:
                          MainAxisSize.min,

                      children: [

                        if (_isGeneratingReplies)
                          const SizedBox(
                            width:
                                13,
                            height:
                                13,

                            child:
                                CircularProgressIndicator(
                              strokeWidth:
                                  1.7,

                              color:
                                  blue,
                            ),
                          )
                        else
                          const Icon(
                            Icons
                                .reply_all_rounded,

                            color:
                                Colors.white,

                            size:
                                14,
                          ),

                        const SizedBox(
                          width:
                              4,
                        ),

                        Text(
                          _isGeneratingReplies
                              ? 'Generating…'
                              : 'Generate replies',

                          style:
                              TextStyle(
                            color:
                                _isGeneratingReplies
                                    ? blue
                                    : Colors.white,

                            fontSize:
                                8.5,

                            fontWeight:
                                FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }


  // ============================================================
  // SMART REPLIES CARD
  // ============================================================

  Widget _buildSmartRepliesCard() {

    return Container(
      margin:
          const EdgeInsets
              .only(
        bottom: 13,
      ),

      padding:
          const EdgeInsets.all(
        13,
      ),

      decoration:
          BoxDecoration(
        color:
            Colors.white,

        borderRadius:
            BorderRadius.circular(
          21,
        ),

        border:
            Border.all(
          color:
              const Color(
            0xFFDDEBF4,
          ),
        ),
      ),

      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,

        children: [

          Row(
            children: [

              const Icon(
                Icons
                    .auto_awesome_rounded,

                color:
                    blue,

                size:
                    18,
              ),

              const SizedBox(
                width:
                    6,
              ),

              const Text(
                'Suggested replies',

                style:
                    TextStyle(
                  color:
                      darkBlue,

                  fontSize:
                      12,

                  fontWeight:
                      FontWeight.w900,
                ),
              ),

              const Spacer(),

              IconButton(
                constraints:
                    const BoxConstraints(),

                padding:
                    EdgeInsets.zero,

                onPressed: () {

                  setState(() {
                    _smartReplies = [];
                    _smartReplyError = null;
                  });
                },

                icon:
                    const Icon(
                  Icons.close_rounded,

                  color:
                      softText,

                  size:
                      17,
                ),
              ),
            ],
          ),

          if (_isGeneratingReplies) ...[

            const SizedBox(
              height:
                  12,
            ),

            const Center(
              child:
                  CircularProgressIndicator(
                strokeWidth:
                    2,

                color:
                    blue,
              ),
            ),

            const SizedBox(
              height:
                  8,
            ),

            const Center(
              child: Text(
                'Creating replies for exactly what was heard…',

                style:
                    TextStyle(
                  color:
                      softText,

                  fontSize:
                      9,
                ),
              ),
            ),
          ],

          if (_smartReplyError !=
              null) ...[

            const SizedBox(
              height:
                  8,
            ),

            Text(
              _smartReplyError!,

              style:
                  const TextStyle(
                color:
                    Color(
                  0xFFC94A4A,
                ),

                fontSize:
                    10,
              ),
            ),

            const SizedBox(
              height:
                  8,
            ),

            OutlinedButton.icon(
              onPressed:
                  _generateRepliesFromCurrentSpeech,

              icon:
                  const Icon(
                Icons.refresh_rounded,

                size:
                    16,
              ),

              label:
                  const Text(
                'Try again',
              ),
            ),
          ],

          if (_smartReplies
              .isNotEmpty) ...[

            const SizedBox(
              height:
                  7,
            ),

            ...List.generate(
              _smartReplies.length,
              (
                index,
              ) {

                final String reply =
                    _smartReplies[index];

                final String speakId =
                    'smart_reply_$index';

                final bool speaking =
                    _speakingId ==
                            speakId &&
                        _isTtsSpeaking;

                return AnimatedContainer(
                  duration:
                      const Duration(
                    milliseconds:
                        180,
                  ),

                  margin:
                      const EdgeInsets
                          .only(
                    bottom:
                        8,
                  ),

                  padding:
                      const EdgeInsets.all(
                    10,
                  ),

                  decoration:
                      BoxDecoration(
                    gradient:
                        speaking
                            ? LinearGradient(
                                colors: [
                                  blue.withOpacity(
                                    0.13,
                                  ),
                                  cyan.withOpacity(
                                    0.10,
                                  ),
                                  green.withOpacity(
                                    0.12,
                                  ),
                                ],
                              )
                            : null,

                    color:
                        speaking
                            ? null
                            : const Color(
                                0xFFF6FAFD,
                              ),

                    borderRadius:
                        BorderRadius.circular(
                      15,
                    ),

                    border:
                        Border.all(
                      color:
                          speaking
                              ? blue.withOpacity(
                                  0.45,
                                )
                              : const Color(
                                  0xFFE0EAF2,
                                ),

                      width:
                          speaking
                              ? 1.5
                              : 1,
                    ),
                  ),

                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,

                    children: [

                      Row(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,

                        children: [

                          Container(
                            width:
                                24,
                            height:
                                24,

                            alignment:
                                Alignment.center,

                            decoration:
                                BoxDecoration(
                              gradient:
                                  speaking
                                      ? const LinearGradient(
                                          colors: [
                                            blue,
                                            cyan,
                                            green,
                                          ],
                                        )
                                      : null,

                              color:
                                  speaking
                                      ? null
                                      : const Color(
                                          0xFFE8F3FF,
                                        ),

                              shape:
                                  BoxShape.circle,
                            ),

                            child:
                                speaking
                                    ? const Icon(
                                        Icons
                                            .graphic_eq_rounded,

                                        color:
                                            Colors.white,

                                        size:
                                            14,
                                      )
                                    : Text(
                                        '${index + 1}',

                                        style:
                                            const TextStyle(
                                          color:
                                              blue,

                                          fontSize:
                                              9,

                                          fontWeight:
                                              FontWeight.w900,
                                        ),
                                      ),
                          ),

                          const SizedBox(
                            width:
                                8,
                          ),

                          Expanded(
                            child: Text(
                              reply,

                              style:
                                  const TextStyle(
                                color:
                                    darkText,

                                fontSize:
                                    11.5,

                                height:
                                    1.4,

                                fontWeight:
                                    FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(
                        height:
                            7,
                      ),

                      Row(
                        mainAxisAlignment:
                            MainAxisAlignment.end,

                        children: [

                          _smallAction(
                            icon:
                                Icons.edit_rounded,

                            label:
                                'Use',

                            onTap: () async {

                              await _setSpeakForMeMode(
                                true,
                              );

                              if (!mounted) {
                                return;
                              }

                              setState(() {

                                _textController.text =
                                    reply;

                                _textController.selection =
                                    TextSelection
                                        .fromPosition(
                                  TextPosition(
                                    offset:
                                        reply.length,
                                  ),
                                );
                              });
                            },
                          ),

                          const SizedBox(
                            width:
                                10,
                          ),

                          _smallAction(
                            icon:
                                Icons.copy_rounded,

                            label:
                                'Copy',

                            onTap: () =>
                                _copyText(
                              reply,
                            ),
                          ),

                          const SizedBox(
                            width:
                                10,
                          ),

                          _smallAction(
                            icon:
                                speaking
                                    ? Icons
                                        .graphic_eq_rounded
                                    : Icons
                                        .volume_up_rounded,

                            label:
                                speaking
                                    ? 'Speaking…'
                                    : 'Speak',

                            active:
                                speaking,

                            onTap: () =>
                                _speakText(
                              reply,

                              id:
                                  speakId,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }


  // ============================================================
  // SPEAK FOR ME RESULT
  // ============================================================

  Widget _buildSpeakForMeResult() {

    final String result =
        _speakForMeResult!;

    final bool speaking =
        _speakingId ==
                'speak_for_me_result' &&
            _isTtsSpeaking;

    return AnimatedContainer(
      duration:
          const Duration(
        milliseconds:
            180,
      ),

      margin:
          const EdgeInsets
              .fromLTRB(
        12,
        0,
        12,
        7,
      ),

      padding:
          const EdgeInsets.all(
        11,
      ),

      decoration:
          BoxDecoration(
        gradient:
            speaking
                ? LinearGradient(
                    colors: [
                      blue.withOpacity(
                        0.13,
                      ),
                      cyan.withOpacity(
                        0.10,
                      ),
                      green.withOpacity(
                        0.13,
                      ),
                    ],
                  )
                : null,

        color:
            speaking
                ? null
                : const Color(
                    0xFFF0F8FF,
                  ),

        borderRadius:
            BorderRadius.circular(
          17,
        ),

        border:
            Border.all(
          color:
              speaking
                  ? blue
                  : const Color(
                      0xFFD5E8F6,
                    ),

          width:
              speaking
                  ? 1.5
                  : 1,
        ),
      ),

      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,

        children: [

          Row(
            children: [

              Icon(
                speaking
                    ? Icons
                        .graphic_eq_rounded
                    : Icons
                        .record_voice_over_rounded,

                color:
                    speaking
                        ? green
                        : blue,

                size:
                    18,
              ),

              const SizedBox(
                width:
                    6,
              ),

              Text(
                speaking
                    ? 'Speaking…'
                    : 'Ready to speak',

                style:
                    TextStyle(
                  color:
                      speaking
                          ? const Color(
                              0xFF008C67,
                            )
                          : darkBlue,

                  fontSize:
                      10,

                  fontWeight:
                      FontWeight.w900,
                ),
              ),

              const Spacer(),

              IconButton(
                constraints:
                    const BoxConstraints(),

                padding:
                    EdgeInsets.zero,

                onPressed: () {

                  _tts.stop();

                  setState(() {
                    _speakForMeResult = null;
                  });
                },

                icon:
                    const Icon(
                  Icons.close_rounded,

                  color:
                      softText,

                  size:
                      17,
                ),
              ),
            ],
          ),

          const SizedBox(
            height:
                7,
          ),

          Text(
            result,

            style:
                const TextStyle(
              color:
                  darkText,

              fontSize:
                  12.5,

              height:
                  1.4,

              fontWeight:
                  FontWeight.w600,
            ),
          ),

          if (_speakFallbackUsed) ...[

            const SizedBox(
              height:
                  5,
            ),

            const Text(
              'AI was unavailable, so your original wording was used.',

              style:
                  TextStyle(
                color:
                    softText,

                fontSize:
                    8,
              ),
            ),
          ],

          const SizedBox(
            height:
                8,
          ),

          Row(
            children: [

              FilledButton.icon(
                onPressed: () =>
                    _speakText(
                  result,

                  id:
                      'speak_for_me_result',
                ),

                icon: Icon(
                  speaking
                      ? Icons
                          .graphic_eq_rounded
                      : Icons
                          .replay_rounded,

                  size:
                      16,
                ),

                label: Text(
                  speaking
                      ? 'Speaking…'
                      : 'Replay',
                ),

                style:
                    FilledButton
                        .styleFrom(
                  backgroundColor:
                      speaking
                          ? green
                          : blue,

                  visualDensity:
                      VisualDensity.compact,

                  textStyle:
                      const TextStyle(
                    fontSize:
                        9,
                  ),
                ),
              ),

              const SizedBox(
                width:
                    8,
              ),

              OutlinedButton.icon(
                onPressed: () =>
                    _copyText(
                  result,
                ),

                icon:
                    const Icon(
                  Icons.copy_rounded,

                  size:
                      15,
                ),

                label:
                    const Text(
                  'Copy',
                ),

                style:
                    OutlinedButton
                        .styleFrom(
                  foregroundColor:
                      blue,

                  visualDensity:
                      VisualDensity.compact,

                  textStyle:
                      const TextStyle(
                    fontSize:
                        9,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }


  // ============================================================
  // BOTTOM AREA
  // ============================================================

  Widget _buildBottomArea() {

    return Container(
      padding:
          EdgeInsets.fromLTRB(
        10,
        6,
        10,
        8 +
            MediaQuery.of(
              context,
            ).padding.bottom,
      ),

      decoration:
          BoxDecoration(
        color:
            Colors.white,

        boxShadow: [
          BoxShadow(
            color:
                Colors.black
                    .withOpacity(
              0.06,
            ),

            blurRadius:
                16,

            offset:
                const Offset(
              0,
              -5,
            ),
          ),
        ],
      ),

      child: Column(
        mainAxisSize:
            MainAxisSize.min,

        children: [

          // =====================================================
          // COMPACT TOOL BAR
          // Generate replies is NOT here anymore.
          // It is beside the heard speech.
          // =====================================================

          SizedBox(
            height:
                31,

            child:
                SingleChildScrollView(
              scrollDirection:
                  Axis.horizontal,

              child: Row(
                children: [

                  _toolChip(
                    icon:
                        _isListening
                            ? Icons
                                .stop_rounded
                            : Icons
                                .hearing_rounded,

                    label:
                        _isListening
                            ? 'Stop listening'
                            : _liveSpeechWanted
                                ? 'Listen again'
                                : 'Live speech',

                    active:
                        _isListening ||
                            _liveSpeechWanted,

                    onTap:
                        _toggleLiveConversation,
                  ),

                  _toolChip(
                    icon:
                        Icons
                            .record_voice_over_rounded,

                    label:
                        'Speak for me',

                    active:
                        _speakForMeMode,

                    onTap: () async {

                      await _setSpeakForMeMode(
                        !_speakForMeMode,
                      );
                    },
                  ),

                  _toolChip(
                    icon:
                        Icons.auto_awesome_rounded,

                    label:
                        'SignBridge',

                    active:
                        _signBridgeMode,
                    onTap: () {
                      _toggleSignBridgeMode();
                    },
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(
            height:
                6,
          ),

          // =====================================================
          // ACTIVE SPEAK MODE LABEL
          // =====================================================

          if (_speakForMeMode)
            Padding(
              padding:
                  const EdgeInsets
                      .only(
                bottom:
                    5,
              ),

              child: Row(
                children: [

                  Container(
                    padding:
                        const EdgeInsets
                            .symmetric(
                      horizontal:
                          8,
                      vertical:
                          4,
                    ),

                    decoration:
                        BoxDecoration(
                      gradient:
                          LinearGradient(
                        colors: [
                          blue.withOpacity(
                            0.10,
                          ),
                          green.withOpacity(
                            0.10,
                          ),
                        ],
                      ),

                      borderRadius:
                          BorderRadius.circular(
                        15,
                      ),
                    ),

                    child:
                        const Text(
                      'SPEAK FOR ME',

                      style:
                          TextStyle(
                        color:
                            blue,

                        fontSize:
                            8,

                        fontWeight:
                            FontWeight.w900,
                      ),
                    ),
                  ),

                  const SizedBox(
                    width:
                        7,
                  ),

                  const Expanded(
                    child: Text(
                      'The phone will speak exactly what you type.',

                      style:
                          TextStyle(
                        color:
                            softText,

                        fontSize:
                            8.5,
                      ),
                    ),
                  ),

                  InkWell(
                    onTap: () async {

                      await _setSpeakForMeMode(
                        false,
                      );
                    },

                    child:
                        const Row(
                      children: [

                        Icon(
                          Icons
                              .close_rounded,

                          size:
                              14,

                          color:
                              softText,
                        ),

                        SizedBox(
                          width:
                              2,
                        ),

                        Text(
                          'Chat',

                          style:
                              TextStyle(
                            color:
                                softText,

                            fontSize:
                                8.5,

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

          if (_signBridgeMode && !_speakForMeMode)
            Padding(
              padding: const EdgeInsets.only(bottom: 5),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          blue.withOpacity(0.10),
                          green.withOpacity(0.10),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: const Text(
                      'SIGNBRIDGE AI',
                      style: TextStyle(
                        color: blue,
                        fontSize: 8,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  const SizedBox(width: 7),
                  const Expanded(
                    child: Text(
                      'Ask anything — SignBridge, your progress, recent activity, or general questions.',
                      style: TextStyle(color: softText, fontSize: 8.5),
                    ),
                  ),
                  InkWell(
                    onTap: () { _toggleSignBridgeMode(); },
                    child: const Icon(Icons.close_rounded, size: 14, color: softText),
                  ),
                ],
              ),
            ),

          // =====================================================
          // INPUT
          // =====================================================

          Row(
            crossAxisAlignment:
                CrossAxisAlignment.end,

            children: [

              Container(
                width:
                    45,
                height:
                    45,

                decoration:
                    BoxDecoration(
                  color:
                      const Color(
                    0xFFEAF4FF,
                  ),

                  borderRadius:
                      BorderRadius.circular(
                    15,
                  ),
                ),

                child:
                    const Icon(
                  Icons.add_rounded,

                  color:
                      blue,
                ),
              ),

              const SizedBox(
                width:
                    7,
              ),

              Expanded(
                child: Container(
                  constraints:
                      const BoxConstraints(
                    minHeight:
                        45,

                    maxHeight:
                        120,
                  ),

                  decoration:
                      BoxDecoration(
                    color:
                        const Color(
                      0xFFF5F8FC,
                    ),

                    borderRadius:
                        BorderRadius.circular(
                      16,
                    ),

                    border:
                        Border.all(
                      color:
                          const Color(
                        0xFFDDE7F0,
                      ),
                    ),
                  ),

                  child: TextField(
                    controller:
                        _textController,

                    minLines:
                        1,

                    maxLines:
                        4,

                    enabled:
                        !_isChatSending &&
                            !_isPreparingSpeech,

                    textCapitalization:
                        TextCapitalization
                            .sentences,

                    decoration:
                        InputDecoration(
                      border:
                          InputBorder.none,

                      hintText:
                          _speakForMeMode
                              ? 'Type what you want the phone to say…'
                              : _signBridgeMode
                                  ? 'Ask SignBridge AI anything…'
                                  : 'Message SignBridge AI…',

                      hintStyle:
                          const TextStyle(
                        color:
                            Color(
                          0xFF8D99A9,
                        ),

                        fontSize:
                            11,
                      ),

                      contentPadding:
                          const EdgeInsets
                              .symmetric(
                        horizontal:
                            12,

                        vertical:
                            12,
                      ),
                    ),

                    onSubmitted: (_) {

                      if (!_isChatSending &&
                          !_isPreparingSpeech) {

                        _sendInput();
                      }
                    },
                  ),
                ),
              ),

              const SizedBox(
                width:
                    7,
              ),

              InkWell(
                onTap:
                    _isChatSending ||
                            _isPreparingSpeech
                        ? null
                        : _sendInput,

                borderRadius:
                    BorderRadius.circular(
                  15,
                ),

                child: Container(
                  width:
                      45,
                  height:
                      45,

                  decoration:
                      BoxDecoration(
                    gradient:
                        const LinearGradient(
                      colors: [
                        blue,
                        cyan,
                        green,
                      ],
                    ),

                    borderRadius:
                        BorderRadius.circular(
                      15,
                    ),

                    boxShadow: [
                      BoxShadow(
                        color:
                            blue.withOpacity(
                          0.22,
                        ),

                        blurRadius:
                            11,

                        offset:
                            const Offset(
                          0,
                          4,
                        ),
                      ),
                    ],
                  ),

                  child:
                      _isChatSending ||
                              _isPreparingSpeech
                          ? const Padding(
                              padding:
                                  EdgeInsets.all(
                                13,
                              ),

                              child:
                                  CircularProgressIndicator(
                                strokeWidth:
                                    2,

                                color:
                                    Colors.white,
                              ),
                            )
                          : Icon(
                              _speakForMeMode
                                  ? Icons
                                      .volume_up_rounded
                                  : Icons
                                      .arrow_upward_rounded,

                              color:
                                  Colors.white,

                              size:
                                  22,
                            ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }


  // ============================================================
  // TOOL CHIP
  // ============================================================

  Widget _toolChip({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool active = false,
  }) {

    return Padding(
      padding:
          const EdgeInsets
              .only(
        right:
            6,
      ),

      child: InkWell(
        onTap:
            onTap,

        borderRadius:
            BorderRadius.circular(
          20,
        ),

        child:
            AnimatedContainer(
          duration:
              const Duration(
            milliseconds:
                170,
          ),

          padding:
              const EdgeInsets
                  .symmetric(
            horizontal:
                9,
            vertical:
                6,
          ),

          decoration:
              BoxDecoration(
            gradient:
                active
                    ? const LinearGradient(
                        colors: [
                          blue,
                          cyan,
                          green,
                        ],
                      )
                    : null,

            color:
                active
                    ? null
                    : const Color(
                        0xFFF0F6FB,
                      ),

            borderRadius:
                BorderRadius.circular(
              20,
            ),
          ),

          child: Row(
            mainAxisSize:
                MainAxisSize.min,

            children: [

              Icon(
                icon,

                color:
                    active
                        ? Colors.white
                        : blue,

                size:
                    13,
              ),

              const SizedBox(
                width:
                    4,
              ),

              Text(
                label,

                style:
                    TextStyle(
                  color:
                      active
                          ? Colors.white
                          : darkText,

                  fontSize:
                      8.5,

                  fontWeight:
                      FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }


  // ============================================================
  // SMALL ACTION
  // ============================================================

  Widget _smallAction({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool active = false,
  }) {

    return InkWell(
      onTap:
          onTap,

      borderRadius:
          BorderRadius.circular(
        10,
      ),

      child: Padding(
        padding:
            const EdgeInsets
                .symmetric(
          horizontal:
              3,
          vertical:
              3,
        ),

        child: Row(
          mainAxisSize:
              MainAxisSize.min,

          children: [

            Icon(
              icon,

              color:
                  active
                      ? green
                      : blue,

              size:
                  14,
            ),

            const SizedBox(
              width:
                  3,
            ),

            Text(
              label,

              style:
                  TextStyle(
                color:
                    active
                        ? const Color(
                            0xFF008F69,
                          )
                        : blue,

                fontSize:
                    8.5,

                fontWeight:
                    FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}


// ============================================================
// CHAT MESSAGE MODEL
// ============================================================

class _ChatMessage {

  final String text;

  final bool isUser;

  final bool isWelcome;

  const _ChatMessage({
    required this.text,
    required this.isUser,
    this.isWelcome = false,
  });


  Map<String, dynamic> toJson() {

    return {
      'text':
          text,

      'is_user':
          isUser,

      'is_welcome':
          isWelcome,
    };
  }


  factory _ChatMessage.fromJson(
    Map<String, dynamic> json,
  ) {

    return _ChatMessage(
      text:
          (json['text'] ?? '')
              .toString(),

      isUser:
          json['is_user'] ==
              true,

      isWelcome:
          json['is_welcome'] ==
              true,
    );
  }
}


// ============================================================
// CHAT SESSION MODEL
// ============================================================

class _ChatSession {

  final String id;

  final String title;

  final int updatedAt;

  final List<_ChatMessage>
      messages;


  const _ChatSession({
    required this.id,
    required this.title,
    required this.updatedAt,
    required this.messages,
  });


  Map<String, dynamic> toJson() {

    return {
      'id':
          id,

      'title':
          title,

      'updated_at':
          updatedAt,

      'messages':
          messages
              .map(
                (
                  message,
                ) =>
                    message
                        .toJson(),
              )
              .toList(),
    };
  }


  factory _ChatSession.fromJson(
    Map<String, dynamic> json,
  ) {

    final dynamic rawMessages =
        json['messages'];

    final List<_ChatMessage>
        parsedMessages = [];

    if (rawMessages is List) {

      for (final item
          in rawMessages) {

        if (item is Map) {

          parsedMessages.add(
            _ChatMessage.fromJson(
              Map<String, dynamic>
                  .from(
                item,
              ),
            ),
          );
        }
      }
    }

    return _ChatSession(
      id:
          (json['id'] ?? '')
              .toString(),

      title:
          (json['title'] ??
                  'Conversation')
              .toString(),

      updatedAt:
          int.tryParse(
                (
                  json['updated_at'] ??
                      0
                ).toString(),
              ) ??
              0,

      messages:
          parsedMessages,
    );
  }
}