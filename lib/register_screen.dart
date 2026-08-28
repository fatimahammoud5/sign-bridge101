import 'package:flutter/material.dart';

import 'screens/main_navigation_screen.dart';
import 'login_screen.dart';
import 'services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  static const Color purple = Color(0xFF6C3BFF);
  static const Color lightPurple = Color(0xFFF5F1FF);
  static const Color textDark = Color(0xFF1F2340);

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController nameController = TextEditingController();
  final TextEditingController emailController = TextEditingController();
  final TextEditingController phoneController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();

  bool isLoading = false;
  bool obscurePassword = true;
  String selectedUserType = 'deaf';

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    phoneController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Future<void> register() async {
    final name = nameController.text.trim();
    final email = emailController.text.trim();
    final phone = phoneController.text.trim();
    final password = passwordController.text.trim();

    if (name.isEmpty || email.isEmpty || password.isEmpty) {
      showMessage('Please fill all required fields');
      return;
    }

    if (password.length < 8) {
      showMessage('Password must be at least 8 characters');
      return;
    }

    setState(() {
      isLoading = true;
    });

    try {
      await AuthService.register(
        name: name,
        email: email,
        phone: phone,
        password: password,
        userType: selectedUserType,
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
    const Color purple = RegisterScreen.purple;
    const Color lightPurple = RegisterScreen.lightPurple;
    const Color textDark = RegisterScreen.textDark;

    return Scaffold(
      backgroundColor: lightPurple,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const SizedBox(height: 30),

              Align(
                alignment: Alignment.centerLeft,
                child: IconButton(
                  onPressed: () {
                    Navigator.pop(context);
                  },
                  icon: const Icon(
                    Icons.arrow_back_ios_new,
                    color: purple,
                  ),
                ),
              ),

              const SizedBox(height: 8),

              Container(
                height: 105,
                width: 105,
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
                  Icons.person_add_alt_1,
                  size: 58,
                  color: purple,
                ),
              ),

              const SizedBox(height: 20),

              const Text(
                "Create Account",
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: textDark,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                "Join Hear & Help and start safely",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.black54,
                ),
              ),

              const SizedBox(height: 30),

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
                      "Full Name",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: textDark,
                      ),
                    ),

                    const SizedBox(height: 10),

                    TextField(
                      controller: nameController,
                      decoration: InputDecoration(
                        hintText: "Enter your full name",
                        prefixIcon: const Icon(Icons.person_outline),
                        filled: true,
                        fillColor: lightPurple,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),

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

                    const SizedBox(height: 20),

                    const Text(
                      "Phone",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: textDark,
                      ),
                    ),

                    const SizedBox(height: 10),

                    TextField(
                      controller: phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: InputDecoration(
                        hintText: "Enter your phone number",
                        prefixIcon: const Icon(Icons.phone_outlined),
                        filled: true,
                        fillColor: lightPurple,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),

                    const Text(
                      "Account Type",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: textDark,
                      ),
                    ),

                    const SizedBox(height: 10),

                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: lightPurple,
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: selectedUserType,
                          isExpanded: true,
                          items: const [
                            DropdownMenuItem(
                              value: 'deaf',
                              child: Text('Deaf User'),
                            ),
                            DropdownMenuItem(
                              value: 'family',
                              child: Text('Family Member'),
                            ),
                            DropdownMenuItem(
                              value: 'rescuer',
                              child: Text('Rescuer'),
                            ),
                          ],
                          onChanged: (value) {
                            if (value == null) return;
                            setState(() {
                              selectedUserType = value;
                            });
                          },
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),

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
                        hintText: "At least 8 characters",
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

                    const SizedBox(height: 28),

                    SizedBox(
                      width: double.infinity,
                      height: 58,
                      child: ElevatedButton.icon(
                        onPressed: isLoading ? null : register,
                        icon: isLoading
                            ? const SizedBox(
                                height: 22,
                                width: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.person_add_alt_1),
                        label: Text(
                          isLoading ? "Creating account..." : "Create Account",
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

                    const SizedBox(height: 18),

                    const Center(
                      child: Text(
                        "Your information is protected",
                        style: TextStyle(
                          color: Colors.black45,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text("Already have an account? "),
                  GestureDetector(
                    onTap: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const LoginScreen(),
                        ),
                      );
                    },
                    child: const Text(
                      "Login",
                      style: TextStyle(
                        color: purple,
                        fontWeight: FontWeight.bold,
                      ),
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
