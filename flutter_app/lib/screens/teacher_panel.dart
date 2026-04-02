import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/attendance.dart';

class TeacherPanel extends StatefulWidget {
  @override
  _TeacherPanelState createState() => _TeacherPanelState();
}

class _TeacherPanelState extends State<TeacherPanel> {
  List<Attendance> records = [];

  @override
  void initState() {
    super.initState();
    loadAttendance();
  }

  void loadAttendance() async {
    List<Attendance> list = await ApiService.getAttendance();
    setState(() { records = list; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Teacher Panel")),
      body: ListView.builder(
        itemCount: records.length,
        itemBuilder: (context, index) {
          Attendance a = records[index];
          return ListTile(
            title: Text(a.name),
            subtitle: Text("Roll: ${a.rollNo} | Status: ${a.status} | ${a.date} ${a.time}"),
          );
        },
      ),
    );
  }
}
