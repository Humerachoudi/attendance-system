from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str
    role: str

class AttendanceRequest(BaseModel):
    student_id: int
