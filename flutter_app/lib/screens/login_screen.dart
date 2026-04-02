import 'package:flutter/material.dart';
import 'student_home.dart';
import 'teacher_panel.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  String error = "";

  void login() async {
    String username = _usernameController.text;
    String password = _passwordController.text;
    String role = await ApiService.login(username, password);

    if (role == "student") {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => StudentHome()));
    } else if (role == "teacher") {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => TeacherPanel()));
    } else {
      setState(() { error = "Invalid credentials"; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Login")),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          children: [
            TextField(controller: _usernameController, decoration: InputDecoration(labelText: "Username")),
            TextField(controller: _passwordController, decoration: InputDecoration(labelText: "Password"), obscureText: true),
            SizedBox(height: 20),
            ElevatedButton(onPressed: login, child: Text("Login")),
            SizedBox(height: 10),
            Text(error, style: TextStyle(color: Colors.red)),
          ],
        ),
      ),
    );
  }
}
