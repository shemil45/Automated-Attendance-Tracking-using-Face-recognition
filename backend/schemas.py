"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, field_validator, model_validator
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
    SAT = "SAT"
    SUN = "SUN"


class SessionStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    EXPIRED = "expired"           # Computed only — never stored in DB
    BEFORE_START = "before_start" # Computed only — period hasn't begun yet


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


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class ClassCreate(BaseModel):
    class_name: str
    password: str

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Class name is required")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        return value


class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    password: Optional[str] = None

    @field_validator("class_name")
    @classmethod
    def validate_optional_class_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Class name cannot be empty")
        return value

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        return value


class ClassResponse(BaseModel):
    id: int
    class_name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class TimetableEntryRequest(BaseModel):
    day: DayEnum
    period: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    start_time: time
    end_time: time
    is_break: bool = False

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Period number must be at least 1")
        return value

    @field_validator("subject_code", "subject_name", mode="before")
    @classmethod
    def normalize_blank_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_timetable_entry(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        if self.is_break and (self.subject_code or self.subject_name):
            raise ValueError("Break periods must not contain subjects")
        return self


class TimetableEntryUpdate(BaseModel):
    day: Optional[DayEnum] = None
    period: Optional[int] = None
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_break: Optional[bool] = None

    @field_validator("period")
    @classmethod
    def validate_optional_period(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("Period number must be at least 1")
        return value


class AdminTimetableEntry(TimetableEntry):
    class_name: str


# Attendance Session
class StartSessionRequest(BaseModel):
    date: date
    period: int
    test_mode: bool = False  # When True, skip the 10-minute start-window check


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
    marked_at: Optional[datetime] = None

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
