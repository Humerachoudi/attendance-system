from fastapi import FastAPI, HTTPException, Request, Form, Cookie, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, date, timedelta
from backend.database import get_connection
from backend.qr_generate import generate_qr
from passlib.hash import bcrypt
import os, base64, traceback, io, csv, hashlib, sqlite3
from pydantic import BaseModel


app = FastAPI()

# ---------------- Static & Templates ---------------- #
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
templates = Jinja2Templates(directory="backend/templates")

@app.get("/ping")
def ping():
    return {"status": "ok"}

# ---------------- Memory variable ---------------- #
ACTIVE_SUBJECT = {}

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_current_user(session_id):
    """Retrieve current user by cookie"""
    if not session_id:
        return None
    conn = get_connection()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (session_id,))
    user = cur.fetchone()
    conn.close()
    return user


# ---------------------- AUTO TABLE CREATION ---------------------- #
conn = get_connection()
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_number TEXT UNIQUE,
    password TEXT,
    role TEXT,
    name TEXT
)
""")
conn.commit()
conn.close()


# ---------------- LOGIN ----------#
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "",
        "reg_number": "",
        "password": "",
        "role": ""
    })


@app.post("/login")
def login(
    request: Request,
    reg_number: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    try:
        import hashlib  # ✅ Import inside to avoid errors if missing

        conn = get_connection()
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE reg_number=? AND role=?", (reg_number, role))
        user = cur.fetchone()
        conn.close()

        if not user:
            # ❌ No such user
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "❌ Invalid credentials! Please try again.",
                "reg_number": "",
                "password": "",
                "role": ""
            })

        db_password = user["password"]

        # ✅ Always hash the entered password (same for teacher & student)
        hashed_input = hashlib.sha256(password.strip().encode("utf-8")).hexdigest()
        valid = hashed_input == db_password

        if valid:
            # ✅ Redirect based on role
            redirect_url = "/teacher_panel" if user["role"] == "teacher" else "/student_panel"
            response = RedirectResponse(url=redirect_url, status_code=303)
            response.set_cookie(key="session_id", value=str(user["id"]))
            return response

        # ❌ Wrong password
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "❌ Invalid password!",
            "reg_number": "",
            "password": "",
            "role": ""
        })

    except Exception as e:
        print("⚠️ LOGIN ERROR:", e)
        traceback.print_exc()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"⚠️ Server error: {e}",
            "reg_number": "",
            "password": "",
            "role": ""
        })

# ---------------------- TEACHER REGISTRATION PAGE (GET) ---------------------- #
@app.get("/register_teacher", response_class=HTMLResponse)
def register_teacher_page(request: Request):
    return templates.TemplateResponse("register_teacher.html", {"request": request, "error": ""})


# ---------------------- TEACHER REGISTRATION (POST) ---------------------- #
@app.post("/register_teacher", response_class=HTMLResponse)
def register_teacher(
    request: Request,
    teacher_id: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    try:
        if password != confirm_password:
            return templates.TemplateResponse(
                "register_teacher.html",
                {"request": request, "error": "❌ Passwords do not match!"}
            )

        conn = get_connection()
        cur = conn.cursor()

        # Check if teacher already exists
        cur.execute("SELECT * FROM users WHERE reg_number=?", (teacher_id,))
        if cur.fetchone():
            conn.close()
            return templates.TemplateResponse(
                "register_teacher.html",
                {"request": request, "error": "⚠️ Teacher already registered!"}
            )

        # ✅ Hash password using SHA-256
        hashed_pw = hashlib.sha256(password.encode("utf-8")).hexdigest()

        # ✅ Save teacher into DB
        cur.execute("""
            INSERT INTO users (reg_number, name, password, role)
            VALUES (?, ?, ?, 'teacher')
        """, (teacher_id, name, hashed_pw))
        conn.commit()
        conn.close()

        return templates.TemplateResponse(
            "register_teacher.html",
            {"request": request, "error": f"✅ Registration successful!<br>Your ID: <b>{teacher_id}</b>"}
        )

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()
        return templates.TemplateResponse(
            "register_teacher.html",
            {"request": request, "error": f"⚠️ Server Error: {e}"}
        )


# ---------------------- URL REDIRECT FIX ---------------------- #
@app.get("/teacher_register", response_class=HTMLResponse)
def teacher_register_redirect():
    return RedirectResponse(url="/register_teacher", status_code=307)


# ---------------------- STUDENT REGISTRATION PAGE (GET) ---------------------- #
@app.get("/student_register", response_class=HTMLResponse)
def student_register_page(request: Request):
    return templates.TemplateResponse("student_register.html", {"request": request, "error": ""})

# ---------------------- STUDENT REGISTRATION ---------------------- #
@app.post("/register_student")
def register_student(
    request: Request,
    reg_number: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    try:
        if password != confirm_password:
            return templates.TemplateResponse(
                "student_register.html",
                {"request": request, "error": "❌ Passwords do not match!"},
            )

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE reg_number=?", (reg_number,))
        if cur.fetchone():
            conn.close()
            return templates.TemplateResponse(
                "student_register.html",
                {"request": request, "error": "⚠️ Reg number already registered!"},
            )

        cur.execute(
            "INSERT INTO users (reg_number, name, password, role) VALUES (?, ?, ?, 'student')",
            (reg_number, name, password),
        )
        conn.commit()
        conn.close()

        return templates.TemplateResponse(
            "student_register.html",
            {
                "request": request,
                "error": f"✅ Registration successful!<br>Your Reg No: <b>{reg_number}</b><br>Password: <b>{password}</b>"
            },
        )
    except Exception as e:
        traceback.print_exc()
        return templates.TemplateResponse(
            "student_register.html",
            {"request": request, "error": f"⚠️ Server error: {e}"},
        )


# ---------------- QR GENERATION ---------------- #
@app.get("/api/generate_qr")
def api_generate_qr(session_id: str = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "teacher":
        return {"success": False, "message": "Unauthorized"}

    try:
        qr_path, qr_text = generate_qr(user["id"])
        with open(qr_path, "rb") as f:
            qr_base64 = base64.b64encode(f.read()).decode("utf-8")

        return {
            "success": True,
            "qr_text": qr_text,
            "qr_base64": qr_base64,
            "date": str(date.today())
        }

    except Exception as e:
        return {"success": False, "message": str(e)}


# ---------------- ACTIVATE SUBJECT (10 MIN) ---------------- #
@app.post("/api/activate_subject/{subject}")
def activate_subject(subject: str, session_id: str = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "teacher":
        return {"success": False, "message": "Unauthorized"}

    expires = datetime.now() + timedelta(minutes=10)
    ACTIVE_SUBJECT[str(user["id"])] = {"subject": subject, "expires": expires}

    print(f"✅ '{subject}' activated by Teacher {user['id']} until {expires}")
    return {"success": True, "message": f"✅ '{subject}' activated for 10 minutes."}


# ---------------- STOP ATTENDANCE ---------------- #
@app.post("/api/stop_attendance")
def stop_attendance(session_id: str = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "teacher":
        return {"success": False, "message": "Unauthorized"}

    tid = str(user["id"])
    if tid in ACTIVE_SUBJECT:
        del ACTIVE_SUBJECT[tid]
        return {"success": True, "message": "🛑 Attendance stopped manually."}
    return {"success": False, "message": "No active attendance found."}


# ---------------- GET ACTIVE SUBJECTS (FOR STUDENTS) ---------------- #
@app.get("/api/active_attendance")
def get_active_attendance():
    now = datetime.now()
    expired = [tid for tid, info in ACTIVE_SUBJECT.items() if now > info["expires"]]
    for tid in expired:
        del ACTIVE_SUBJECT[tid]

    active_list = [
        {"teacher_id": tid, "subject": info["subject"]}
        for tid, info in ACTIVE_SUBJECT.items()
    ]

    if not active_list:
        return {"success": True, "active_subjects": []}
    return {"success": True, "active_subjects": active_list}


# ---------------- SCAN QR (STUDENT) ---------------- #
@app.post("/api/scan_qr/{student_id}")
def scan_qr(
    student_id: int,
    qr_text: str = Form(...),
    subject: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None)
):
    try:
        parts = qr_text.strip().split("-")
        if len(parts) != 2 or parts[0] != "TEACHER":
            return {"success": False, "message": "❌ Invalid QR code format"}

        teacher_id = str(int(parts[1]))
        today = str(date.today())

        now = datetime.now()
        for tid in list(ACTIVE_SUBJECT.keys()):
            if now > ACTIVE_SUBJECT[tid]["expires"]:
                del ACTIVE_SUBJECT[tid]

        active = ACTIVE_SUBJECT.get(teacher_id)
        if not active:
            return {"success": False, "message": "❌ No active subject right now."}

        if now > active["expires"]:
            del ACTIVE_SUBJECT[teacher_id]
            return {"success": False, "message": "⏰ Attendance window closed (10 minutes passed)."}

        active_subject = active["subject"]

        if subject != active_subject:
            return {"success": False, "message": f"❌ Attendance active for '{active_subject}', not '{subject}'."}

        conn = get_connection()
        conn.row_factory = dict_factory
        cur = conn.cursor()

        cur.execute("SELECT name FROM users WHERE id=? AND role='student'", (student_id,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return {"success": False, "message": "❌ Student not found"}

        student_name = student["name"]

        cur.execute("""
            SELECT 1 FROM attendance
            WHERE student_id=? AND date=? AND teacher_id=? AND subject=?
        """, (student_id, today, teacher_id, active_subject))
        if cur.fetchone():
            conn.close()
            return {"success": True, "message": f"✅ Already marked present for {active_subject}."}

        cur.execute("""
            INSERT INTO attendance (
                student_id, teacher_id, subject, date, time, status, qr_text, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            teacher_id,
            active_subject,
            today,
            datetime.now().strftime("%H:%M:%S"),
            "Present",
            qr_text,
            latitude,
            longitude
        ))
        conn.commit()
        conn.close()

        return {"success": True, "message": f"✅ Attendance marked for {active_subject} ({student_name})."}

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": f"⚠️ Server error: {e}"}


# ---------------- ATTENDANCE RECORDS ---------------- #
@app.get("/api/attendance/{subject}")
def get_attendance(subject: str, session_id: str = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "teacher":
        return {"success": False, "message": "Unauthorized"}

    conn = get_connection()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            u.reg_number, 
            u.name, 
            a.date, 
            a.time, 
            a.status,
            a.latitude,
            a.longitude
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        WHERE a.teacher_id=? AND a.subject=?
        ORDER BY a.date DESC, a.time DESC
    """, (user["id"], subject))

    rows = cur.fetchall()
    conn.close()

    # Build proper Google Maps link in Python
    for row in rows:
        lat = row.get("latitude")
        lng = row.get("longitude")
        if lat and lng:
            row["map_link"] = f"https://www.google.com/maps?q={lat},{lng}"
        else:
            row["map_link"] = None

        # Remove raw lat/lng from response
        row.pop("latitude", None)
        row.pop("longitude", None)

    return {"success": True, "records": rows}

# ---------------- DOWNLOAD ATTENDANCE CSV ---------------- #
@app.get("/api/download_csv/{subject}")
def download_csv(subject: str, session_id: str = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "teacher":
        return {"success": False, "message": "Unauthorized"}

    conn = get_connection()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("""
        SELECT u.reg_number, u.name, a.date, a.time, a.status, a.latitude, a.longitude
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        WHERE a.teacher_id=? AND a.subject=?
        ORDER BY a.date DESC, a.time DESC
    """, (user["id"], subject))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"success": False, "message": "No attendance records found for this subject."}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Reg No", "Name", "Date", "Time", "Status", "Latitude", "Longitude"])
    for row in rows:
        writer.writerow([
            row.get("reg_number",""),
            row.get("name",""),
            row.get("date",""),
            row.get("time",""),
            row.get("status",""),
            row.get("latitude",""),
            row.get("longitude","")
        ])

    output.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename=attendance_{subject.replace(' ', '_')}.csv"
    }
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

# ---------------- PREVIOUS ATTENDANCE (FULL DETAIL) ---------------- #
@app.get("/api/previous_attendance")
def previous_attendance(session_id: str = Cookie(None)):
    """Fetch all past attendance records for the logged-in teacher (student-level)."""
    user = get_current_user(session_id)
    if not user or user["role"] != "teacher":
        return {"success": False, "message": "Unauthorized"}

    conn = get_connection()
    conn.row_factory = dict_factory
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            u.reg_number, 
            u.name, 
            a.subject,
            a.date, 
            a.time, 
            a.status,
            CASE 
                WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL 
                THEN 'https://www.google.com/maps?q=' || a.latitude || ',' || a.longitude
                ELSE NULL 
            END AS map_link
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        WHERE a.teacher_id = ?
        ORDER BY a.date DESC, a.time DESC
    """, (user["id"],))

    rows = cur.fetchall()
    conn.close()
    return {"success": True, "records": rows}

# ---------------- CHECK DATABASE ---------------- #
@app.get("/check_db")
def check_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]

    result = {"tables": tables}
    if "users" in tables:
        cur.execute("SELECT COUNT(*) FROM users")
        result["users_count"] = cur.fetchone()[0]
    if "attendance" in tables:
        cur.execute("SELECT COUNT(*) FROM attendance")
        result["attendance_count"] = cur.fetchone()[0]

    conn.close()
    return result


# ---------------- STUDENT PANEL ---------------- #
@app.get("/student_panel", response_class=HTMLResponse)
def student_panel(request: Request, session_id: str = Cookie(None)):
    try:
        user = get_current_user(session_id)
        if not user or user["role"] != "student":
            return RedirectResponse(url="/")

        return templates.TemplateResponse("student_panel.html", {
            "request": request,
            "student_id": user["id"],
            "name": user["name"],
            "reg_number": user["reg_number"]
        })
    except Exception:
        return HTMLResponse(f"<h1>Server Error</h1><pre>{traceback.format_exc()}</pre>")
    
    # ---------------- TEACHER PANEL ---------------- #

# ---------------- TEACHER PANEL ---------------- #
@app.get("/teacher_panel", response_class=HTMLResponse)
def teacher_panel(request: Request, session_id: str = Cookie(None)):
    try:
        user = get_current_user(session_id)
        if not user or user["role"] != "teacher":
            return RedirectResponse(url="/", status_code=303)

        # ✅ Fetch subjects from DB and pass to template
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM subjects ORDER BY name ASC")
        subjects = [row["name"] for row in cur.fetchall()]
        conn.close()

        return templates.TemplateResponse("teacher_panel.html", {
            "request": request,
            "teacher_id": user["id"],
            "name": user["name"],
            "reg_number": user["reg_number"],
            "subjects": subjects
        })
    except Exception:
        return HTMLResponse(f"<h1>Server Error</h1><pre>{traceback.format_exc()}</pre>")
    
    
# ✅ Add this route anywhere after the teacher panel route
@app.get("/api/teacher_name")
def get_teacher_name(request: Request):
    user_id = request.cookies.get("session_id")
    if not user_id:
        return {"name": "Teacher"}
    conn = sqlite3.connect("backend/attendance.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id=? AND role='teacher'", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"name": row[0]}
    return {"name": "Teacher"}

# ---------------- Forgot Password System ----------#
@app.get("/login", response_class=HTMLResponse)
def login_redirect():
    """Redirect /login to main login page"""
    return RedirectResponse(url="/", status_code=303)


# ---------------- Forgot Password System ----------#

class ResetData(BaseModel):
    reg_number: str
    new_password: str

@app.get("/forgot-password", response_class=HTMLResponse)
def get_forgot_page(request: Request):
    """Serve the forgot password page"""
    return templates.TemplateResponse("forgot.html", {"request": request})

@app.post("/forgot-password")
def reset_password(data: ResetData):
    """Reset password using register number"""
    reg_number = data.reg_number.strip()
    new_password = data.new_password.strip()

    if not reg_number or not new_password:
        raise HTTPException(status_code=400, detail="All fields are required.")

    try:
        conn = get_connection()
        cur = conn.cursor()

        # ✅ Check if user exists
        cur.execute("SELECT * FROM users WHERE reg_number=?", (reg_number,))
        user = cur.fetchone()

        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ Always hash the password before storing
        hashed_pw = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
        cur.execute("UPDATE users SET password=? WHERE reg_number=?", (hashed_pw, reg_number))

        conn.commit()
        conn.close()

        return {"message": "Password reset successful!"}

    except Exception as e:
        print("⚠️ Error resetting password:", e)
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
