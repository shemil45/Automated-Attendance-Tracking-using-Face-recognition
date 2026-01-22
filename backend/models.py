"""
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Enum, ForeignKey, LargeBinary
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


class SessionStatusEnum(str, enum.Enum):
    NOT_STARTED = "not_started"
    ONGOING = "ongoing"
    COMPLETED = "completed"


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

    # Composite unique constraint
    __table_args__ = (
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
