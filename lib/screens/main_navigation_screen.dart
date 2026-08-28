import 'dart:async';

import 'package:flutter/material.dart';

import '../services/app_command_service.dart';

import 'dictionary_page.dart';
import 'education_page.dart';
import 'games_page.dart';
import 'sos_page.dart';
import 'translate_page.dart';
import 'voice_assist_page.dart';
import 'chatbot_page.dart';


class MainNavigationScreen
    extends StatefulWidget {
  const MainNavigationScreen({
    super.key,
  });

  @override
  State<MainNavigationScreen>
      createState() =>
          _MainNavigationScreenState();
}


class _MainNavigationScreenState
    extends State<MainNavigationScreen>
    with SingleTickerProviderStateMixin {

  int _selectedIndex = 0;

  double? _sosX;
  double? _sosY;


  late final AnimationController
      _glowController;

  late final Animation<double>
      _glowAnimation;


  late final StreamSubscription<
      SignBridgeAppCommand>
      _commandSubscription;


  final List<Widget> _pages =
      const [
    TranslatePage(),
    VoiceAssistPage(),
    DictionaryPage(),
    EducationPage(),
    GamesPage(),
  ];


  // ==========================================================
  // INIT
  // ==========================================================

  @override
  void initState() {
    super.initState();


    // --------------------------------------------------------
    // EXISTING SOS ANIMATION
    // --------------------------------------------------------

    _glowController =
        AnimationController(
      vsync: this,

      duration:
          const Duration(
        milliseconds: 1300,
      ),
    )..repeat(
        reverse: true,
      );


    _glowAnimation =
        Tween<double>(
      begin: 0.25,
      end: 0.65,
    ).animate(
      CurvedAnimation(
        parent:
            _glowController,

        curve:
            Curves.easeInOut,
      ),
    );


    // --------------------------------------------------------
    // SIGNBRIDGE AI COMMAND LISTENER
    // --------------------------------------------------------

    _commandSubscription =
        AppCommandService
            .instance
            .commands
            .listen(
      _handleAppCommand,
    );
  }


  // ==========================================================
  // DISPOSE
  // ==========================================================

  @override
  void dispose() {
    _commandSubscription.cancel();

    _glowController.dispose();

    super.dispose();
  }


  // ==========================================================
  // CHANGE MAIN PAGE
  // ==========================================================

  void _changePage(
    int index,
  ) {
    if (!mounted) {
      return;
    }

    if (_selectedIndex ==
        index) {
      return;
    }

    setState(() {
      _selectedIndex =
          index;
    });
  }


  // ==========================================================
  // SIGNBRIDGE AI APP CONTROL
  // ==========================================================
  //
  // MainNavigationScreen is responsible ONLY for selecting
  // the correct major page.
  //
  // Deep commands are handled INSIDE the page itself.
  //
  // Example:
  //
  // education + open_lesson
  //
  // MainNavigation:
  //   -> selects Education
  //
  // EducationPage:
  //   -> opens requested lesson
  //
  // This avoids changing page constructors.
  //
  // ==========================================================

  void _handleAppCommand(
    SignBridgeAppCommand command,
  ) {
    if (!mounted) {
      return;
    }

    switch (command.page) {

      // ------------------------------------------------------
      // TRANSLATE
      // ------------------------------------------------------

      case 'translate':
      case 'translation':
      case 'sign_translation':

        _changePage(
          0,
        );

        break;


      // ------------------------------------------------------
      // VOICE ASSIST
      // ------------------------------------------------------

      case 'voice_assist':
      case 'voiceassist':
      case 'sound':
      case 'sounds':

        _changePage(
          1,
        );

        break;


      // ------------------------------------------------------
      // DICTIONARY
      // ------------------------------------------------------

      case 'dictionary':

        _changePage(
          2,
        );

        break;


      // ------------------------------------------------------
      // EDUCATION
      // ------------------------------------------------------

      case 'education':
      case 'learning':

        _changePage(
          3,
        );

        break;


      // ------------------------------------------------------
      // GAMES
      // ------------------------------------------------------

      case 'games':
      case 'game':

        _changePage(
          4,
        );

        break;


      // ------------------------------------------------------
      // SOS
      // ------------------------------------------------------

      case 'sos':
      case 'emergency':

        // Important:
        //
        // AI can OPEN the SOS screen.
        //
        // It must NOT silently send an emergency action.
        //
        // Actual emergency sending remains inside SosPage
        // and requires user confirmation.

        _openSosPage();

        break;


      default:

        // Unknown commands are intentionally ignored.
        //
        // They must never break the current application.
        break;
    }
  }


  // ==========================================================
  // OPEN CHATBOT
  // ==========================================================

  void _openChatbotPage() {
    if (!mounted) {
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => const ChatbotPage(),
      ),
    );
  }


  // ==========================================================
  // OPEN SOS
  // ==========================================================

  void _openSosPage() {
    if (!mounted) {
      return;
    }

    Navigator.push(
      context,

      MaterialPageRoute(
        builder: (_) =>
            const SosPage(),
      ),
    );
  }


  // ==========================================================
  // BUILD
  // ==========================================================

  @override
  Widget build(
    BuildContext context,
  ) {
    return Scaffold(
      backgroundColor:
          const Color(
        0xFFF8F9FD,
      ),


      // ======================================================
      // BODY
      // ======================================================

      body:
          LayoutBuilder(
        builder: (
          BuildContext context,
          BoxConstraints constraints,
        ) {

          const double sosSize =
              70;


          final double defaultX =
              constraints.maxWidth -
                  sosSize -
                  12;


          final double defaultY =
              (
                constraints.maxHeight /
                    2
              ) -
                  (
                    sosSize /
                        2
                  );


          final double sosX =
              _sosX ??
                  defaultX;


          final double sosY =
              _sosY ??
                  defaultY;


          return Stack(
            children: [

              // =================================================
              // EXISTING MAIN PAGES
              // =================================================

              IndexedStack(
                index:
                    _selectedIndex,

                children:
                    _pages,
              ),


              // =================================================
              // SIGNBRIDGE AI CHATBOT BUTTON
              // =================================================

              Positioned(
                right: 18,
                top: sosY - 85,
                child: GestureDetector(
                  onTap: _openChatbotPage,
                  child: Container(
                    width: 62,
                    height: 62,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(
                        colors: [
                          Color(0xFF173B8F),
                          Color(0xFF4D8DFF),
                        ],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF173B8F).withValues(alpha: 0.35),
                          blurRadius: 18,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.smart_toy_rounded,
                      color: Colors.white,
                      size: 30,
                    ),
                  ),
                ),
              ),


              // =================================================
              // EXISTING MOVABLE SOS
              // =================================================

              Positioned(
                left:
                    sosX,

                top:
                    sosY,

                child:
                    GestureDetector(

                  onPanUpdate: (
                    DragUpdateDetails
                        details,
                  ) {

                    setState(() {

                      final double newX =
                          (
                            _sosX ??
                                defaultX
                          ) +
                              details
                                  .delta
                                  .dx;


                      final double newY =
                          (
                            _sosY ??
                                defaultY
                          ) +
                              details
                                  .delta
                                  .dy;


                      _sosX =
                          newX
                              .clamp(
                                8.0,

                                constraints
                                        .maxWidth -
                                    sosSize -
                                    8,
                              )
                              .toDouble();


                      _sosY =
                          newY
                              .clamp(
                                8.0,

                                constraints
                                        .maxHeight -
                                    sosSize -
                                    8,
                              )
                              .toDouble();
                    });
                  },


                  child:
                      AnimatedBuilder(

                    animation:
                        _glowAnimation,


                    builder: (
                      BuildContext context,
                      Widget? child,
                    ) {

                      return Container(
                        width:
                            sosSize,

                        height:
                            sosSize,


                        decoration:
                            BoxDecoration(

                          shape:
                              BoxShape
                                  .circle,


                          boxShadow: [

                            BoxShadow(
                              color:
                                  const Color(
                                0xFFE53935,
                              ).withValues(
                                alpha:
                                    _glowAnimation
                                        .value,
                              ),

                              blurRadius:
                                  20 +
                                      (
                                        _glowAnimation
                                                .value *
                                            12
                                      ),

                              spreadRadius:
                                  2 +
                                      (
                                        _glowAnimation
                                                .value *
                                            4
                                      ),
                            ),


                            BoxShadow(
                              color:
                                  const Color(
                                0xFFFF8C42,
                              ).withValues(
                                alpha:
                                    0.20,
                              ),

                              blurRadius:
                                  30,

                              spreadRadius:
                                  2,
                            ),
                          ],
                        ),


                        child:
                            child,
                      );
                    },


                    child:
                        Material(
                      color:
                          Colors.transparent,


                      child:
                          InkWell(

                        onTap:
                            _openSosPage,


                        customBorder:
                            const CircleBorder(),


                        child:
                            Ink(

                          decoration:
                              const BoxDecoration(

                            shape:
                                BoxShape
                                    .circle,


                            gradient:
                                LinearGradient(

                              begin:
                                  Alignment
                                      .topLeft,

                              end:
                                  Alignment
                                      .bottomRight,


                              colors: [
                                Color(
                                  0xFFE53935,
                                ),

                                Color(
                                  0xFFFF5A4F,
                                ),

                                Color(
                                  0xFFFF8C42,
                                ),
                              ],
                            ),
                          ),


                          child:
                              const Column(

                            mainAxisAlignment:
                                MainAxisAlignment
                                    .center,


                            children: [

                              Icon(
                                Icons
                                    .sos_rounded,

                                size:
                                    25,

                                color:
                                    Colors
                                        .white,
                              ),


                              SizedBox(
                                height:
                                    1,
                              ),


                              Text(
                                'SOS',

                                style:
                                    TextStyle(

                                  fontSize:
                                      11,

                                  fontWeight:
                                      FontWeight
                                          .bold,

                                  color:
                                      Colors
                                          .white,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),


      // ======================================================
      // EXISTING BOTTOM NAVIGATION
      // ======================================================

      bottomNavigationBar:
          BottomAppBar(

        height:
            80,

        padding:
            EdgeInsets.zero,

        color:
            Colors.white,

        elevation:
            12,

        shadowColor:
            Colors.black
                .withValues(
          alpha:
              0.15,
        ),


        child:
            Row(
          children: [

            // ------------------------------------------------
            // TRANSLATE
            // ------------------------------------------------

            Expanded(
              child:
                  _NavigationItem(

                icon:
                    Icons
                        .sign_language_rounded,

                label:
                    'Translate',

                selected:
                    _selectedIndex ==
                        0,

                onTap:
                    () =>
                        _changePage(
                  0,
                ),
              ),
            ),


            // ------------------------------------------------
            // VOICE ASSIST
            // ------------------------------------------------

            Expanded(
              child:
                  _NavigationItem(

                icon:
                    Icons
                        .graphic_eq_rounded,

                label:
                    'Voice Assist',

                selected:
                    _selectedIndex ==
                        1,

                onTap:
                    () =>
                        _changePage(
                  1,
                ),
              ),
            ),


            // ------------------------------------------------
            // DICTIONARY
            // ------------------------------------------------

            Expanded(
              child:
                  _NavigationItem(

                icon:
                    Icons
                        .menu_book_rounded,

                label:
                    'Dictionary',

                selected:
                    _selectedIndex ==
                        2,

                onTap:
                    () =>
                        _changePage(
                  2,
                ),
              ),
            ),


            // ------------------------------------------------
            // EDUCATION
            // ------------------------------------------------

            Expanded(
              child:
                  _NavigationItem(

                icon:
                    Icons
                        .school_rounded,

                label:
                    'Education',

                selected:
                    _selectedIndex ==
                        3,

                onTap:
                    () =>
                        _changePage(
                  3,
                ),
              ),
            ),


            // ------------------------------------------------
            // GAMES
            // ------------------------------------------------

            Expanded(
              child:
                  _NavigationItem(

                icon:
                    Icons
                        .sports_esports_rounded,

                label:
                    'Games',

                selected:
                    _selectedIndex ==
                        4,

                onTap:
                    () =>
                        _changePage(
                  4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


// ============================================================
// NAVIGATION ITEM
// ============================================================

class _NavigationItem
    extends StatelessWidget {

  final IconData icon;

  final String label;

  final bool selected;

  final VoidCallback onTap;


  const _NavigationItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });


  @override
  Widget build(
    BuildContext context,
  ) {

    final Color color =
        selected

            ? const Color(
                0xFF173B8F,
              )

            : const Color(
                0xFFA0A8B5,
              );


    return Material(
      color:
          Colors.transparent,


      child:
          InkWell(

        onTap:
            onTap,


        child:
            Column(

          mainAxisAlignment:
              MainAxisAlignment
                  .center,


          children: [

            AnimatedContainer(
              duration:
                  const Duration(
                milliseconds:
                    180,
              ),


              padding:
                  const EdgeInsets
                      .all(
                7,
              ),


              decoration:
                  BoxDecoration(

                color:
                    selected

                        ? const Color(
                            0xFFEEF2FF,
                          )

                        : Colors
                            .transparent,


                borderRadius:
                    BorderRadius
                        .circular(
                  12,
                ),
              ),


              child:
                  Icon(
                icon,

                color:
                    color,

                size:
                    24,
              ),
            ),


            const SizedBox(
              height:
                  2,
            ),


            Text(
              label,

              maxLines:
                  1,

              overflow:
                  TextOverflow
                      .ellipsis,


              style:
                  TextStyle(

                color:
                    color,

                fontSize:
                    9,

                fontWeight:
                    selected

                        ? FontWeight
                            .w800

                        : FontWeight
                            .normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}