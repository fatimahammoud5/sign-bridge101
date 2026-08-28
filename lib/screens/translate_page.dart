import 'dart:convert';

import 'sign_camera_translation_page.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class TranslatePage extends StatefulWidget {
  const TranslatePage({super.key});

  @override
  State<TranslatePage> createState() => _TranslatePageState();
}

class _TranslatePageState extends State<TranslatePage> {
  final TextEditingController _textController =
  TextEditingController();

  bool _isLoading = false;
  List<String> _returnedSigns = [];

  static const Color purple = Color(0xFF7B2FF7);
  static const Color orange = Color(0xFFFF8C42);
  static const Color darkText = Color(0xFF20243A);

  static const String _apiUrl =
      'http://192.168.0.118:5000/api/text-to-sign';

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _translateText() async {
    final String text = _textController.text.trim();

    if (text.isEmpty) {
      _showMessage(
        'Please type a sentence first.',
      );
      return;
    }

    FocusScope.of(context).unfocus();

    setState(() {
      _isLoading = true;
      _returnedSigns = [];
    });

    try {
      final http.Response response = await http
          .post(
        Uri.parse(_apiUrl),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'text': text,
        }),
      )
          .timeout(
        const Duration(seconds: 120),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Server returned status ${response.statusCode}.',
        );
      }

      final dynamic decoded =
      jsonDecode(response.body);

      if (decoded is! Map<String, dynamic>) {
        throw const FormatException(
          'Invalid response from server.',
        );
      }

      if (decoded['success'] != true) {
        throw Exception(
          decoded['message'] ??
              'Translation failed.',
        );
      }

      final List<String> signs =
      List<String>.from(
        decoded['sign_sequence'] ?? [],
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _returnedSigns = signs;
      });

      if (signs.isEmpty) {
        _showMessage(
          'No supported signs were returned.',
        );
      } else {
        _showMessage(
          'Signs: ${signs.join(' → ')}',
        );
      }
    } catch (error) {
      if (!mounted) {
        return;
      }

      _showMessage(
        'Connection failed: $error',
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

    void _openCamera() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => const SignCameraTranslationPage(),
      ),
    );
  }

  void _startVoiceInput() {
    _showMessage(
      'Voice recording will be added next.',
    );
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          behavior: SnackBarBehavior.floating,
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor:
      const Color(0xFFF8F9FD),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            16,
            12,
            16,
            10,
          ),
          child: Column(
            children: [
              const _TranslateHeader(),
              const SizedBox(height: 12),

              Expanded(
                child: _AvatarArea(
                  signs: _returnedSigns,
                  isLoading: _isLoading,
                ),
              ),

              const SizedBox(height: 12),

              _TranslateInputBar(
                controller: _textController,
                isLoading: _isLoading,
                onSend: _translateText,
                onCameraPressed: _openCamera,
                onMicrophonePressed:
                _startVoiceInput,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TranslateHeader extends StatelessWidget {
  const _TranslateHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [
                _TranslatePageState.purple,
                _TranslatePageState.orange,
              ],
            ),
            borderRadius:
            BorderRadius.circular(15),
          ),
          child: const Icon(
            Icons.sign_language_rounded,
            color: Colors.white,
            size: 25,
          ),
        ),
        const SizedBox(width: 11),
        const Expanded(
          child: Column(
            crossAxisAlignment:
            CrossAxisAlignment.start,
            children: [
              Text(
                'SignBridge',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                  color:
                  _TranslatePageState.darkText,
                ),
              ),
              SizedBox(height: 2),
              Text(
                'AI sign language translator',
                style: TextStyle(
                  fontSize: 11,
                  color: Color(0xFF7B8494),
                ),
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(
            horizontal: 11,
            vertical: 8,
          ),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius:
            BorderRadius.circular(14),
            border: Border.all(
              color: const Color(0xFFE3E7EE),
            ),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.language_rounded,
                size: 18,
                color:
                _TranslatePageState.purple,
              ),
              SizedBox(width: 5),
              Text(
                'EN',
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color:
                  _TranslatePageState.darkText,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _AvatarArea extends StatelessWidget {
  final List<String> signs;
  final bool isLoading;

  const _AvatarArea({
    required this.signs,
    required this.isLoading,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFFF5F0FF),
            Color(0xFFFFF4EC),
            Color(0xFFF8FAFF),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius:
        BorderRadius.circular(27),
        border: Border.all(
          color: const Color(0xFFE9E5F4),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(
              alpha: 0.06,
            ),
            blurRadius: 16,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            top: 14,
            right: 14,
            child: Container(
              padding:
              const EdgeInsets.symmetric(
                horizontal: 10,
                vertical: 7,
              ),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius:
                BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisSize:
                MainAxisSize.min,
                children: [
                  CircleAvatar(
                    radius: 4,
                    backgroundColor:
                    isLoading
                        ? Colors.orange
                        : Colors.green,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    isLoading
                        ? 'Translating'
                        : 'Avatar ready',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight:
                      FontWeight.w700,
                      color:
                      Color(0xFF536075),
                    ),
                  ),
                ],
              ),
            ),
          ),
          Center(
            child: Padding(
              padding:
              const EdgeInsets.symmetric(
                horizontal: 24,
              ),
              child: Column(
                mainAxisSize:
                MainAxisSize.min,
                children: [
                  if (isLoading)
                    const SizedBox(
                      width: 52,
                      height: 52,
                      child:
                      CircularProgressIndicator(
                        strokeWidth: 5,
                        color:
                        _TranslatePageState
                            .purple,
                      ),
                    )
                  else
                    const Icon(
                      Icons
                          .accessibility_new_rounded,
                      size: 125,
                      color:
                      _TranslatePageState
                          .purple,
                    ),
                  const SizedBox(height: 14),
                  Text(
                    isLoading
                        ? 'AI is translating...'
                        : 'Unity Avatar Area',
                    textAlign:
                    TextAlign.center,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight:
                      FontWeight.w800,
                      color:
                      _TranslatePageState
                          .darkText,
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (signs.isEmpty)
                    Text(
                      isLoading
                          ? 'Please wait while the sentence is processed.'
                          : 'Your animated sign-language avatar will appear here.',
                      textAlign:
                      TextAlign.center,
                      style: const TextStyle(
                        fontSize: 12,
                        height: 1.4,
                        color:
                        Color(0xFF7D8798),
                      ),
                    )
                  else
                    Wrap(
                      alignment:
                      WrapAlignment.center,
                      spacing: 7,
                      runSpacing: 7,
                      children: signs.map(
                            (String sign) {
                          return Container(
                            padding:
                            const EdgeInsets
                                .symmetric(
                              horizontal: 10,
                              vertical: 7,
                            ),
                            decoration:
                            BoxDecoration(
                              color: Colors.white,
                              borderRadius:
                              BorderRadius
                                  .circular(
                                12,
                              ),
                              border: Border.all(
                                color:
                                const Color(
                                  0xFFE4D8FA,
                                ),
                              ),
                            ),
                            child: Text(
                              sign,
                              style:
                              const TextStyle(
                                fontSize: 11,
                                fontWeight:
                                FontWeight
                                    .w700,
                                color:
                                _TranslatePageState
                                    .purple,
                              ),
                            ),
                          );
                        },
                      ).toList(),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TranslateInputBar
    extends StatelessWidget {
  final TextEditingController controller;
  final bool isLoading;
  final VoidCallback onSend;
  final VoidCallback onCameraPressed;
  final VoidCallback onMicrophonePressed;

  const _TranslateInputBar({
    required this.controller,
    required this.isLoading,
    required this.onSend,
    required this.onCameraPressed,
    required this.onMicrophonePressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 8,
        vertical: 8,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius:
        BorderRadius.circular(26),
        border: Border.all(
          color: const Color(0xFFE3E7EE),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(
              alpha: 0.07,
            ),
            blurRadius: 14,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        children: [
                _SignCameraButton(
        onPressed: isLoading
            ? null
            : onCameraPressed,
      ),

          const SizedBox(width: 7),

          _RoundInputButton(
            icon: Icons.mic_rounded,
            color:
            _TranslatePageState.orange,
            onPressed: isLoading
                ? null
                : onMicrophonePressed,
          ),

          const SizedBox(width: 9),

          Expanded(
            child: TextField(
              controller: controller,
              enabled: !isLoading,
              textInputAction:
              TextInputAction.send,
              onSubmitted: (_) {
                if (!isLoading) {
                  onSend();
                }
              },
              decoration:
              const InputDecoration(
                hintText:
                'Type to translate',
                border: InputBorder.none,
                isDense: true,
                contentPadding:
                EdgeInsets.symmetric(
                  vertical: 13,
                ),
                hintStyle: TextStyle(
                  color:
                  Color(0xFF9AA4B2),
                  fontSize: 13,
                ),
              ),
            ),
          ),

          const SizedBox(width: 7),

          Container(
            width: 45,
            height: 45,
            decoration: BoxDecoration(
              gradient: isLoading
                  ? const LinearGradient(
                colors: [
                  Color(0xFFB7BEC8),
                  Color(0xFF9AA4B2),
                ],
              )
                  : const LinearGradient(
                colors: [
                  _TranslatePageState
                      .purple,
                  Color(0xFF9C62FF),
                ],
              ),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              onPressed:
              isLoading ? null : onSend,
              icon: isLoading
                  ? const SizedBox(
                width: 20,
                height: 20,
                child:
                CircularProgressIndicator(
                  strokeWidth: 2.4,
                  color: Colors.white,
                ),
              )
                  : const Icon(
                Icons
                    .arrow_upward_rounded,
                color: Colors.white,
                size: 22,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RoundInputButton
    extends StatelessWidget {
  final IconData icon;
  final Color color;
  final VoidCallback? onPressed;

  const _RoundInputButton({
    required this.icon,
    required this.color,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 45,
      height: 45,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: color.withValues(
              alpha: 0.25,
            ),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: IconButton(
        onPressed: onPressed,
        icon: Icon(
          icon,
          color: Colors.white,
          size: 22,
        ),
      ),
    );
  }

}
class _SignCameraButton extends StatelessWidget {
  final VoidCallback? onPressed;

  const _SignCameraButton({
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final bool enabled = onPressed != null;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(18),
        child: Ink(
          height: 48,
          padding: const EdgeInsets.symmetric(
            horizontal: 12,
          ),
          decoration: BoxDecoration(
            gradient: enabled
                ? const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFF7B2FF7),
                      Color(0xFF536DFE),
                      Color(0xFF3F8CFF),
                    ],
                  )
                : const LinearGradient(
                    colors: [
                      Color(0xFFB7BEC8),
                      Color(0xFF9AA4B2),
                    ],
                  ),
            borderRadius: BorderRadius.circular(18),
            boxShadow: enabled
                ? [
                    BoxShadow(
                      color: const Color(0xFF7B2FF7)
                          .withValues(alpha: 0.30),
                      blurRadius: 12,
                      offset: const Offset(0, 5),
                    ),
                  ]
                : [],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Stack(
                clipBehavior: Clip.none,
                children: [
                  const Icon(
                    Icons.camera_alt_rounded,
                    color: Colors.white,
                    size: 23,
                  ),

                  Positioned(
                    top: -7,
                    right: -9,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 4,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFC857),
                        borderRadius:
                            BorderRadius.circular(6),
                        border: Border.all(
                          color: Colors.white,
                          width: 1.2,
                        ),
                      ),
                      child: const Text(
                        'AI',
                        style: TextStyle(
                          fontSize: 7,
                          fontWeight: FontWeight.w900,
                          color: Color(0xFF322452),
                        ),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(width: 8),

              const Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sign',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      height: 1,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Camera',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      height: 1,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}