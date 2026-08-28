import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class SignCameraTranslationPage extends StatefulWidget {
  const SignCameraTranslationPage({super.key});

  @override
  State<SignCameraTranslationPage> createState() =>
      _SignCameraTranslationPageState();
}

class _SignCameraTranslationPageState
    extends State<SignCameraTranslationPage> {
  // ============================================================
  // COLORS
  // ============================================================

  static const Color purple = Color(0xFF7B2FF7);
  static const Color blue = Color(0xFF536DFE);
  static const Color orange = Color(0xFFFF8C42);
  static const Color darkText = Color(0xFF20243A);

  // ============================================================
  // BACKEND
  // ============================================================

  // إذا كنت تشغلين Flutter على Windows:
  static const String _baseUrl = 'http://192.168.0.118:5000';

  // ============================================================
  // STATE
  // ============================================================

  Uint8List? _cameraFrame;

  Timer? _frameTimer;
  Timer? _statusTimer;

  bool _loadingFrame = false;
  bool _loadingStatus = false;

  bool _backendConnected = false;
  bool _isTranslating = false;

  String _aiState = 'CONNECTING';
  String _prediction = 'Waiting...';
  String _reason = '';

  double _confidence = 0.0;

  int _hands = 0;

  List<String> _history = [];

  // ============================================================
  // INIT
  // ============================================================

  @override
  void initState() {
    super.initState();

    _checkBackend();
    _startPolling();
  }

  // ============================================================
  // CHECK BACKEND
  // ============================================================

  Future<void> _checkBackend() async {
    try {
      final response = await http
          .get(
            Uri.parse('$_baseUrl/api/health'),
          )
          .timeout(
            const Duration(seconds: 3),
          );

      if (!mounted) return;

      setState(() {
        _backendConnected = response.statusCode == 200;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _backendConnected = false;
      });
    }
  }

  // ============================================================
  // POLLING
  // ============================================================

  void _startPolling() {
    // Camera preview
    _frameTimer = Timer.periodic(
      const Duration(milliseconds: 120),
      (_) {
        _fetchCameraFrame();
      },
    );

    // AI result
    _statusTimer = Timer.periodic(
      const Duration(milliseconds: 250),
      (_) {
        _fetchStatus();
      },
    );

    _fetchCameraFrame();
    _fetchStatus();
  }

  // ============================================================
  // GET CAMERA FRAME
  // ============================================================

  Future<void> _fetchCameraFrame() async {
    if (_loadingFrame) return;

    _loadingFrame = true;

    try {
      final response = await http
          .get(
            Uri.parse(
              '$_baseUrl/api/sign/frame',
            ),
          )
          .timeout(
            const Duration(seconds: 2),
          );

      if (!mounted) return;

      if (response.statusCode == 200 &&
          response.bodyBytes.isNotEmpty) {
        setState(() {
          _cameraFrame = response.bodyBytes;
          _backendConnected = true;
        });
      }
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _backendConnected = false;
      });
    } finally {
      _loadingFrame = false;
    }
  }

  // ============================================================
  // GET AI STATUS / RESULT
  // ============================================================

  Future<void> _fetchStatus() async {
    if (_loadingStatus) return;

    _loadingStatus = true;

    try {
      final response = await http
          .get(
            Uri.parse(
              '$_baseUrl/api/sign/status',
            ),
          )
          .timeout(
            const Duration(seconds: 2),
          );

      if (response.statusCode != 200) {
        return;
      }

      final dynamic decoded =
          jsonDecode(response.body);

      if (decoded is! Map<String, dynamic>) {
        return;
      }

      if (!mounted) return;

      final String state =
          decoded['state']?.toString() ??
              'READY';

      final dynamic rawLabel =
          decoded['label'];

      final String? label =
          rawLabel?.toString();

      final dynamic rawConfidence =
          decoded['confidence'];

      final double confidence =
          rawConfidence is num
              ? rawConfidence.toDouble()
              : 0.0;

      final dynamic rawHands =
          decoded['hands'];

      final int hands =
          rawHands is num
              ? rawHands.toInt()
              : 0;

      final List<String> history =
          List<String>.from(
        decoded['history'] ?? const [],
      );

      setState(() {
        _backendConnected = true;

        _isTranslating =
            decoded['enabled'] == true;

        _aiState = state;

        _confidence = confidence;

        _hands = hands;

        _reason =
            decoded['reason']
                    ?.toString() ??
                '';

        _history = history;

        if (label != null &&
            label.isNotEmpty) {
          _prediction = label;
        } else {
          _prediction =
              _textForState(state);
        }
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _backendConnected = false;
        _aiState = 'OFFLINE';
      });
    } finally {
      _loadingStatus = false;
    }
  }

  // ============================================================
  // TEXT ACCORDING TO AI STATE
  // ============================================================

  String _textForState(String state) {
    switch (state) {
      case 'WAITING':
        return 'Show a sign';

      case 'RECORDING':
        return 'Reading sign...';

      case 'ACCEPTED':
        return 'Sign detected';

      case 'UNKNOWN':
        return 'Unknown sign';

      case 'PAUSED':
        return 'Translation paused';

      case 'ERROR':
        return 'AI error';

      default:
        return 'Waiting...';
    }
  }

  // ============================================================
  // START / STOP AI
  // ============================================================

  Future<void> _toggleTranslation() async {
    final bool shouldStart =
        !_isTranslating;

    final String endpoint =
        shouldStart
            ? '/api/sign/start'
            : '/api/sign/stop';

    try {
      final response = await http
          .post(
            Uri.parse(
              '$_baseUrl$endpoint',
            ),
          )
          .timeout(
            const Duration(seconds: 3),
          );

      if (response.statusCode != 200) {
        throw Exception(
          'Backend error ${response.statusCode}',
        );
      }

      if (!mounted) return;

      setState(() {
        _isTranslating = shouldStart;

        if (shouldStart) {
          _aiState = 'WAITING';
          _prediction = 'Show a sign';
          _confidence = 0.0;
        } else {
          _aiState = 'PAUSED';
          _prediction =
              'Translation paused';
          _confidence = 0.0;
        }
      });

      await _fetchStatus();
    } catch (error) {
      _showMessage(
        'Cannot connect to the AI backend.',
      );
    }
  }

  // ============================================================
  // CLEAR
  // ============================================================

  Future<void> _clearHistory() async {
    try {
      await http
          .post(
            Uri.parse(
              '$_baseUrl/api/sign/reset',
            ),
          )
          .timeout(
            const Duration(seconds: 3),
          );

      if (!mounted) return;

      setState(() {
        _history.clear();
        _confidence = 0.0;

        _prediction =
            _isTranslating
                ? 'Show a sign'
                : 'Translation paused';
      });
    } catch (error) {
      _showMessage(
        'Could not clear history.',
      );
    }
  }

  // ============================================================
  // MESSAGE
  // ============================================================

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          behavior:
              SnackBarBehavior.floating,
        ),
      );
  }

  // ============================================================
  // DISPOSE
  // ============================================================

  @override
  void dispose() {
    _frameTimer?.cancel();
    _statusTimer?.cancel();

    super.dispose();
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor:
          const Color(0xFFF8F9FD),

      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),

            Expanded(
              child: SingleChildScrollView(
                padding:
                    const EdgeInsets.fromLTRB(
                  16,
                  4,
                  16,
                  24,
                ),

                child: Column(
                  children: [
                    _buildCamera(),

                    const SizedBox(
                      height: 14,
                    ),

                    _buildStatus(),

                    const SizedBox(
                      height: 14,
                    ),

                    _buildResult(),

                    const SizedBox(
                      height: 14,
                    ),

                    _buildStartButton(),

                    const SizedBox(
                      height: 18,
                    ),

                    _buildHistory(),
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
  // HEADER
  // ============================================================

  Widget _buildHeader() {
    return Padding(
      padding:
          const EdgeInsets.fromLTRB(
        6,
        10,
        16,
        10,
      ),

      child: Row(
        children: [
          IconButton(
            onPressed: () {
              Navigator.pop(context);
            },
            icon: const Icon(
              Icons
                  .arrow_back_ios_new_rounded,
              color: darkText,
            ),
          ),

          Container(
            width: 46,
            height: 46,

            decoration: BoxDecoration(
              gradient:
                  const LinearGradient(
                begin:
                    Alignment.topLeft,
                end:
                    Alignment.bottomRight,
                colors: [
                  purple,
                  blue,
                ],
              ),

              borderRadius:
                  BorderRadius.circular(15),

              boxShadow: [
                BoxShadow(
                  color: purple.withValues(
                    alpha: 0.25,
                  ),
                  blurRadius: 12,
                  offset:
                      const Offset(0, 5),
                ),
              ],
            ),

            child: const Stack(
              alignment: Alignment.center,
              children: [
                Icon(
                  Icons.camera_alt_rounded,
                  color: Colors.white,
                  size: 25,
                ),

                Positioned(
                  right: 4,
                  top: 4,
                  child: Text(
                    'AI',
                    style: TextStyle(
                      color:
                          Color(0xFFFFD166),
                      fontSize: 7,
                      fontWeight:
                          FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(width: 11),

          const Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  'Sign Camera',
                  style: TextStyle(
                    color: darkText,
                    fontSize: 20,
                    fontWeight:
                        FontWeight.w900,
                  ),
                ),

                SizedBox(height: 2),

                Text(
                  'Real-time AI sign translation',
                  style: TextStyle(
                    color:
                        Color(0xFF7B8494),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),

          _buildConnectionBadge(),
        ],
      ),
    );
  }

  Widget _buildConnectionBadge() {
    final Color color =
        _backendConnected
            ? const Color(0xFF28A65A)
            : const Color(0xFFE53935);

    return Container(
      padding:
          const EdgeInsets.symmetric(
        horizontal: 9,
        vertical: 7,
      ),

      decoration: BoxDecoration(
        color: color.withValues(
          alpha: 0.10,
        ),
        borderRadius:
            BorderRadius.circular(13),
      ),

      child: Row(
        mainAxisSize:
            MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(
              color: color,
              shape:
                  BoxShape.circle,
            ),
          ),

          const SizedBox(width: 5),

          Text(
            _backendConnected
                ? 'AI Ready'
                : 'Offline',
            style: TextStyle(
              color: color,
              fontSize: 10,
              fontWeight:
                  FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // CAMERA
  // ============================================================

  Widget _buildCamera() {
    return AspectRatio(
      aspectRatio: 4 / 3,

      child: Container(
        width: double.infinity,

        decoration: BoxDecoration(
          color:
              const Color(0xFF151926),
          borderRadius:
              BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: Colors.black
                  .withValues(alpha: 0.13),
              blurRadius: 18,
              offset:
                  const Offset(0, 8),
            ),
          ],
        ),

        clipBehavior:
            Clip.antiAlias,

        child: Stack(
          fit: StackFit.expand,
          children: [
            if (_cameraFrame != null)
              Image.memory(
                _cameraFrame!,
                fit: BoxFit.cover,
                gaplessPlayback: true,
              )
            else
              _buildCameraLoading(),

            Positioned(
              top: 14,
              left: 14,
              child: _buildLiveBadge(),
            ),

            Positioned(
              right: 14,
              bottom: 14,
              child: _buildHandsBadge(),
            ),

            if (!_backendConnected)
              Container(
                color: Colors.black
                    .withValues(
                  alpha: 0.55,
                ),
                child: const Center(
                  child: Column(
                    mainAxisSize:
                        MainAxisSize.min,
                    children: [
                      Icon(
                        Icons
                            .cloud_off_rounded,
                        color:
                            Colors.white,
                        size: 40,
                      ),

                      SizedBox(height: 10),

                      Text(
                        'AI backend is offline',
                        style: TextStyle(
                          color:
                              Colors.white,
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

  Widget _buildCameraLoading() {
    return const Center(
      child: Column(
        mainAxisSize:
            MainAxisSize.min,
        children: [
          CircularProgressIndicator(
            color: Colors.white,
          ),

          SizedBox(height: 12),

          Text(
            'Connecting to camera...',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveBadge() {
    return Container(
      padding:
          const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: Colors.black
            .withValues(alpha: 0.55),
        borderRadius:
            BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: _isTranslating
                  ? const Color(
                      0xFF52F08B,
                    )
                  : Colors.white54,
              shape:
                  BoxShape.circle,
            ),
          ),

          const SizedBox(width: 6),

          Text(
            _isTranslating
                ? 'LIVE AI'
                : 'READY',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight:
                  FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHandsBadge() {
    return Container(
      padding:
          const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: Colors.black
            .withValues(alpha: 0.55),
        borderRadius:
            BorderRadius.circular(15),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.back_hand_rounded,
            color: Colors.white,
            size: 14,
          ),

          const SizedBox(width: 5),

          Text(
            '$_hands',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 11,
              fontWeight:
                  FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // STATUS
  // ============================================================

  Widget _buildStatus() {
    Color color;

    switch (_aiState) {
      case 'RECORDING':
        color = orange;
        break;

      case 'ACCEPTED':
        color =
            const Color(0xFF26A65B);
        break;

      case 'UNKNOWN':
      case 'ERROR':
        color =
            const Color(0xFFE53935);
        break;

      case 'PAUSED':
        color =
            const Color(0xFF9AA4B2);
        break;

      default:
        color = purple;
    }

    return Container(
      width: double.infinity,
      padding:
          const EdgeInsets.symmetric(
        horizontal: 15,
        vertical: 12,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius:
            BorderRadius.circular(17),
        border: Border.all(
          color:
              const Color(0xFFE6E9F0),
        ),
      ),

      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              color: color,
              shape:
                  BoxShape.circle,
            ),
          ),

          const SizedBox(width: 9),

          const Text(
            'AI Status',
            style: TextStyle(
              color:
                  Color(0xFF737D8E),
              fontSize: 12,
              fontWeight:
                  FontWeight.w700,
            ),
          ),

          const Spacer(),

          Text(
            _aiState,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight:
                  FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // RESULT
  // ============================================================

  Widget _buildResult() {
    return Container(
      width: double.infinity,

      padding:
          const EdgeInsets.all(20),

      decoration: BoxDecoration(
        gradient:
            const LinearGradient(
          begin:
              Alignment.topLeft,
          end:
              Alignment.bottomRight,
          colors: [
            Color(0xFFF5F0FF),
            Color(0xFFF0F4FF),
            Color(0xFFFFF5EC),
          ],
        ),

        borderRadius:
            BorderRadius.circular(25),

        border: Border.all(
          color:
              const Color(0xFFE5D9FA),
        ),
      ),

      child: Column(
        children: [
          const Row(
            children: [
              Icon(
                Icons
                    .auto_awesome_rounded,
                color: purple,
                size: 18,
              ),

              SizedBox(width: 7),

              Text(
                'DETECTED SIGN',
                style: TextStyle(
                  color:
                      Color(0xFF697386),
                  fontSize: 11,
                  letterSpacing: 0.8,
                  fontWeight:
                      FontWeight.w900,
                ),
              ),
            ],
          ),

          const SizedBox(height: 19),

          AnimatedSwitcher(
            duration:
                const Duration(
              milliseconds: 200,
            ),
            child: Text(
              _prediction.toUpperCase(),
              key: ValueKey(
                _prediction,
              ),
              textAlign:
                  TextAlign.center,
              style: const TextStyle(
                color: darkText,
                fontSize: 30,
                fontWeight:
                    FontWeight.w900,
              ),
            ),
          ),

          if (_confidence > 0) ...[
            const SizedBox(height: 16),

            ClipRRect(
              borderRadius:
                  BorderRadius.circular(8),
              child:
                  LinearProgressIndicator(
                value: _confidence
                    .clamp(
                  0.0,
                  1.0,
                ),
                minHeight: 7,
                backgroundColor:
                    Colors.white,
                color: purple,
              ),
            ),

            const SizedBox(height: 8),

            Text(
              'Confidence ${(100 * _confidence).toStringAsFixed(1)}%',
              style: const TextStyle(
                color:
                    Color(0xFF727C8D),
                fontSize: 11,
                fontWeight:
                    FontWeight.w700,
              ),
            ),
          ],

          if (_reason.isNotEmpty &&
              _aiState == 'UNKNOWN') ...[
            const SizedBox(height: 8),

            Text(
              _reason,
              style: const TextStyle(
                color:
                    Color(0xFFE53935),
                fontSize: 10,
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ============================================================
  // START / STOP BUTTON
  // ============================================================

  Widget _buildStartButton() {
    final List<Color> colors =
        _isTranslating
            ? const [
                Color(0xFFE53935),
                Color(0xFFFF7043),
              ]
            : const [
                purple,
                blue,
                Color(0xFF3F8CFF),
              ];

    return Container(
      width: double.infinity,
      height: 58,

      decoration: BoxDecoration(
        gradient:
            LinearGradient(
          colors: colors,
        ),
        borderRadius:
            BorderRadius.circular(19),
        boxShadow: [
          BoxShadow(
            color: colors.first
                .withValues(
              alpha: 0.28,
            ),
            blurRadius: 13,
            offset:
                const Offset(0, 6),
          ),
        ],
      ),

      child: ElevatedButton.icon(
        onPressed:
            _backendConnected
                ? _toggleTranslation
                : null,

        style:
            ElevatedButton.styleFrom(
          backgroundColor:
              Colors.transparent,
          disabledBackgroundColor:
              Colors.transparent,
          shadowColor:
              Colors.transparent,
          foregroundColor:
              Colors.white,
          shape:
              RoundedRectangleBorder(
            borderRadius:
                BorderRadius.circular(
              19,
            ),
          ),
        ),

        icon: Icon(
          _isTranslating
              ? Icons.stop_rounded
              : Icons
                  .play_arrow_rounded,
        ),

        label: Text(
          _isTranslating
              ? 'Stop Translation'
              : 'Start AI Translation',
          style: const TextStyle(
            fontSize: 15,
            fontWeight:
                FontWeight.w900,
          ),
        ),
      ),
    );
  }

  // ============================================================
  // HISTORY
  // ============================================================

  Widget _buildHistory() {
    return Container(
      width: double.infinity,

      padding:
          const EdgeInsets.all(17),

      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius:
            BorderRadius.circular(22),
        border: Border.all(
          color:
              const Color(0xFFE6E9F0),
        ),
      ),

      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.history_rounded,
                color: purple,
                size: 19,
              ),

              const SizedBox(width: 7),

              const Text(
                'Recent signs',
                style: TextStyle(
                  color: darkText,
                  fontSize: 13,
                  fontWeight:
                      FontWeight.w900,
                ),
              ),

              const Spacer(),

              if (_history.isNotEmpty)
                TextButton(
                  onPressed:
                      _clearHistory,
                  child:
                      const Text(
                    'Clear',
                  ),
                ),
            ],
          ),

          const SizedBox(height: 8),

          if (_history.isEmpty)
            const Text(
              'Detected signs will appear here.',
              style: TextStyle(
                color:
                    Color(0xFF8B94A4),
                fontSize: 11,
              ),
            )
          else
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children:
                  _history.map(
                (word) {
                  return Container(
                    padding:
                        const EdgeInsets
                            .symmetric(
                      horizontal: 11,
                      vertical: 7,
                    ),

                    decoration:
                        BoxDecoration(
                      color:
                          const Color(
                        0xFFF5F0FF,
                      ),
                      borderRadius:
                          BorderRadius
                              .circular(
                        12,
                      ),
                      border:
                          Border.all(
                        color:
                            const Color(
                          0xFFE3D5FB,
                        ),
                      ),
                    ),

                    child: Text(
                      word
                          .toUpperCase(),
                      style:
                          const TextStyle(
                        color: purple,
                        fontSize: 10,
                        fontWeight:
                            FontWeight.w900,
                      ),
                    ),
                  );
                },
              ).toList(),
            ),
        ],
      ),
    );
  }
}