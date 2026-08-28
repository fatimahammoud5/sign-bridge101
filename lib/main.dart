import 'package:flutter/material.dart';
import 'services/local_notification_service.dart';
import 'screens/main_navigation_screen.dart';
import 'services/sound_monitoring_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await LocalNotificationService.instance.initialize();
  await SoundMonitoringService.initialize();

  runApp(const SignBridgeApp());
}

class SignBridgeApp extends StatelessWidget {
  const SignBridgeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'SignBridge',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF7F9FC),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2457D6),
        ),
      ),
      home: const MainNavigationScreen(),
    );
  }
}