class Attendance {
  String name;
  String rollNo;
  String date;
  String time;
  String status;

  Attendance({required this.name, required this.rollNo, required this.date, required this.time, required this.status});

  factory Attendance.fromJson(Map<String, dynamic> json) {
    return Attendance(
      name: json['name'],
      rollNo: json['roll_no'],
      date: json['date'] ?? "-",
      time: json['time'] ?? "-",
      status: json['status'],
    );
  }
}
