import 'package:flutter/material.dart';

class SosPage extends StatelessWidget {
  const SosPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF5F5),
      appBar: AppBar(
        title: const Text('Emergency Help'),
        backgroundColor: const Color(0xFFFFF5F5),
      ),
      body: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 45,
              backgroundColor: Color(0xFFFFDADA),
              child: Icon(
                Icons.sos_rounded,
                size: 48,
                color: Color(0xFFE53935),
              ),
            ),
            SizedBox(height: 20),
            Text(
              'Do you need emergency assistance?',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}