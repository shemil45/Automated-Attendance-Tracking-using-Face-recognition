"""
FastAPI Main Application
Faculty-facing attendance portal backend
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta
from typing import List
import pandas as pd
import io

from . import models, schemas, auth
from .database import get_db, init_db
from .face_recognition_service import face_recognition_service

# Create FastAPI app
app = FastAPI(title="Attendance Portal API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("✓ Database initialized")


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Faculty login endpoint"""
    class_obj = auth.authenticate_class(db, request.username, request.password)
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": class_obj.class_name})
    
    return schemas.TokenResponse(
        access_token=access_token,
        class_name=class_obj.class_name
    )


# ==================== Timetable Endpoints ====================

@app.get("/api/timetable/today", response_model=schemas.TodayTimetable)
def get_today_timetable(
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Get today's timetable with session status"""
    today = date.today()
    day_name = today.strftime("%a").upper()[:3]  # MON, TUE, etc.
    
    # Get timetable for today
    timetable_entries = db.query(models.Timetable).filter(
        models.Timetable.class_name == current_class.class_name,
        models.Timetable.day == day_name
    ).order_by(models.Timetable.period).all()
    
    # Get existing sessions for today
    sessions = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.class_name == current_class.class_name,
        models.AttendanceSession.date == today
    ).all()
    
    # Create session lookup by period
    session_by_period = {s.period: s for s in sessions}
    
    # Build response
    periods = []
    for entry in timetable_entries:
        # Skip breaks and free periods for display purposes
        if entry.is_break or not entry.subject_code:
            continue
        
        # Check if session exists
        session = session_by_period.get(entry.period)
        
        # Create period data dict with time strings
        period_dict = {
            'id': entry.id,
            'day': entry.day,
            'period': entry.period,
            'subject_code': entry.subject_code,
            'subject_name': entry.subject_name,
            'start_time': entry.start_time.strftime("%H:%M"),
            'end_time': entry.end_time.strftime("%H:%M"),
            'is_break': entry.is_break,
            'status': session.status if session else schemas.SessionStatusEnum.NOT_STARTED,
            'session_id': session.id if session else None
        }
        
        period_data = schemas.TimetableEntry(**period_dict)
        periods.append(period_data)
    
    return schemas.TodayTimetable(
        date=today.isoformat(),
        day=day_name,
        periods=periods
    )


# ==================== Attendance Session Endpoints ====================

@app.post("/api/attendance/start-session", response_model=schemas.SessionResponse)
def start_attendance_session(
    request: schemas.StartSessionRequest,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Start an attendance session for a specific period"""
    # Get timetable entry
    day_name = request.date.strftime("%a").upper()[:3]
    
    timetable_entry = db.query(models.Timetable).filter(
        models.Timetable.class_name == current_class.class_name,
        models.Timetable.day == day_name,
        models.Timetable.period == request.period
    ).first()
    
    if not timetable_entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    
    if timetable_entry.is_break or not timetable_entry.subject_code:
        raise HTTPException(status_code=400, detail="Cannot start session for break/free period")
    
    # Check if session already exists
    existing_session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.class_name == current_class.class_name,
        models.AttendanceSession.date == request.date,
        models.AttendanceSession.period == request.period
    ).first()
    
    if existing_session:
        # If already exists, just update status to ongoing
        if existing_session.status == models.SessionStatusEnum.NOT_STARTED:
            existing_session.status = models.SessionStatusEnum.ONGOING
            existing_session.started_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_session)
        
        # Start face recognition
        def on_face_recognized(name: str):
            # Find student by name
            student = db.query(models.Student).filter(
                models.Student.name == name,
                models.Student.class_name == current_class.class_name
            ).first()
            
            if student:
                # Check if already marked
                existing_record = db.query(models.AttendanceRecord).filter(
                    models.AttendanceRecord.session_id == existing_session.id,
                    models.AttendanceRecord.reg_no == student.reg_no
                ).first()
                
                if not existing_record:
                    # Mark attendance
                    record = models.AttendanceRecord(
                        session_id=existing_session.id,
                        reg_no=student.reg_no,
                        status=models.AttendanceStatusEnum.PRESENT,
                        marked_by=models.MarkedByEnum.SYSTEM,
                        marked_at=datetime.utcnow()
                    )
                    db.add(record)
                    db.commit()
        # Convert to response schema with proper serialization
        return schemas.SessionResponse(
            id=existing_session.id,
            class_name=existing_session.class_name,
            date=existing_session.date.isoformat(),
            day=existing_session.day,
            period=existing_session.period,
            subject_code=existing_session.subject_code,
            subject_name=existing_session.subject_name,
            start_time=existing_session.start_time.strftime("%H:%M"),
            end_time=existing_session.end_time.strftime("%H:%M"),
            status=existing_session.status,
            started_at=existing_session.started_at,
            ended_at=existing_session.ended_at
        )
    
    # Create new session
    session = models.AttendanceSession(
        class_name=current_class.class_name,
        date=request.date,
        day=day_name,
        period=request.period,
        subject_code=timetable_entry.subject_code,
        subject_name=timetable_entry.subject_name,
        start_time=timetable_entry.start_time,
        end_time=timetable_entry.end_time,
        status=models.SessionStatusEnum.ONGOING,
        started_at=datetime.utcnow()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Start face recognition
    def on_face_recognized(name: str):
        # Find student by name
        student = db.query(models.Student).filter(
            models.Student.name == name,
            models.Student.class_name == current_class.class_name
        ).first()
        
        if student:
            # Check if already marked
            existing_record = db.query(models.AttendanceRecord).filter(
                models.AttendanceRecord.session_id == session.id,
                models.AttendanceRecord.reg_no == student.reg_no
            ).first()
            
            if not existing_record:
                # Mark attendance
                record = models.AttendanceRecord(
                    session_id=session.id,
                    reg_no=student.reg_no,
                    status=models.AttendanceStatusEnum.PRESENT,
                    marked_by=models.MarkedByEnum.SYSTEM,
                    marked_at=datetime.utcnow()
                )
                db.add(record)
                db.commit()
    
    # Convert to response schema with proper serialization
    return schemas.SessionResponse(
        id=session.id,
        class_name=session.class_name,
        date=session.date.isoformat(),
        day=session.day,
        period=session.period,
        subject_code=session.subject_code,
        subject_name=session.subject_name,
        start_time=session.start_time.strftime("%H:%M"),
        end_time=session.end_time.strftime("%H:%M"),
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at
    )


@app.get("/api/attendance/session/{session_id}", response_model=schemas.SessionResponse)
def get_session(
    session_id: int,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Get session details"""
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return schemas.SessionResponse(
        id=session.id,
        class_name=session.class_name,
        date=session.date.isoformat(),
        day=session.day,
        period=session.period,
        subject_code=session.subject_code,
        subject_name=session.subject_name,
        start_time=session.start_time.strftime("%H:%M"),
        end_time=session.end_time.strftime("%H:%M"),
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at
    )


@app.post("/api/attendance/session/{session_id}/recognize")
async def recognize_faces(
    session_id: int,
    file: UploadFile = File(...),
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Process a video frame for face recognition"""
    # Verify session ownership
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session or session.status != models.SessionStatusEnum.ONGOING:
        return {"processed": False, "message": "Session not active"}
    
    # Callback to handle recognition
    def on_face_recognized(name: str):
        # Find student
        student = db.query(models.Student).filter(
            models.Student.name == name
        ).first()
        if not student:
            return
            
        # Check if already present
        existing_record = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.session_id == session_id,
            models.AttendanceRecord.reg_no == student.reg_no
        ).first()
        
        if existing_record:
            if existing_record.status == models.AttendanceStatusEnum.ABSENT:
                existing_record.status = models.AttendanceStatusEnum.PRESENT
                existing_record.marked_by = models.MarkedByEnum.SYSTEM
                existing_record.marked_at = datetime.utcnow()
                db.commit()
        else:
            # Create new record
            record = models.AttendanceRecord(
                session_id=session_id,
                reg_no=student.reg_no,
                status=models.AttendanceStatusEnum.PRESENT,
                marked_by=models.MarkedByEnum.SYSTEM,
                marked_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()

    # Read image content
    contents = await file.read()
    
    # Process the frame
    try:
        recognized_names = face_recognition_service.process_frame(
            session_id, 
            contents, 
            on_face_recognized
        )
        return {"processed": True, "recognized": recognized_names}
    except Exception as e:
        print(f"Error processing frame: {e}")
        return {"processed": False, "error": str(e)}


@app.post("/api/attendance/end-session/{session_id}", response_model=schemas.SessionResponse)
def end_session(
    session_id: int,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """End an attendance session"""
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session status
    session.status = models.SessionStatusEnum.COMPLETED
    session.ended_at = datetime.utcnow()
    
    # Mark all students not present as absent
    all_students = db.query(models.Student).filter(
        models.Student.class_name == current_class.class_name
    ).all()
    
    marked_reg_nos = {r.reg_no for r in session.attendance_records}
    
    for student in all_students:
        if student.reg_no not in marked_reg_nos:
            record = models.AttendanceRecord(
                session_id=session.id,
                reg_no=student.reg_no,
                status=models.AttendanceStatusEnum.ABSENT,
                marked_by=models.MarkedByEnum.SYSTEM,
                marked_at=datetime.utcnow()
            )
            db.add(record)
    
    db.commit()
    db.refresh(session)
    
    return schemas.SessionResponse(
        id=session.id,
        class_name=session.class_name,
        date=session.date.isoformat(),
        day=session.day,
        period=session.period,
        subject_code=session.subject_code,
        subject_name=session.subject_name,
        start_time=session.start_time.strftime("%H:%M"),
        end_time=session.end_time.strftime("%H:%M"),
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at
    )


@app.get("/api/attendance/session/{session_id}/students", response_model=List[schemas.AttendanceRecordResponse])
def get_session_students(
    session_id: int,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Get all students and their attendance status for a session"""
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all attendance records
    records = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session_id
    ).all()
    
    # Build response
    result = []
    for record in records:
        student = db.query(models.Student).filter(
            models.Student.reg_no == record.reg_no
        ).first()
        
        if student:
            result.append(schemas.AttendanceRecordResponse(
                reg_no=record.reg_no,
                name=student.name,
                status=record.status,
                marked_by=record.marked_by,
                marked_at=record.marked_at
            ))
    
    return result


@app.post("/api/attendance/manual-override")
def manual_override(
    request: schemas.ManualOverrideRequest,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Manually override attendance status"""
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == request.session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if record exists
    record = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == request.session_id,
        models.AttendanceRecord.reg_no == request.reg_no
    ).first()
    
    if record:
        # Update existing record
        record.status = request.status
        record.marked_by = models.MarkedByEnum.FACULTY
        record.marked_at = datetime.utcnow()
    else:
        # Create new record
        record = models.AttendanceRecord(
            session_id=request.session_id,
            reg_no=request.reg_no,
            status=request.status,
            marked_by=models.MarkedByEnum.FACULTY,
            marked_at=datetime.utcnow()
        )
        db.add(record)
    
    db.commit()
    
    return {"message": "Attendance updated successfully"}


# ==================== Reports Endpoints ====================

@app.get("/api/reports/sessions", response_model=List[schemas.SessionResponse])
def get_sessions_by_date(
    date: date,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Get all sessions for a specific date"""
    sessions = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.class_name == current_class.class_name,
        models.AttendanceSession.date == date
    ).order_by(models.AttendanceSession.period).all()
    
    return sessions


@app.get("/api/reports/session/{session_id}/report", response_model=schemas.SessionReport)
def get_session_report(
    session_id: int,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Get detailed attendance report for a session"""
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all students in class
    all_students = db.query(models.Student).filter(
        models.Student.class_name == current_class.class_name
    ).all()
    
    # Get attendance records
    records = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session_id
    ).all()
    
    # Build attendance list
    attendance_list = []
    present_count = 0
    absent_count = 0
    od_count = 0
    
    for student in all_students:
        # Find record for this student
        record = next((r for r in records if r.reg_no == student.reg_no), None)
        
        if record:
            attendance_list.append(schemas.AttendanceRecordResponse(
                reg_no=student.reg_no,
                name=student.name,
                status=record.status,
                marked_by=record.marked_by,
                marked_at=record.marked_at
            ))
            
            if record.status == models.AttendanceStatusEnum.PRESENT:
                present_count += 1
            elif record.status == models.AttendanceStatusEnum.ABSENT:
                absent_count += 1
            elif record.status == models.AttendanceStatusEnum.OD:
                od_count += 1
        else:
            # No record means not yet marked (for ongoing sessions)
            attendance_list.append(schemas.AttendanceRecordResponse(
                reg_no=student.reg_no,
                name=student.name,
                status=models.AttendanceStatusEnum.ABSENT,
                marked_by=models.MarkedByEnum.SYSTEM,
                marked_at=datetime.utcnow()
            ))
            absent_count += 1
    
    try:
        # Convert session to Pydantic model explicitly
        session_data = schemas.SessionResponse.model_validate(session)
        
        return schemas.SessionReport(
            session=session_data,
            attendance=attendance_list,
            total_students=len(all_students),
            present_count=present_count,
            absent_count=absent_count,
            od_count=od_count
        )
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.get("/api/reports/session/{session_id}/export")
def export_session_report(
    session_id: int,
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Download attendance report as Excel file"""
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.id == session_id,
        models.AttendanceSession.class_name == current_class.class_name
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get attendance data
    all_students = db.query(models.Student).filter(
        models.Student.class_name == current_class.class_name
    ).all()
    
    records = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session_id
    ).all()
    
    record_dict = {r.reg_no: r for r in records}
    
    # Build data for Excel
    data = []
    for student in all_students:
        record = record_dict.get(student.reg_no)
        if record:
            data.append({
                'Reg No': student.reg_no,
                'Name': student.name,
                'Status': record.status.value.upper(),
                'Marked By': record.marked_by.value.upper(),
                'Marked At': record.marked_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            data.append({
                'Reg No': student.reg_no,
                'Name': student.name,
                'Status': 'ABSENT',
                'Marked By': 'SYSTEM',
                'Marked At': ''
            })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Generate Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
    output.seek(0)
    
    # Generate filename
    filename = f"{session.class_name}_{session.date}_{session.period}_{session.subject_code}.xlsx"
    filename = filename.replace('/', '-')  # Remove any slashes
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== Utility Endpoints ====================

@app.post("/api/reload-encodings")
def reload_encodings(current_class: models.Class = Depends(auth.get_current_class)):
    """Reload face encodings (for when new students are added)"""
    success = face_recognition_service.reload_encodings()
    
    if success:
        return {"message": "Encodings reloaded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload encodings")


@app.post("/api/students/sync")
def sync_students(
    current_class: models.Class = Depends(auth.get_current_class),
    db: Session = Depends(get_db)
):
    """Sync students from CSV to Database and reload encodings"""
    import csv
    from pathlib import Path
    
    # Path to students.csv
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "data" / "students.csv"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="students.csv not found")
    
    try:
        updated_count = 0
        added_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reg_no = row['RegNo']
                name = row['Name']
                class_name = row['Class']
                email = row.get('Email', '')
                
                # Check if student exists
                student = db.query(models.Student).filter(
                    models.Student.reg_no == reg_no
                ).first()
                
                if student:
                    # Update existing
                    student.name = name
                    student.class_name = class_name
                    student.email = email
                    updated_count += 1
                else:
                    # Create new
                    student = models.Student(
                        reg_no=reg_no,
                        name=name,
                        class_name=class_name,
                        email=email,
                        created_at=datetime.utcnow()
                    )
                    db.add(student)
                    added_count += 1
        
        db.commit()
        
        # Reload encodings
        face_recognition_service.reload_encodings()
        
        return {
            "message": "Sync successful",
            "added": added_count,
            "updated": updated_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
