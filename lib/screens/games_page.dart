import 'package:flutter/material.dart';

class GamesPage extends StatelessWidget {
  const GamesPage({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(
        0xFFF8F9FD,
      ),
      body: SafeArea(
        child: Center(
          child: Text(
            'ASL Games',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w900,
              color: Color(
                0xFF20243A,
              ),
            ),
          ),
        ),
      ),
    );
  }
}