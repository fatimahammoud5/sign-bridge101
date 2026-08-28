import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_config.dart';
import 'token_storage.dart';

class AuthService {
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/login');

    final response = await http.post(
      url,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200 && data['status'] == true) {
      final token = data['token'];

      if (token == null || token.toString().isEmpty) {
        throw Exception('Token not found in response');
      }

      await TokenStorage.saveToken(token);

      return data;
    }

    String message = 'Login failed';

    if (data is Map<String, dynamic>) {
      if (data['message'] != null) {
        message = data['message'].toString();
      } else if (data['errors'] != null) {
        message = data['errors'].toString();
      }
    }

    throw Exception(message);
  }
//Register
   static Future<Map<String, dynamic>> register({
  required String name,
  required String email,
  required String phone,
  required String password,
  String userType = 'deaf',
}) async {
  final url = Uri.parse('${ApiConfig.baseUrl}/register');

  final response = await http.post(
    url,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'name': name,
      'email': email,
      'phone': phone,
      'password': password,
      'user_type': userType,
    }),
  );

  final data = jsonDecode(response.body);

  if ((response.statusCode == 200 || response.statusCode == 201) &&
      data['status'] == true) {
    final token = data['token'];

    if (token == null || token.toString().isEmpty) {
      throw Exception('Token not found in response');
    }

    await TokenStorage.saveToken(token);

    return data;
  }

  String message = 'Register failed';

  if (data is Map<String, dynamic>) {
    if (data['message'] != null) {
      message = data['message'].toString();
    } else if (data['errors'] != null) {
      final errors = data['errors'] as Map<String, dynamic>;
      message = errors.values.first[0].toString();
    }
  }

  throw Exception(message);
}


  static Future<Map<String, dynamic>> me() async {
    final token = await TokenStorage.getToken();

    if (token == null) {
      throw Exception('No token found');
    }

    final url = Uri.parse('${ApiConfig.baseUrl}/me');

    final response = await http.get(
      url,
      headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200 && data['status'] == true) {
      return data;
    }

    throw Exception(data['message'] ?? 'Failed to get user');
  }

  static Future<void> logout() async {
    final token = await TokenStorage.getToken();

    if (token != null) {
      final url = Uri.parse('${ApiConfig.baseUrl}/logout');

      await http.post(
        url,
        headers: {
          'Accept': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
    }

    await TokenStorage.clearToken();
  }
}