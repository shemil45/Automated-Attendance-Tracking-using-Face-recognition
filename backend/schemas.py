"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum


# Enums
class DayEnum(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"


class SessionStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    ONGOING = "ongoing"
    COMPLETED = "completed"


class AttendanceStatusEnum(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    OD = "od"


class MarkedByEnum(str, Enum):
    SYSTEM = "system"
    FACULTY = "faculty"


# Authentication
class LoginRequest(BaseModel):
    username: str  # class name
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    class_name: str


# Timetable
class TimetableEntry(BaseModel):
    id: int
    day: DayEnum
    period: int
    subject_code: Optional[str]
    subject_name: Optional[str]
    start_time: str  # Changed from time to str
    end_time: str    # Changed from time to str
    is_break: bool
    status: Optional[SessionStatusEnum] = None  # For today view
    session_id: Optional[int] = None  # For today view

    class Config:
        from_attributes = True
        json_encoders = {
            time: lambda v: v.strftime("%H:%M") if v else None
        }

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle time objects"""
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
            # Convert time objects to strings
            if 'start_time' in data and hasattr(data['start_time'], 'strftime'):
                data['start_time'] = data['start_time'].strftime("%H:%M")
            if 'end_time' in data and hasattr(data['end_time'], 'strftime'):
                data['end_time'] = data['end_time'].strftime("%H:%M")
            return super().model_validate(data)
        return super().model_validate(obj)


class TodayTimetable(BaseModel):
    date: str  # Changed from date to str
    day: DayEnum
    periods: List[TimetableEntry]

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle date objects"""
        if isinstance(obj, dict):
            data = obj.copy()
            if 'date' in data and hasattr(data['date'], 'isoformat'):
                data['date'] = data['date'].isoformat()
            return super().model_validate(data)
        return super().model_validate(obj)


# Attendance Session
class StartSessionRequest(BaseModel):
    date: date
    period: int


class SessionResponse(BaseModel):
    id: int
    class_name: str
    date: str  # Changed from date to str
    day: DayEnum
    period: int
    subject_code: Optional[str]
    subject_name: Optional[str]
    start_time: str  # Changed from time to str
    end_time: str    # Changed from time to str
    status: SessionStatusEnum
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.strftime("%H:%M") if v else None
        }

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle date/time objects"""
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
            # Convert date to string
            if 'date' in data and hasattr(data['date'], 'isoformat'):
                data['date'] = data['date'].isoformat()
            # Convert time objects to strings
            if 'start_time' in data and hasattr(data['start_time'], 'strftime'):
                data['start_time'] = data['start_time'].strftime("%H:%M")
            if 'end_time' in data and hasattr(data['end_time'], 'strftime'):
                data['end_time'] = data['end_time'].strftime("%H:%M")
            return super().model_validate(data)
        return super().model_validate(obj)


# Attendance Record
class AttendanceRecordResponse(BaseModel):
    reg_no: str
    name: str
    status: AttendanceStatusEnum
    marked_by: MarkedByEnum
    marked_at: datetime

    class Config:
        from_attributes = True


class ManualOverrideRequest(BaseModel):
    session_id: int
    reg_no: str
    status: AttendanceStatusEnum


# Report
class SessionReport(BaseModel):
    session: SessionResponse
    attendance: List[AttendanceRecordResponse]
    total_students: int
    present_count: int
    absent_count: int
    od_count: int


# Student
class StudentResponse(BaseModel):
    reg_no: str
    name: str
    class_name: str
    email: Optional[str]

    class Config:
        from_attributes = True
