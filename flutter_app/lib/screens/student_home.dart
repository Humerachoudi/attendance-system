import 'package:flutter/material.dart';
import 'scan_screen.dart';

class StudentHome extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Student Home")),
      body: Center(
        child: ElevatedButton(
          child: Text("Scan QR Attendance"),
          onPressed: () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => ScanScreen()));
          },
        ),
      ),
    );
  }
}
