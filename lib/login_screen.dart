import 'package:flutter/material.dart';

import 'screens/main_navigation_screen.dart';
import 'services/auth_service.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  static const Color purple = Color(0xFF6C3BFF);
  static const Color lightPurple = Color(0xFFF5F1FF);
  static const Color textDark = Color(0xFF1F2340);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController emailController =
      TextEditingController(text: 'test@hearhelp.com');

  final TextEditingController passwordController =
      TextEditingController(text: '12345678');

  bool isLoading = false;
  bool obscurePassword = true;

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Future<void> login() async {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      showMessage('Please enter email and password');
      return;
    }

    setState(() {
      isLoading = true;
    });

    try {
      await AuthService.login(
        email: email,
        password: password,
      );

      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const MainNavigationScreen(),
        ),
      );
    } catch (e) {
      showMessage(e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    }
  }

  void showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.redAccent,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const Color purple = LoginScreen.purple;
    const Color lightPurple = LoginScreen.lightPurple;
    const Color textDark = LoginScreen.textDark;

    return Scaffold(
      backgroundColor: lightPurple,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const SizedBox(height: 40),

              Container(
                height: 120,
                width: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: purple.withOpacity(0.12),
                  boxShadow: [
                    BoxShadow(
                      color: purple.withOpacity(0.18),
                      blurRadius: 25,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.hearing,
                  size: 65,
                  color: purple,
                ),
              ),

              const SizedBox(height: 22),

              const Text(
                "Hear & Help",
                style: TextStyle(
                  fontSize: 34,
                  fontWeight: FontWeight.bold,
                  color: purple,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                "Empowering deaf people\nthrough smart technology",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.black54,
                  height: 1.5,
                ),
              ),

              const SizedBox(height: 42),

              const Text(
                "Welcome Back 👋",
                style: TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                  color: textDark,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                "Login to continue",
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.black45,
                ),
              ),

              const SizedBox(height: 34),

              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: purple.withOpacity(0.12),
                      blurRadius: 30,
                      offset: const Offset(0, 14),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Email",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: textDark,
                      ),
                    ),

                    const SizedBox(height: 10),

                    TextField(
                      controller: emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: InputDecoration(
                        hintText: "Enter your email",
                        prefixIcon: const Icon(Icons.email_outlined),
                        filled: true,
                        fillColor: lightPurple,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),

                    const SizedBox(height: 24),

                    const Text(
                      "Password",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: textDark,
                      ),
                    ),

                    const SizedBox(height: 10),

                    TextField(
                      controller: passwordController,
                      obscureText: obscurePassword,
                      decoration: InputDecoration(
                        hintText: "Enter your password",
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          icon: Icon(
                            obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                          onPressed: () {
                            setState(() {
                              obscurePassword = !obscurePassword;
                            });
                          },
                        ),
                        filled: true,
                        fillColor: lightPurple,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
                        Row(
                          children: [
                            Icon(
                              Icons.check_box,
                              color: purple,
                            ),
                            SizedBox(width: 8),
                            Text("Remember me"),
                          ],
                        ),
                        Text(
                          "Forgot Password?",
                          style: TextStyle(
                            color: purple,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 28),

                    SizedBox(
                      width: double.infinity,
                      height: 58,
                      child: ElevatedButton.icon(
                        onPressed: isLoading ? null : login,
                        icon: isLoading
                            ? const SizedBox(
                                height: 22,
                                width: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.login),
                        label: Text(
                          isLoading ? "Logging in..." : "Login",
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: purple,
                          foregroundColor: Colors.white,
                          elevation: 10,
                          shadowColor: purple.withOpacity(0.35),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 24),

                    Row(
                      children: const [
                        Expanded(child: Divider()),
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 12),
                          child: Text("or"),
                        ),
                        Expanded(child: Divider()),
                      ],
                    ),

                    const SizedBox(height: 24),

                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: OutlinedButton.icon(
                       onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const RegisterScreen(),
                          ),
                        );
                      },
                        icon: const Icon(Icons.person_add_alt),
                        label: const Text(
                          "Create New Account",
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: purple,
                          side: const BorderSide(
                            color: purple,
                            width: 1.5,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 18),

                    const Center(
                      child: Text(
                        "Your data is safe and secure with us",
                        style: TextStyle(
                          color: Colors.black45,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 28),

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Text("Don’t have an account? "),
                  Text(
                    "Sign Up",
                    style: TextStyle(
                      color: purple,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }
}