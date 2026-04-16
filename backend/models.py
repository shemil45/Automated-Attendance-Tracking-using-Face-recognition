"""
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Enum, ForeignKey, LargeBinary, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class DayEnum(str, enum.Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class SessionStatusEnum(str, enum.Enum):
    NOT_STARTED = "not_started"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    EXPIRED = "expired"   # Computed status — not stored in DB rows


class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    OD = "od"


class MarkedByEnum(str, enum.Enum):
    SYSTEM = "system"
    FACULTY = "faculty"


class Class(Base):
    """Faculty/Class table"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    students = relationship("Student", back_populates="class_")
    timetable = relationship("Timetable", back_populates="class_")
    sessions = relationship("AttendanceSession", back_populates="class_")


class AdminUser(Base):
    """Admin accounts for managing classes and timetables"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Student(Base):
    """Students table"""
    __tablename__ = "students"

    reg_no = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    class_name = Column(String, ForeignKey("classes.class_name"), nullable=False)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    class_ = relationship("Class", back_populates="students")
    attendance_records = relationship("AttendanceRecord", back_populates="student")


class Timetable(Base):
    """Timetable table"""
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, ForeignKey("classes.class_name"), nullable=False)
    day = Column(Enum(DayEnum), nullable=False)
    period = Column(Integer, nullable=False)
    subject_code = Column(String)  # Nullable for free periods
    subject_name = Column(String)  # Nullable for free periods
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_break = Column(Boolean, default=False)

    # Relationships
    class_ = relationship("Class", back_populates="timetable")

    __table_args__ = (
        UniqueConstraint("class_name", "day", "period", name="timetable_class_day_period_unique"),
        CheckConstraint("start_time < end_time", name="timetable_valid_time_range"),
        CheckConstraint(
            "is_break = false OR (subject_code IS NULL AND subject_name IS NULL)",
            name="timetable_break_has_no_subject",
        ),
        {'sqlite_autoincrement': True},
    )


class AttendanceSession(Base):
    """Attendance sessions table"""
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, ForeignKey("classes.class_name"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    day = Column(Enum(DayEnum), nullable=False)
    period = Column(Integer, nullable=False)
    subject_code = Column(String)
    subject_name = Column(String)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(Enum(SessionStatusEnum), default=SessionStatusEnum.NOT_STARTED)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)

    # Relationships
    class_ = relationship("Class", back_populates="sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

    # Composite unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class AttendanceRecord(Base):
    """Attendance records table"""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    reg_no = Column(String, ForeignKey("students.reg_no"), nullable=False)
    status = Column(Enum(AttendanceStatusEnum), default=AttendanceStatusEnum.PRESENT)
    marked_by = Column(Enum(MarkedByEnum), default=MarkedByEnum.SYSTEM)
    marked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("Student", back_populates="attendance_records")

    # Composite unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class FaceEncoding(Base):
    """Face encodings table"""
    __tablename__ = "face_encodings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    encoding = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
