import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:video_player/video_player.dart';


// ============================================================
// IMPORTANT
// ============================================================
// غيّري هذا الـIP إذا تغيّر IP الكمبيوتر.
// إذا كنتِ تعملين على هاتف حقيقي:
// استخدمي IP الكمبيوتر مثل 192.168.1.8
//
// إذا كنتِ تعملين على Android Emulator:
// استخدمي 10.0.2.2 بدل IP الشبكة.
const String dictionaryBaseUrl = 'http://192.168.0.118:5000';


// ============================================================
// DICTIONARY COLOR PALETTE
// ============================================================

const List<Color> dictionaryLetterColors = [
  Color(0xFF42A5F5),
  Color(0xFF1E88E5),
  Color(0xFF1565C0),
  Color(0xFF0D47A1),
  Color(0xFF29B6F6),
  Color(0xFF00ACC1),
  Color(0xFF26C6DA),
  Color(0xFF5C6BC0),
  Color(0xFF7E57C2),
  Color(0xFF3949AB),
  Color(0xFF00897B),
  Color(0xFF039BE5),
];

Color dictionaryColorForLetter(String letter) {
  if (letter.isEmpty) {
    return dictionaryLetterColors.first;
  }

  final int code = letter.toUpperCase().codeUnitAt(0);

  return dictionaryLetterColors[
      code % dictionaryLetterColors.length
  ];
}


// ============================================================
// WORD EMOJIS
// ============================================================

const Map<String, String> dictionaryWordEmojis = {
  'ACCIDENT': '🚨',
  'ACCEPT': '✅',
  'ACTION': '🎬',
  'ADDRESS': '📍',
  'AFTER': '⏭️',
  'AGAIN': '🔁',
  'AIRPLANE': '✈️',
  'ANIMAL': '🐾',
  'APPLE': '🍎',
  'ARRIVE': '🏁',
  'ASK': '❓',
  'BABY': '👶',
  'BACK': '🔙',
  'BACKPACK': '🎒',
  'BACON': '🥓',
  'BAD': '👎',
  'BAG': '👜',
  'BALL': '⚽',
  'BED': '🛏️',
  'BLACK': '⚫',
  'BLUE': '🔵',
  'BOOK': '📖',
  'BREAD': '🍞',
  'BROTHER': '👦',
  'BUY': '🛒',
  'CAKE': '🍰',
  'CALENDAR': '📅',
  'CALL': '📞',
  'CALM': '😌',
  'CAMERA': '📷',
  'CAN': '💪',
  'CAR': '🚗',
  'CAT': '🐱',
  'CHAIR': '🪑',
  'CHEESE': '🧀',
  'CHILD': '🧒',
  'CITY': '🏙️',
  'CLOTHES': '👕',
  'COFFEE': '☕',
  'COLOR': '🎨',
  'COMPUTER': '💻',
  'COOK': '👩‍🍳',
  'COUSIN': '👨‍👩‍👧‍👦',
  'DANCE': '💃',
  'DANGER': '⚠️',
  'DATE': '📅',
  'DAUGHTER': '👧',
  'DAY': '☀️',
  'DEAF': '🧏',
  'DECIDE': '🤔',
  'DOCTOR': '🩺',
  'DOG': '🐶',
  'DOOR': '🚪',
  'DRAW': '✏️',
  'DRINK': '🥤',
  'DRIVE': '🚘',
  'EAR': '👂',
  'EARLY': '🌅',
  'EARTH': '🌍',
  'EASY': '👌',
  'EAT': '🍽️',
  'EGG': '🥚',
  'EMERGENCY': '🆘',
  'ENJOY': '😊',
  'EVENING': '🌆',
  'EXCITED': '🤩',
  'FACE': '🙂',
  'FAMILY': '👨‍👩‍👧‍👦',
  'FAMOUS': '⭐',
  'FARM': '🚜',
  'FAST': '⚡',
  'FATHER': '👨',
  'FEEL': '💭',
  'FINE': '👍',
  'FIRE': '🔥',
  'FISH': '🐟',
  'FOOD': '🍲',
  'FORGET': '🫥',
  'FRIEND': '🫂',
  'GAME': '🎮',
  'GARAGE': '🏠',
  'GAS': '⛽',
  'GET': '📥',
  'GIFT': '🎁',
  'GIRL': '👧',
  'GIVE': '🤲',
  'GO': '➡️',
  'GOOD': '👍',
  'GREEN': '🟢',
  'HAIR': '💇',
  'HALF': '½️',
  'HAMBURGER': '🍔',
  'HAPPY': '😄',
  'HAT': '🎩',
  'HEARING': '👂',
  'HELP': '🆘',
  'HOME': '🏠',
  'HOSPITAL': '🏥',
  'HOT': '♨️',
  'HOUSE': '🏡',
  'HOW': '❓',
  'HUNGRY': '😋',
  'ICE': '🧊',
  'ICECREAM': '🍦',
  'IDEA': '💡',
  'IF': '🔀',
  'ILOVEYOU': '🤟',
  'IMPORTANT': '❗',
  'IMPOSSIBLE': '🚫',
  'IMPROVE': '📈',
  'IN': '📥',
  'INDEPENDENT': '🕊️',
  'INTERNET': '🌐',
  'JACKET': '🧥',
  'JEALOUS': '😒',
  'JEWELRY': '💎',
  'JOIN': '🤝',
  'JOKE': '😂',
  'JUICE': '🧃',
  'KEEP': '📦',
  'KEY': '🔑',
  'KEYBOARD': '⌨️',
  'KICK': '🦵',
  'KID': '🧒',
  'KING': '👑',
  'KISS': '💋',
  'KITCHEN': '🍳',
  'LANGUAGE': '💬',
  'LAPTOP': '💻',
  'LAST': '⏮️',
  'LATE': '⏰',
  'LATER': '🕒',
  'LAUGH': '😂',
  'LAW': '⚖️',
  'LAWYER': '⚖️',
  'LEARN': '📚',
  'LETTER': '🔤',
  'LIKE': '👍',
  'LOVE': '❤️',
  'MACHINE': '⚙️',
  'MAGAZINE': '📰',
  'MAKE': '🛠️',
  'MAN': '👨',
  'MEDICINE': '💊',
  'MEET': '🤝',
  'MONEY': '💵',
  'MONTH': '🗓️',
  'MORNING': '🌅',
  'MOTHER': '👩',
  'MOVIE': '🎬',
  'NAME': '🏷️',
  'NEAR': '📍',
  'NEED': '🙏',
  'NETWORK': '🌐',
  'NEW': '🆕',
  'NEXT': '⏭️',
  'NIGHT': '🌙',
  'NO': '❌',
  'NOW': '⏱️',
  'NUMBER': '🔢',
  'OCEAN': '🌊',
  'OFF': '⏹️',
  'OFFICE': '🏢',
  'OFTEN': '🔁',
  'OK': '👌',
  'OLD': '👴',
  'ON': '🔛',
  'ONE': '1️⃣',
  'ORANGE': '🍊',
  'PAGE': '📄',
  'PAIN': '🤕',
  'PAINT': '🎨',
  'PANTS': '👖',
  'PAPER': '📄',
  'PARENTS': '👨‍👩‍👧',
  'PHONE': '📱',
  'PIZZA': '🍕',
  'PLAY': '▶️',
  'PLEASE': '🙏',
  'POLICE': '👮',
  'PROBLEM': '⚠️',
  'QUALITY': '💎',
  'QUARTER': '🪙',
  'QUEEN': '👸',
  'QUIET': '🤫',
  'QUIT': '🚪',
  'RABBIT': '🐰',
  'RADIO': '📻',
  'RAIN': '🌧️',
  'RAINBOW': '🌈',
  'READ': '📖',
  'READY': '✅',
  'REALLY': '💯',
  'RED': '🔴',
  'REMEMBER': '🧠',
  'RIGHT': '➡️',
  'ROOM': '🚪',
  'RUN': '🏃',
  'SAD': '😢',
  'SAFE': '🛡️',
  'SALAD': '🥗',
  'SALT': '🧂',
  'SANDWICH': '🥪',
  'SATURDAY': '📅',
  'SCHOOL': '🏫',
  'SEE': '👀',
  'SHIRT': '👕',
  'SHOES': '👟',
  'SICK': '🤒',
  'SISTER': '👧',
  'SLEEP': '😴',
  'SLOW': '🐢',
  'SMALL': '🤏',
  'SORRY': '🙏',
  'STUDY': '📚',
  'SUN': '☀️',
  'TABLE': '🪑',
  'TABLET': '📱',
  'TAKE': '🤲',
  'TALK': '🗣️',
  'TALL': '📏',
  'TEA': '🍵',
  'TEACH': '🧑‍🏫',
  'TEACHER': '👩‍🏫',
  'THANKYOU': '🙏',
  'THINK': '🤔',
  'TIME': '⏰',
  'TODAY': '📅',
  'TOMORROW': '➡️',
  'TRAIN': '🚆',
  'UGLY': '😖',
  'UMBRELLA': '☂️',
  'UNCLE': '👨',
  'UNDER': '⬇️',
  'UNDERSTAND': '💡',
  'UNIVERSITY': '🎓',
  'UP': '⬆️',
  'UPLOAD': '⬆️',
  'UPSET': '😞',
  'VACATION': '🏖️',
  'VACUUM': '🧹',
  'VALIDATE': '✅',
  'VALUE': '💎',
  'VANILLA': '🍦',
  'VEGETABLE': '🥦',
  'VERY': '‼️',
  'VEST': '🦺',
  'VIDEOGAME': '🎮',
  'WAIT': '⏳',
  'WALK': '🚶',
  'WALL': '🧱',
  'WALLET': '👛',
  'WANT': '🙋',
  'WARM': '🌤️',
  'WASH': '🧼',
  'WATCH': '⌚',
  'WATER': '💧',
  'WEEK': '📅',
  'WHAT': '❓',
  'WHERE': '📍',
  'WHO': '👤',
  'WHY': '❓',
  'WORK': '💼',
  'WRITE': '✍️',
  'YAY': '🎉',
  'YEAH': '👍',
  'YEAR': '🗓️',
  'YELLOW': '🟡',
  'YES': '✅',
  'YESTERDAY': '⬅️',
  'YOU': '👉',
  'YOUNG': '🧒',
  'YOUR': '👉',
  'YOURSELF': '🪞',
  'ZEBRA': '🦓',
  'ZERO': '0️⃣',
  'ZIPPER': '🤐',
  'ZOO': '🦁',
  'ZOOMIN': '🔎',
  'ZOOMOFF': '🔍',
};

String dictionaryEmojiForWord(String word) {
  final String key = word
      .trim()
      .toUpperCase()
      .replaceAll(RegExp(r'[^A-Z0-9]'), '');

  if (key.length == 1 &&
      key.codeUnitAt(0) >= 65 &&
      key.codeUnitAt(0) <= 90) {
    return '🔤';
  }

  return dictionaryWordEmojis[key] ?? '🤟';
}

// ============================================================
// PAGE
// ============================================================

class DictionaryPage extends StatefulWidget {
  const DictionaryPage({super.key});

  @override
  State<DictionaryPage> createState() =>
      _DictionaryPageState();
}

class _DictionaryPageState extends State<DictionaryPage> {
  final TextEditingController _searchController =
      TextEditingController();

  Timer? _searchTimer;

  bool _loading = true;
  String? _error;

  String _selectedLetter = 'ALL';

  List<DictionaryLetter> _letters = [];
  List<DictionarySign> _allSigns = [];
  List<DictionarySign> _visibleSigns = [];

  static const List<String> alphabet = [
    'A',
    'B',
    'C',
    'D',
    'E',
    'F',
    'G',
    'H',
    'I',
    'J',
    'K',
    'L',
    'M',
    'N',
    'O',
    'P',
    'Q',
    'R',
    'S',
    'T',
    'U',
    'V',
    'W',
    'X',
    'Y',
    'Z',
  ];

  @override
  void initState() {
    super.initState();
    _loadDictionary();
  }

  @override
  void dispose() {
    _searchTimer?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadDictionary() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final Uri lettersUri = Uri.parse(
        '$dictionaryBaseUrl/api/dictionary/letters',
      );

      final Uri signsUri = Uri.parse(
        '$dictionaryBaseUrl/api/dictionary/signs?limit=1000',
      );

      final List<http.Response> responses =
          await Future.wait([
        http
            .get(lettersUri)
            .timeout(const Duration(seconds: 12)),
        http
            .get(signsUri)
            .timeout(const Duration(seconds: 12)),
      ]);

      final http.Response lettersResponse =
          responses[0];

      final http.Response signsResponse =
          responses[1];

      if (lettersResponse.statusCode != 200) {
        throw Exception(
          'Could not load dictionary letters.',
        );
      }

      if (signsResponse.statusCode != 200) {
        throw Exception(
          'Could not load dictionary words.',
        );
      }

      final Map<String, dynamic> lettersJson =
          Map<String, dynamic>.from(
        jsonDecode(lettersResponse.body),
      );

      final Map<String, dynamic> signsJson =
          Map<String, dynamic>.from(
        jsonDecode(signsResponse.body),
      );

      final List<dynamic> rawLetters =
          lettersJson['letters'] ?? [];

      final List<dynamic> rawSigns =
          signsJson['items'] ?? [];

      final List<DictionaryLetter> loadedLetters =
          rawLetters.map((dynamic item) {
        return DictionaryLetter.fromJson(
          Map<String, dynamic>.from(item),
        );
      }).toList();

      final List<DictionarySign> loadedSigns =
          rawSigns.map((dynamic item) {
        return DictionarySign.fromJson(
          Map<String, dynamic>.from(item),
        );
      }).toList();

      loadedSigns.sort(
        (DictionarySign a, DictionarySign b) {
          return a.word.compareTo(b.word);
        },
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _letters = loadedLetters;
        _allSigns = loadedSigns;
        _visibleSigns = loadedSigns;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
        _error =
            'Could not connect to the dictionary.\n$error';
      });
    }
  }

  void _filterSigns() {
    final String search =
        _searchController.text.trim().toUpperCase();

    List<DictionarySign> result =
        List<DictionarySign>.from(_allSigns);

    if (_selectedLetter != 'ALL') {
      result = result.where(
        (DictionarySign sign) {
          return sign.letter == _selectedLetter;
        },
      ).toList();
    }

    if (search.isNotEmpty) {
      result = result.where(
        (DictionarySign sign) {
          return sign.word
              .toUpperCase()
              .contains(search);
        },
      ).toList();
    }

    result.sort(
      (DictionarySign a, DictionarySign b) {
        return a.word.compareTo(b.word);
      },
    );

    if (!mounted) {
      return;
    }

    setState(() {
      _visibleSigns = result;
    });
  }

  void _searchChanged(String value) {
    setState(() {});

    _searchTimer?.cancel();

    _searchTimer = Timer(
      const Duration(milliseconds: 250),
      _filterSigns,
    );
  }

  void _chooseLetter(String letter) {
    setState(() {
      _selectedLetter = letter;
    });

    _filterSigns();
  }

  void _clearSearch() {
    _searchController.clear();
    setState(() {});
    _filterSigns();
  }

  bool _letterExists(String letter) {
    // Every A-Z letter has its own ASL alphabet image.
    // Therefore all letter chips stay enabled, including X
    // even when ASL Citizen has no X words.
    return alphabet.contains(letter.toUpperCase());
  }

  int _letterCount(String letter) {
    int wordCount = 0;

    for (final DictionaryLetter item in _letters) {
      if (item.letter == letter) {
        wordCount = item.count;
        break;
      }
    }

    // +1 for the alphabet image shown as the first item.
    return wordCount + 1;
  }

  Map<String, List<DictionarySign>>
      _groupSignsByLetter() {
    final Map<String, List<DictionarySign>> result = {};

    final bool isSearching =
        _searchController.text.trim().isNotEmpty;

    // When we are not searching, always create the section(s)
    // first so every alphabet image A-Z can appear even if
    // there are no ASL Citizen words for that letter (e.g. X).
    if (!isSearching) {
      if (_selectedLetter == 'ALL') {
        for (final String letter in alphabet) {
          result[letter] = [];
        }
      } else {
        result[_selectedLetter] = [];
      }
    }

    for (final DictionarySign sign in _visibleSigns) {
      result.putIfAbsent(
        sign.letter,
        () => [],
      );

      result[sign.letter]!.add(sign);
    }

    return result;
  }

  Future<void> _openWord(
    DictionarySign sign,
  ) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) {
          return DictionaryDetailsPage(
            signId: sign.id,
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor:
          const Color(0xFFF3F8FF),
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(
              child: _buildContent(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF071A52),
            Color(0xFF0D47A1),
            Color(0xFF1976D2),
            Color(0xFF4FC3F7),
          ],
        ),
        borderRadius: BorderRadius.vertical(
          bottom: Radius.circular(34),
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            right: -45,
            top: -50,
            child: Container(
              width: 170,
              height: 170,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withOpacity(0.08),
              ),
            ),
          ),
          Positioned(
            left: -40,
            bottom: -60,
            child: Container(
              width: 140,
              height: 140,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF81D4FA)
                    .withOpacity(0.10),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(
              18,
              18,
              18,
              20,
            ),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    // بدل الجوهرة: كتاب
                    Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        gradient:
                            const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            Color(0xFFB3E5FC),
                            Color(0xFF29B6F6),
                            Color(0xFF5C6BC0),
                          ],
                        ),
                        borderRadius:
                            BorderRadius.circular(19),
                        boxShadow: [
                          BoxShadow(
                            color:
                                const Color(0xFF40C4FF)
                                    .withOpacity(0.35),
                            blurRadius: 18,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.menu_book_rounded,
                        color: Colors.white,
                        size: 31,
                      ),
                    ),
                    const SizedBox(width: 13),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,
                        children: [
                          Text(
                            'ASL Dictionary',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 23,
                              fontWeight:
                                  FontWeight.w900,
                              letterSpacing: 0.2,
                            ),
                          ),
                          SizedBox(height: 3),
                          Text(
                            'Discover signs from A to Z',
                            style: TextStyle(
                              color:
                                  Color(0xFFD8EEFF),
                              fontSize: 12,
                              fontWeight:
                                  FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding:
                          const EdgeInsets.symmetric(
                        horizontal: 11,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white
                            .withOpacity(0.15),
                        borderRadius:
                            BorderRadius.circular(14),
                        border: Border.all(
                          color: Colors.white
                              .withOpacity(0.18),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.sign_language_rounded,
                            color: Colors.white,
                            size: 17,
                          ),
                          const SizedBox(width: 5),
                          Text(
                            '${_allSigns.length + alphabet.length} signs',
                            style:
                                const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight:
                                  FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // Search
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius:
                        BorderRadius.circular(22),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black
                            .withOpacity(0.10),
                        blurRadius: 18,
                        offset:
                            const Offset(0, 7),
                      ),
                    ],
                  ),
                  child: TextField(
                    controller:
                        _searchController,
                    onChanged:
                        _searchChanged,
                    textInputAction:
                        TextInputAction.search,
                    decoration:
                        InputDecoration(
                      hintText:
                          'Search a sign...',
                      hintStyle:
                          const TextStyle(
                        color:
                            Color(0xFF9AA9B8),
                        fontSize: 13,
                      ),
                      border:
                          InputBorder.none,
                      prefixIcon:
                          const Icon(
                        Icons.search_rounded,
                        color:
                            Color(0xFF1565C0),
                      ),
                      suffixIcon:
                          _searchController
                                  .text
                                  .isNotEmpty
                              ? IconButton(
                                  onPressed:
                                      _clearSearch,
                                  icon:
                                      const Icon(
                                    Icons
                                        .close_rounded,
                                    color:
                                        Color(
                                      0xFF90A4AE,
                                    ),
                                  ),
                                )
                              : null,
                      contentPadding:
                          const EdgeInsets
                              .symmetric(
                        vertical: 17,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 15),

                Row(
                  children: [
                    const Icon(
                      Icons.sort_by_alpha_rounded,
                      color: Colors.white,
                      size: 17,
                    ),
                    const SizedBox(width: 6),
                    const Text(
                      'Browse by letter',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight:
                            FontWeight.w800,
                      ),
                    ),
                    const Spacer(),
                    if (_selectedLetter != 'ALL')
                      Text(
                        'Letter $_selectedLetter',
                        style:
                            const TextStyle(
                          color:
                              Color(0xFFD5EBFF),
                          fontSize: 10,
                        ),
                      ),
                  ],
                ),

                const SizedBox(height: 9),
                _buildLetterSelector(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLetterSelector() {
    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: alphabet.length + 1,
        separatorBuilder: (_, __) =>
            const SizedBox(width: 8),
        itemBuilder:
            (BuildContext context, int index) {
          if (index == 0) {
            return DictionaryLetterChip(
              label: 'ALL',
              count: _allSigns.length + alphabet.length,
              color:
                  const Color(0xFF29B6F6),
              enabled: true,
              selected:
                  _selectedLetter == 'ALL',
              onTap: () {
                _chooseLetter('ALL');
              },
            );
          }

          final String letter =
              alphabet[index - 1];

          final bool enabled =
              _letterExists(letter);

          return DictionaryLetterChip(
            label: letter,
            count:
                _letterCount(letter),
            color:
                dictionaryColorForLetter(
              letter,
            ),
            enabled: enabled,
            selected:
                _selectedLetter == letter,
            onTap: enabled
                ? () {
                    _chooseLetter(letter);
                  }
                : null,
          );
        },
      ),
    );
  }

  Widget _buildContent() {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(
          color: Color(0xFF1565C0),
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.cloud_off_rounded,
                size: 58,
                color: Color(0xFF90A4AE),
              ),
              const SizedBox(height: 16),
              Text(
                _error!,
                textAlign:
                    TextAlign.center,
                style:
                    const TextStyle(
                  color:
                      Color(0xFF607D8B),
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 18),
              FilledButton.icon(
                onPressed:
                    _loadDictionary,
                style:
                    FilledButton.styleFrom(
                  backgroundColor:
                      const Color(
                    0xFF1565C0,
                  ),
                ),
                icon: const Icon(
                  Icons.refresh_rounded,
                ),
                label:
                    const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (_visibleSigns.isEmpty &&
        _searchController.text.trim().isNotEmpty) {
      return Center(
        child: Container(
          margin:
              const EdgeInsets.all(24),
          padding:
              const EdgeInsets.all(26),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius:
                BorderRadius.circular(
              28,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black
                    .withOpacity(0.05),
                blurRadius: 20,
                offset:
                    const Offset(0, 8),
              ),
            ],
          ),
          child: const Column(
            mainAxisSize:
                MainAxisSize.min,
            children: [
              Icon(
                Icons.search_off_rounded,
                size: 55,
                color:
                    Color(0xFF9BB0C3),
              ),
              SizedBox(height: 14),
              Text(
                'No signs found',
                style: TextStyle(
                  color:
                      Color(0xFF18314F),
                  fontSize: 19,
                  fontWeight:
                      FontWeight.w900,
                ),
              ),
              SizedBox(height: 6),
              Text(
                'Try searching for another word or choose another letter.',
                textAlign:
                    TextAlign.center,
                style: TextStyle(
                  color:
                      Color(0xFF73869A),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      );
    }

    final Map<String, List<DictionarySign>>
        groups =
        _groupSignsByLetter();

    final List<String> letters =
        groups.keys.toList()
          ..sort();

    return RefreshIndicator(
      color:
          const Color(0xFF1565C0),
      onRefresh:
          _loadDictionary,
      child: ListView.builder(
        padding:
            const EdgeInsets.fromLTRB(
          16,
          18,
          16,
          115,
        ),
        itemCount:
            letters.length,
        itemBuilder:
            (BuildContext context, int index) {
          final String letter =
              letters[index];

          return DictionaryLetterSection(
            letter: letter,
            signs:
                groups[letter]!,
            color:
                dictionaryColorForLetter(
              letter,
            ),
            onWordTap:
                _openWord,
          );
        },
      ),
    );
  }
}


// ============================================================
// LETTER CHIP
// ============================================================

class DictionaryLetterChip extends StatelessWidget {
  final String label;
  final int count;
  final Color color;
  final bool enabled;
  final bool selected;
  final VoidCallback? onTap;

  const DictionaryLetterChip({
    super.key,
    required this.label,
    required this.count,
    required this.color,
    required this.enabled,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity:
          enabled ? 1 : 0.38,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap:
              enabled ? onTap : null,
          borderRadius:
              BorderRadius.circular(
            16,
          ),
          child: AnimatedContainer(
            duration:
                const Duration(
              milliseconds: 180,
            ),
            padding:
                const EdgeInsets.symmetric(
              horizontal: 13,
              vertical: 9,
            ),
            decoration: BoxDecoration(
              color: selected
                  ? Colors.white
                  : Colors.white
                      .withOpacity(0.12),
              borderRadius:
                  BorderRadius.circular(
                16,
              ),
              border: Border.all(
                color: selected
                    ? Colors.white
                    : Colors.white
                        .withOpacity(
                          0.16,
                        ),
              ),
              boxShadow: selected
                  ? [
                      BoxShadow(
                        color: color
                            .withOpacity(
                          0.35,
                        ),
                        blurRadius: 14,
                      ),
                    ]
                  : null,
            ),
            child: Row(
              mainAxisSize:
                  MainAxisSize.min,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    color: selected
                        ? color
                        : Colors.white,
                    fontWeight:
                        FontWeight.w900,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(width: 6),
                Container(
                  padding:
                      const EdgeInsets.symmetric(
                    horizontal: 5,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: selected
                        ? color.withOpacity(
                            0.10,
                          )
                        : Colors.white
                            .withOpacity(
                              0.13,
                            ),
                    borderRadius:
                        BorderRadius.circular(
                      8,
                    ),
                  ),
                  child: Text(
                    '$count',
                    style: TextStyle(
                      color: selected
                          ? color
                          : Colors.white,
                      fontSize: 9,
                      fontWeight:
                          FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}


// ============================================================
// LETTER SECTION
// ============================================================

class DictionaryLetterSection extends StatelessWidget {
  final String letter;
  final List<DictionarySign> signs;
  final Color color;
  final ValueChanged<DictionarySign>
      onWordTap;

  const DictionaryLetterSection({
    super.key,
    required this.letter,
    required this.signs,
    required this.color,
    required this.onWordTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin:
          const EdgeInsets.only(
        bottom: 20,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius:
            BorderRadius.circular(
          28,
        ),
        border: Border.all(
          color: color.withOpacity(
            0.15,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color:
                color.withOpacity(
              0.08,
            ),
            blurRadius: 18,
            offset:
                const Offset(0, 7),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            padding:
                const EdgeInsets.all(
              16,
            ),
            decoration: BoxDecoration(
              gradient:
                  LinearGradient(
                colors: [
                  color.withOpacity(
                    0.20,
                  ),
                  color.withOpacity(
                    0.045,
                  ),
                ],
              ),
              borderRadius:
                  const BorderRadius
                      .vertical(
                top:
                    Radius.circular(
                  28,
                ),
              ),
            ),
            child: Row(
              children: [
                Transform.rotate(
                  angle: 0.785398,
                  child: Container(
                    width: 46,
                    height: 46,
                    decoration:
                        BoxDecoration(
                      gradient:
                          LinearGradient(
                        begin:
                            Alignment.topLeft,
                        end:
                            Alignment
                                .bottomRight,
                        colors: [
                          color.withOpacity(
                            0.75,
                          ),
                          color,
                        ],
                      ),
                      borderRadius:
                          BorderRadius
                              .circular(
                        12,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: color
                              .withOpacity(
                            0.35,
                          ),
                          blurRadius: 12,
                        ),
                      ],
                    ),
                    child:
                        Transform.rotate(
                      angle:
                          -0.785398,
                      child: Center(
                        child: Text(
                          letter,
                          style:
                              const TextStyle(
                            color:
                                Colors.white,
                            fontSize: 21,
                            fontWeight:
                                FontWeight
                                    .w900,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(
                  width: 17,
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment
                            .start,
                    children: [
                      Text(
                        '$letter Words',
                        style:
                            TextStyle(
                          color: color,
                          fontSize: 19,
                          fontWeight:
                              FontWeight
                                  .w900,
                        ),
                      ),
                      const SizedBox(
                        height: 2,
                      ),
                      Text(
                        '${signs.length + 1} ASL signs',
                        style:
                            const TextStyle(
                          color:
                              Color(
                            0xFF71849A,
                          ),
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.auto_stories_rounded,
                  color:
                      color.withOpacity(
                    0.55,
                  ),
                  size: 21,
                ),
              ],
            ),
          ),
          // ----------------------------------------------------
          // ASL ALPHABET IMAGE - always the first item
          // ----------------------------------------------------
          ListTile(
            onTap: () {
              showDialog<void>(
                context: context,
                builder: (BuildContext dialogContext) {
                  final String imageUrl =
                      '$dictionaryBaseUrl/api/dictionary/letters-media/${letter.toLowerCase()}.png';

                  return Dialog(
                    backgroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(26),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 42,
                                height: 42,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: color.withOpacity(0.10),
                                  borderRadius: BorderRadius.circular(13),
                                ),
                                child: Text(
                                  letter,
                                  style: TextStyle(
                                    color: color,
                                    fontSize: 20,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'ASL Letter $letter',
                                  style: const TextStyle(
                                    color: Color(0xFF18314F),
                                    fontSize: 18,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ),
                              IconButton(
                                onPressed: () {
                                  Navigator.of(dialogContext).pop();
                                },
                                icon: const Icon(Icons.close_rounded),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(18),
                            child: Container(
                              color: const Color(0xFFF7FAFD),
                              constraints: const BoxConstraints(
                                maxHeight: 420,
                              ),
                              child: Image.network(
                                imageUrl,
                                fit: BoxFit.contain,
                                errorBuilder: (
                                  BuildContext context,
                                  Object error,
                                  StackTrace? stackTrace,
                                ) {
                                  return SizedBox(
                                    height: 220,
                                    child: Center(
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(
                                            Icons.broken_image_rounded,
                                            color: color,
                                            size: 45,
                                          ),
                                          const SizedBox(height: 10),
                                          Text(
                                            'Could not load letter $letter image',
                                            style: const TextStyle(
                                              color: Color(0xFF607D8B),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 17,
              vertical: 7,
            ),
            leading: Container(
              width: 52,
              height: 52,
              clipBehavior: Clip.antiAlias,
              decoration: BoxDecoration(
                color: color.withOpacity(0.08),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: color.withOpacity(0.12),
                ),
              ),
              child: Image.network(
                '$dictionaryBaseUrl/api/dictionary/letters-media/${letter.toLowerCase()}.png',
                fit: BoxFit.contain,
                errorBuilder: (
                  BuildContext context,
                  Object error,
                  StackTrace? stackTrace,
                ) {
                  return Center(
                    child: Text(
                      letter,
                      style: TextStyle(
                        color: color,
                        fontSize: 23,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  );
                },
              ),
            ),
            title: Text(
              letter,
              style: const TextStyle(
                color: Color(0xFF18314F),
                fontSize: 15,
                fontWeight: FontWeight.w900,
              ),
            ),
            subtitle: Text(
              'View ASL alphabet letter',
              style: TextStyle(
                color: color.withOpacity(0.82),
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
            trailing: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: color.withOpacity(0.08),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                Icons.image_rounded,
                color: color,
                size: 17,
              ),
            ),
          ),
          Divider(
            height: 1,
            indent: 74,
            color: color.withOpacity(0.09),
          ),
          ListView.separated(
            shrinkWrap: true,
            physics:
                const NeverScrollableScrollPhysics(),
            itemCount:
                signs.length,
            separatorBuilder:
                (_, __) {
              return Divider(
                height: 1,
                indent: 74,
                color: color
                    .withOpacity(
                  0.09,
                ),
              );
            },
            itemBuilder:
                (
              BuildContext context,
              int index,
            ) {
              final DictionarySign sign =
                  signs[index];

              return ListTile(
                onTap: () {
                  onWordTap(sign);
                },
                contentPadding:
                    const EdgeInsets
                        .symmetric(
                  horizontal: 17,
                  vertical: 5,
                ),
                leading: Container(
                  width: 45,
                  height: 45,
                  decoration:
                      BoxDecoration(
                    color:
                        color.withOpacity(
                      0.10,
                    ),
                    borderRadius:
                        BorderRadius
                            .circular(
                      14,
                    ),
                  ),
                  child: Icon(
                    Icons
                        .play_arrow_rounded,
                    color: color,
                    size: 27,
                  ),
                ),
                title: Row(
                  children: [
                    Text(
                      dictionaryEmojiForWord(
                        sign.word,
                      ),
                      style: const TextStyle(
                        fontSize: 19,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        sign.word,
                        style:
                            const TextStyle(
                          color:
                              Color(
                            0xFF18314F,
                          ),
                          fontSize: 14,
                          fontWeight:
                              FontWeight
                                  .w900,
                        ),
                      ),
                    ),
                  ],
                ),
                subtitle: Text(
                  'Watch the sign',
                  style: TextStyle(
                    color: color
                        .withOpacity(
                      0.82,
                    ),
                    fontSize: 11,
                    fontWeight:
                        FontWeight
                            .w600,
                  ),
                ),
                trailing:
                    Container(
                  width: 32,
                  height: 32,
                  decoration:
                      BoxDecoration(
                    color:
                        color.withOpacity(
                      0.08,
                    ),
                    borderRadius:
                        BorderRadius
                            .circular(
                      10,
                    ),
                  ),
                  child: Icon(
                    Icons
                        .arrow_forward_ios_rounded,
                    color: color,
                    size: 13,
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}


// ============================================================
// DETAILS PAGE
// ============================================================

class DictionaryDetailsPage extends StatefulWidget {
  final int signId;

  const DictionaryDetailsPage({
    super.key,
    required this.signId,
  });

  @override
  State<DictionaryDetailsPage> createState() =>
      _DictionaryDetailsPageState();
}

class _DictionaryDetailsPageState
    extends State<DictionaryDetailsPage> {
  DictionarySign? _sign;
  DictionarySign? _previous;
  DictionarySign? _next;

  VideoPlayerController?
      _videoController;

  bool _loading = true;
  String? _error;

  double _speed = 1.0;

  @override
  void initState() {
    super.initState();
    _loadSign();
  }

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  Future<void> _loadSign() async {
    try {
      final Uri uri = Uri.parse(
        '$dictionaryBaseUrl/api/dictionary/signs/${widget.signId}',
      );

      final http.Response response =
          await http
              .get(uri)
              .timeout(
                const Duration(
                  seconds: 12,
                ),
              );

      if (response.statusCode != 200) {
        throw Exception(
          'Could not load this sign.',
        );
      }

      final Map<String, dynamic> data =
          Map<String, dynamic>.from(
        jsonDecode(response.body),
      );

      final DictionarySign sign =
          DictionarySign.fromJson(
        Map<String, dynamic>.from(
          data['sign'],
        ),
      );

      DictionarySign? previous;
      DictionarySign? next;

      if (data['previous'] != null) {
        previous =
            DictionarySign.fromJson(
          Map<String, dynamic>.from(
            data['previous'],
          ),
        );
      }

      if (data['next'] != null) {
        next =
            DictionarySign.fromJson(
          Map<String, dynamic>.from(
            data['next'],
          ),
        );
      }

      final VideoPlayerController controller =
          VideoPlayerController.networkUrl(
        Uri.parse(
          sign.videoUrl,
        ),
      );

      await controller.initialize();
      await controller.setLooping(true);
      await controller.play();

      if (!mounted) {
        controller.dispose();
        return;
      }

      setState(() {
        _sign = sign;
        _previous = previous;
        _next = next;
        _videoController =
            controller;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
        _error =
            'Unable to load video.\n$error';
      });
    }
  }

  Future<void> _playPause() async {
    final VideoPlayerController? controller =
        _videoController;

    if (controller == null) {
      return;
    }

    if (controller.value.isPlaying) {
      await controller.pause();
    } else {
      await controller.play();
    }

    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _replay() async {
    final VideoPlayerController? controller =
        _videoController;

    if (controller == null) {
      return;
    }

    await controller.seekTo(Duration.zero);
    await controller.play();

    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _changeSpeed() async {
    final VideoPlayerController? controller =
        _videoController;

    if (controller == null) {
      return;
    }

    final double newSpeed =
        _speed == 1.0 ? 0.5 : 1.0;

    await controller.setPlaybackSpeed(
      newSpeed,
    );

    if (mounted) {
      setState(() {
        _speed = newSpeed;
      });
    }
  }

  Future<void> _openWord(
    DictionarySign sign,
  ) async {
    await Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) {
          return DictionaryDetailsPage(
            signId: sign.id,
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final Color accent =
        dictionaryColorForLetter(
      _sign?.letter ?? 'A',
    );

    return Scaffold(
      backgroundColor:
          const Color(0xFFF3F8FF),
      appBar: AppBar(
        elevation: 0,
        backgroundColor:
            const Color(0xFFF3F8FF),
        surfaceTintColor:
            Colors.transparent,
        foregroundColor:
            const Color(0xFF18314F),
        title:
            const Text(
          'Sign Details',
          style: TextStyle(
            fontWeight:
                FontWeight.w900,
          ),
        ),
      ),
      body: _buildBody(accent),
    );
  }

  Widget _buildBody(Color accent) {
    if (_loading) {
      return Center(
        child:
            CircularProgressIndicator(
          color: accent,
        ),
      );
    }

    if (_error != null ||
        _sign == null) {
      return Center(
        child: Padding(
          padding:
              const EdgeInsets.all(
            28,
          ),
          child: Text(
            _error ??
                'Sign not found.',
            textAlign:
                TextAlign.center,
            style:
                const TextStyle(
              color:
                  Color(0xFF607D8B),
              fontSize: 14,
            ),
          ),
        ),
      );
    }

    final DictionarySign sign =
        _sign!;

    return ListView(
      padding:
          const EdgeInsets.fromLTRB(
        16,
        10,
        16,
        30,
      ),
      children: [
        Container(
          padding:
              const EdgeInsets.all(
            18,
          ),
          decoration: BoxDecoration(
            gradient:
                LinearGradient(
              begin:
                  Alignment.topLeft,
              end:
                  Alignment.bottomRight,
              colors: [
                accent.withOpacity(
                  0.20,
                ),
                accent.withOpacity(
                  0.05,
                ),
                Colors.white,
              ],
            ),
            borderRadius:
                BorderRadius.circular(
              30,
            ),
            border: Border.all(
              color:
                  accent.withOpacity(
                0.15,
              ),
            ),
            boxShadow: [
              BoxShadow(
                color: accent
                    .withOpacity(
                  0.10,
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
          child: Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 52,
                    height: 52,
                    decoration:
                        BoxDecoration(
                      gradient:
                          LinearGradient(
                        colors: [
                          accent
                              .withOpacity(
                            0.75,
                          ),
                          accent,
                        ],
                      ),
                      borderRadius:
                          BorderRadius
                              .circular(
                        16,
                      ),
                    ),
                    child: const Icon(
                      Icons.menu_book_rounded,
                      color: Colors.white,
                      size: 28,
                    ),
                  ),
                  const SizedBox(
                    width: 14,
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment:
                          CrossAxisAlignment
                              .start,
                      children: [
                        Row(
                          children: [
                            Text(
                              dictionaryEmojiForWord(
                                sign.word,
                              ),
                              style: const TextStyle(
                                fontSize: 28,
                              ),
                            ),
                            const SizedBox(width: 9),
                            Expanded(
                              child: Text(
                                sign.word,
                                style:
                                    const TextStyle(
                                  color:
                                      Color(
                                    0xFF102A43,
                                  ),
                                  fontSize: 27,
                                  fontWeight:
                                      FontWeight
                                          .w900,
                                ),
                              ),
                            ),
                          ],
                        ),
                        Text(
                          'American Sign Language',
                          style:
                              TextStyle(
                            color:
                                accent,
                            fontSize: 11,
                            fontWeight:
                                FontWeight
                                    .w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(
                height: 20,
              ),

              // فيديو بإطار ملون
              Container(
                padding: const EdgeInsets.all(3),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      accent.withOpacity(0.95),
                      accent.withOpacity(0.55),
                      const Color(0xFF4FC3F7),
                    ],
                  ),
                  borderRadius:
                      BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: accent.withOpacity(0.28),
                      blurRadius: 18,
                      offset: const Offset(0, 7),
                    ),
                  ],
                ),
                child: Container(
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                    color: const Color(0xFF101827),
                    borderRadius:
                        BorderRadius.circular(21),
                  ),
                  child: Column(
                    children: [
                      _buildVideo(),
                      Container(
                        width: double.infinity,
                        padding:
                            const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 10,
                        ),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              accent.withOpacity(0.95),
                              accent.withOpacity(0.70),
                            ],
                          ),
                        ),
                        child: const Text(
                          'ASL video preview',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(
                height: 14,
              ),

              Row(
                children: [
                  Expanded(
                    child:
                        DictionaryVideoButton(
                      icon: _videoController
                                  ?.value
                                  .isPlaying ==
                              true
                          ? Icons.pause_rounded
                          : Icons.play_arrow_rounded,
                      label: _videoController
                                  ?.value
                                  .isPlaying ==
                              true
                          ? 'Pause'
                          : 'Play',
                      color: accent,
                      onTap: _playPause,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child:
                        DictionaryVideoButton(
                      icon:
                          Icons.replay_rounded,
                      label:
                          'Replay',
                      color: accent,
                      onTap: _replay,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child:
                        DictionaryVideoButton(
                      icon:
                          Icons.speed_rounded,
                      label:
                          '${_speed}x',
                      color: accent,
                      onTap: _changeSpeed,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 18),

        Container(
          padding:
              const EdgeInsets.all(
            18,
          ),
          decoration:
              BoxDecoration(
            color: Colors.white,
            borderRadius:
                BorderRadius.circular(
              25,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black
                    .withOpacity(
                  0.045,
                ),
                blurRadius: 16,
                offset:
                    const Offset(
                  0,
                  6,
                ),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.all(8),
                    decoration:
                        BoxDecoration(
                      color: accent
                          .withOpacity(0.10),
                      borderRadius:
                          BorderRadius
                              .circular(
                        10,
                      ),
                    ),
                    child: Icon(
                      Icons.info_outline_rounded,
                      color: accent,
                      size: 18,
                    ),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Sign Information',
                    style: TextStyle(
                      color:
                          Color(0xFF18314F),
                      fontSize: 16,
                      fontWeight:
                          FontWeight.w900,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 17),
              DictionaryInfoRow(
                title: 'Word',
                value:
                    '${dictionaryEmojiForWord(sign.word)} ${sign.word}',
              ),
              DictionaryInfoRow(
                title: 'Letter',
                value: sign.letter,
              ),
              DictionaryInfoRow(
                title: 'Language',
                value: 'ASL',
              ),
              DictionaryInfoRow(
                title: 'Source',
                value: sign.source,
              ),
            ],
          ),
        ),

        const SizedBox(height: 18),

        if (_previous != null ||
            _next != null)
          Container(
            padding:
                const EdgeInsets.all(
              18,
            ),
            decoration:
                BoxDecoration(
              color: Colors.white,
              borderRadius:
                  BorderRadius.circular(
                25,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black
                      .withOpacity(
                    0.045,
                  ),
                  blurRadius: 16,
                  offset:
                      const Offset(
                    0,
                    6,
                  ),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                const Text(
                  'Continue Exploring',
                  style:
                      TextStyle(
                    color:
                        Color(
                      0xFF18314F,
                    ),
                    fontSize: 16,
                    fontWeight:
                        FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 13),
                if (_previous != null)
                  DictionaryBrowseWord(
                    label: 'Previous',
                    sign: _previous!,
                    backwards: true,
                    onTap: _openWord,
                  ),
                if (_previous != null &&
                    _next != null)
                  const SizedBox(height: 10),
                if (_next != null)
                  DictionaryBrowseWord(
                    label: 'Next',
                    sign: _next!,
                    backwards: false,
                    onTap: _openWord,
                  ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildVideo() {
    final VideoPlayerController? controller =
        _videoController;

    if (controller == null ||
        !controller.value.isInitialized) {
      return const AspectRatio(
        aspectRatio: 16 / 9,
        child: Center(
          child:
              CircularProgressIndicator(
            color: Colors.white,
          ),
        ),
      );
    }

    double aspectRatio =
        controller.value.aspectRatio;

    if (aspectRatio <= 0) {
      aspectRatio = 16 / 9;
    }

    return AspectRatio(
      aspectRatio:
          aspectRatio,
      child:
          VideoPlayer(
        controller,
      ),
    );
  }
}


// ============================================================
// VIDEO BUTTON
// ============================================================

class DictionaryVideoButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const DictionaryVideoButton({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color:
          Colors.transparent,
      child: InkWell(
        onTap:
            onTap,
        borderRadius:
            BorderRadius.circular(
          16,
        ),
        child: Ink(
          padding:
              const EdgeInsets.symmetric(
            vertical: 12,
            horizontal: 7,
          ),
          decoration:
              BoxDecoration(
            color: Colors.white,
            borderRadius:
                BorderRadius.circular(
              16,
            ),
            border:
                Border.all(
              color:
                  color.withOpacity(
                0.15,
              ),
            ),
          ),
          child: Row(
            mainAxisAlignment:
                MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                color:
                    color,
                size: 18,
              ),
              const SizedBox(width: 5),
              Flexible(
                child: Text(
                  label,
                  overflow:
                      TextOverflow
                          .ellipsis,
                  style:
                      const TextStyle(
                    color:
                        Color(
                      0xFF18314F,
                    ),
                    fontSize: 11,
                    fontWeight:
                        FontWeight
                            .w800,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


// ============================================================
// PREVIOUS / NEXT
// ============================================================

class DictionaryBrowseWord extends StatelessWidget {
  final String label;
  final DictionarySign sign;
  final bool backwards;
  final ValueChanged<DictionarySign>
      onTap;

  const DictionaryBrowseWord({
    super.key,
    required this.label,
    required this.sign,
    required this.backwards,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final Color color =
        dictionaryColorForLetter(
      sign.letter,
    );

    return Material(
      color:
          Colors.transparent,
      child: InkWell(
        onTap: () {
          onTap(sign);
        },
        borderRadius:
            BorderRadius.circular(
          18,
        ),
        child: Ink(
          padding:
              const EdgeInsets.all(
            13,
          ),
          decoration:
              BoxDecoration(
            color:
                color.withOpacity(
              0.07,
            ),
            borderRadius:
                BorderRadius.circular(
              18,
            ),
            border:
                Border.all(
              color:
                  color.withOpacity(
                0.10,
              ),
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 39,
                height: 39,
                decoration:
                    BoxDecoration(
                  color:
                      color,
                  borderRadius:
                      BorderRadius.circular(
                    12,
                  ),
                ),
                child:
                    Icon(
                  backwards
                      ? Icons.arrow_back_rounded
                      : Icons.arrow_forward_rounded,
                  color:
                      Colors.white,
                  size: 19,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment
                          .start,
                  children: [
                    Text(
                      label,
                      style:
                          TextStyle(
                        color:
                            color,
                        fontSize:
                            10,
                        fontWeight:
                            FontWeight
                                .w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Text(
                          dictionaryEmojiForWord(
                            sign.word,
                          ),
                          style: const TextStyle(
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            sign.word,
                            style:
                                const TextStyle(
                              color:
                                  Color(
                                0xFF18314F,
                              ),
                              fontSize:
                                  14,
                              fontWeight:
                                  FontWeight
                                      .w900,
                            ),
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
      ),
    );
  }
}


// ============================================================
// INFO ROW
// ============================================================

class DictionaryInfoRow extends StatelessWidget {
  final String title;
  final String value;

  const DictionaryInfoRow({
    super.key,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding:
          const EdgeInsets.only(
        bottom: 11,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 90,
            child: Text(
              '$title:',
              style:
                  const TextStyle(
                color:
                    Color(
                  0xFF6C8094,
                ),
                fontSize:
                    12,
                fontWeight:
                    FontWeight
                        .w600,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style:
                  const TextStyle(
                color:
                    Color(
                  0xFF18314F,
                ),
                fontSize:
                    13,
                fontWeight:
                    FontWeight
                        .w800,
              ),
            ),
          ),
        ],
      ),
    );
  }
}


// ============================================================
// MODELS
// ============================================================

class DictionaryLetter {
  final String letter;
  final int count;

  const DictionaryLetter({
    required this.letter,
    required this.count,
  });

  factory DictionaryLetter.fromJson(
    Map<String, dynamic> json,
  ) {
    return DictionaryLetter(
      letter:
          json['letter']?.toString() ?? '#',
      count:
          int.tryParse(
                json['count']?.toString() ??
                    '0',
              ) ??
              0,
    );
  }
}

class DictionarySign {
  final int id;
  final String word;
  final String letter;
  final String videoUrl;
  final String source;

  const DictionarySign({
    required this.id,
    required this.word,
    required this.letter,
    required this.videoUrl,
    required this.source,
  });

  factory DictionarySign.fromJson(
    Map<String, dynamic> json,
  ) {
    return DictionarySign(
      id:
          int.tryParse(
                json['id']?.toString() ??
                    '0',
              ) ??
              0,
      word:
          json['word']?.toString() ?? '',
      letter:
          json['letter']?.toString() ?? '#',
      videoUrl:
          json['video_url']?.toString() ?? '',
      source:
          json['source']?.toString() ??
              'ASL Citizen',
    );
  }
}