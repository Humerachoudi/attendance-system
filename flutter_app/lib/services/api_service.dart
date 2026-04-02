import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/attendance.dart';

class ApiService {
  static const String baseUrl = "http://127.0.0.1:8000";

  static Future<String> login(String username, String password) async {
    final response = await http.post(
      Uri.parse("$baseUrl/login/"),
      body: {"username": username, "password": password},
    );

    if (response.statusCode == 303) {
      // Simplified: return role based on redirect
      return username.contains("teacher") ? "teacher" : "student";
    } else {
      return "error";
    }
  }

  static Future<String> markAttendance(String studentId) async {
    final response = await http.post(
      Uri.parse("$baseUrl/mark_attendance/"),
      body: {"student_id": studentId},
    );
    if (response.statusCode == 200) return "✅ Attendance marked!";
    return "❌ Error";
  }

  static Future<List<Attendance>> getAttendance() async {
    final response = await http.get(Uri.parse("$baseUrl/teacher_panel"));
    if (response.statusCode == 200) {
      // Fake parsing, in real app parse JSON
      return [];
    }
    return [];
  }
}
