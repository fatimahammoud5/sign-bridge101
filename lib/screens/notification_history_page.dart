import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/alert_record.dart';
import '../services/notification_history_service.dart';

class NotificationHistoryPage extends StatefulWidget {
  const NotificationHistoryPage({super.key});

  @override
  State<NotificationHistoryPage> createState() =>
      _NotificationHistoryPageState();
}

class _NotificationHistoryPageState
    extends State<NotificationHistoryPage> {
  static const Color purple = Color(0xFF7B2FF7);
  static const Color orange = Color(0xFFFF8C42);
  static const Color darkText = Color(0xFF20243A);

  final NotificationHistoryService _historyService =
      NotificationHistoryService.instance;

  List<AlertRecord> _history = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();

    _historyService.historyVersion.addListener(
      _handleHistoryChanged,
    );

    _loadHistory();
  }

  @override
  void dispose() {
    _historyService.historyVersion.removeListener(
      _handleHistoryChanged,
    );

    super.dispose();
  }

  void _handleHistoryChanged() {
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final history = await _historyService.getHistory();

    if (!mounted) {
      return;
    }

    setState(() {
      _history = history;
      _isLoading = false;
    });
  }

  Future<void> _deleteRecord(
    AlertRecord record,
  ) async {
    await _historyService.deleteRecord(record.id);
  }

  Future<void> _confirmClearAll() async {
    if (_history.isEmpty) {
      return;
    }

    final shouldClear = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Clear all notifications?'),
          content: const Text(
            'All saved Voice Assist notifications will be deleted.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context, false);
              },
              child: const Text('Cancel'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: Colors.red,
              ),
              onPressed: () {
                Navigator.pop(context, true);
              },
              child: const Text('Clear All'),
            ),
          ],
        );
      },
    );

    if (shouldClear == true) {
      await _historyService.clearHistory();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F6FC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: darkText,
        centerTitle: true,
        title: const Text(
          'Notifications',
          style: TextStyle(
            fontWeight: FontWeight.w900,
          ),
        ),
        actions: [
          if (_history.isNotEmpty)
            TextButton(
              onPressed: _confirmClearAll,
              child: const Text(
                'Clear all',
                style: TextStyle(
                  color: Colors.red,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          const SizedBox(width: 6),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(
                color: purple,
              ),
            )
          : _history.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  color: purple,
                  onRefresh: _loadHistory,
                  child: ListView.separated(
                    padding: const EdgeInsets.fromLTRB(
                      18,
                      14,
                      18,
                      30,
                    ),
                    itemCount: _history.length,
                    separatorBuilder: (context, index) {
                      return const SizedBox(height: 12);
                    },
                    itemBuilder: (context, index) {
                      return _buildHistoryCard(
                        _history[index],
                      );
                    },
                  ),
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 110,
              height: 110,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    purple.withValues(alpha: 0.15),
                    orange.withValues(alpha: 0.15),
                  ],
                ),
              ),
              child: const Icon(
                Icons.notifications_none_rounded,
                color: purple,
                size: 52,
              ),
            ),
            const SizedBox(height: 22),
            const Text(
              'No notifications yet',
              style: TextStyle(
                color: darkText,
                fontSize: 20,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Detected sounds will be saved here with their time and importance.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Color(0xFF7B8494),
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryCard(AlertRecord record) {
    final date = DateFormat(
      'dd MMM yyyy',
    ).format(record.createdAt);

    final time = DateFormat(
      'h:mm a',
    ).format(record.createdAt);

    return Dismissible(
      key: ValueKey(record.id),
      direction: DismissDirection.endToStart,
      background: Container(
        padding: const EdgeInsets.only(right: 24),
        alignment: Alignment.centerRight,
        decoration: BoxDecoration(
          color: Colors.red,
          borderRadius: BorderRadius.circular(22),
        ),
        child: const Icon(
          Icons.delete_rounded,
          color: Colors.white,
          size: 30,
        ),
      ),
      onDismissed: (_) {
        _deleteRecord(record);
      },
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: record.color.withValues(alpha: 0.25),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.045),
              blurRadius: 12,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: record.backgroundColor,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                record.icon,
                color: record.color,
                size: 27,
              ),
            ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          record.title,
                          style: const TextStyle(
                            color: darkText,
                            fontSize: 16,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                      Container(
                        padding:
                            const EdgeInsets.symmetric(
                          horizontal: 9,
                          vertical: 5,
                        ),
                        decoration: BoxDecoration(
                          color: record.backgroundColor,
                          borderRadius:
                              BorderRadius.circular(20),
                        ),
                        child: Text(
                          record.severityName,
                          style: TextStyle(
                            color: record.color,
                            fontSize: 11,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    record.description,
                    style: const TextStyle(
                      color: Color(0xFF6F7787),
                      fontSize: 13,
                      height: 1.35,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Icon(
                        Icons.schedule_rounded,
                        size: 16,
                        color: record.color,
                      ),
                      const SizedBox(width: 5),
                      Expanded(
                        child: Text(
                          '$date • $time',
                          style: const TextStyle(
                            color: Color(0xFF8991A0),
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      Text(
                        record.formattedConfidence,
                        style: TextStyle(
                          color: record.color,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(width: 4),
            IconButton(
              tooltip: 'Delete',
              onPressed: () {
                _deleteRecord(record);
              },
              icon: const Icon(
                Icons.delete_outline_rounded,
                color: Colors.black38,
              ),
            ),
          ],
        ),
      ),
    );
  }
}