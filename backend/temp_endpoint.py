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
