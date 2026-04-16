"""
Admin portal routes for class and timetable management.
"""
import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth, models, schemas
from .database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


def seed_admin_user() -> None:
    """Create the bootstrap admin account from environment variables."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin@123")

    from .database import SessionLocal

    db = SessionLocal()
    try:
        existing = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
        if existing:
            return

        db.add(models.AdminUser(
            username=username,
            password_hash=auth.get_password_hash(password),
            created_at=datetime.utcnow(),
        ))
        db.commit()
    finally:
        db.close()


def _format_timetable_entry(entry: models.Timetable) -> schemas.AdminTimetableEntry:
    return schemas.AdminTimetableEntry(
        id=entry.id,
        class_name=entry.class_name,
        day=entry.day,
        period=entry.period,
        subject_code=entry.subject_code,
        subject_name=entry.subject_name,
        start_time=entry.start_time.strftime("%H:%M"),
        end_time=entry.end_time.strftime("%H:%M"),
        is_break=entry.is_break,
    )


def _ensure_class_exists(db: Session, class_name: str) -> models.Class:
    class_obj = db.query(models.Class).filter(models.Class.class_name == class_name).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_obj


def _validate_no_timetable_conflicts(
    db: Session,
    class_name: str,
    entry: schemas.TimetableEntryRequest,
    exclude_id: int | None = None,
) -> None:
    duplicate_query = db.query(models.Timetable).filter(
        models.Timetable.class_name == class_name,
        models.Timetable.day == entry.day,
        models.Timetable.period == entry.period,
    )
    if exclude_id is not None:
        duplicate_query = duplicate_query.filter(models.Timetable.id != exclude_id)
    if duplicate_query.first():
        raise HTTPException(
            status_code=400,
            detail="Duplicate period number for this class and day",
        )

    overlap_query = db.query(models.Timetable).filter(
        models.Timetable.class_name == class_name,
        models.Timetable.day == entry.day,
        models.Timetable.start_time < entry.end_time,
        models.Timetable.end_time > entry.start_time,
    )
    if exclude_id is not None:
        overlap_query = overlap_query.filter(models.Timetable.id != exclude_id)
    if overlap_query.first():
        raise HTTPException(status_code=400, detail="Overlapping time slot for this class and day")


def _validate_timetable_batch(entries: List[schemas.TimetableEntryRequest]) -> None:
    seen_periods = set()
    by_day: dict[str, list[schemas.TimetableEntryRequest]] = {}

    for entry in entries:
        period_key = (entry.day.value, entry.period)
        if period_key in seen_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate period {entry.period} on {entry.day.value}",
            )
        seen_periods.add(period_key)
        by_day.setdefault(entry.day.value, []).append(entry)

    for day, day_entries in by_day.items():
        sorted_entries = sorted(day_entries, key=lambda item: item.start_time)
        for previous, current in zip(sorted_entries, sorted_entries[1:]):
            if previous.end_time > current.start_time:
                raise HTTPException(status_code=400, detail=f"Overlapping time slots on {day}")


@router.post("/auth/login", response_model=schemas.AdminTokenResponse)
def admin_login(request: schemas.AdminLoginRequest, db: Session = Depends(get_db)):
    admin = auth.authenticate_admin(db, request.username, request.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password",
        )

    access_token = auth.create_access_token(data={"sub": admin.username, "role": "admin"})
    return schemas.AdminTokenResponse(access_token=access_token, username=admin.username)


@router.get("/classes", response_model=List[schemas.ClassResponse])
def list_classes(
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.Class).order_by(models.Class.class_name).all()


@router.post("/classes", response_model=schemas.ClassResponse, status_code=201)
def create_class(
    request: schemas.ClassCreate,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    class_obj = models.Class(
        class_name=request.class_name,
        password_hash=auth.get_password_hash(request.password),
        created_at=datetime.utcnow(),
    )
    db.add(class_obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Class name already exists")
    db.refresh(class_obj)
    return class_obj


@router.patch("/classes/{class_id}", response_model=schemas.ClassResponse)
def update_class(
    class_id: int,
    request: schemas.ClassUpdate,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    class_obj = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    if request.class_name and request.class_name != class_obj.class_name:
        has_dependencies = (
            db.query(models.Student).filter(models.Student.class_name == class_obj.class_name).first()
            or db.query(models.Timetable).filter(models.Timetable.class_name == class_obj.class_name).first()
            or db.query(models.AttendanceSession).filter(models.AttendanceSession.class_name == class_obj.class_name).first()
        )
        if has_dependencies:
            raise HTTPException(
                status_code=400,
                detail="Cannot rename a class that already has students, timetable entries, or sessions",
            )
        class_obj.class_name = request.class_name

    if request.password:
        class_obj.password_hash = auth.get_password_hash(request.password)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Class name already exists")
    db.refresh(class_obj)
    return class_obj


@router.delete("/classes/{class_id}", status_code=204)
def delete_class(
    class_id: int,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    class_obj = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    has_history = (
        db.query(models.Student).filter(models.Student.class_name == class_obj.class_name).first()
        or db.query(models.AttendanceSession).filter(models.AttendanceSession.class_name == class_obj.class_name).first()
    )
    if has_history:
        raise HTTPException(status_code=400, detail="Cannot delete a class with students or attendance history")

    db.query(models.Timetable).filter(models.Timetable.class_name == class_obj.class_name).delete()
    db.delete(class_obj)
    db.commit()
    return None


@router.get("/classes/{class_name}/timetable", response_model=List[schemas.AdminTimetableEntry])
def list_timetable(
    class_name: str,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_class_exists(db, class_name)
    entries = db.query(models.Timetable).filter(
        models.Timetable.class_name == class_name,
    ).order_by(models.Timetable.day, models.Timetable.period).all()
    return [_format_timetable_entry(entry) for entry in entries]


@router.put("/classes/{class_name}/timetable", response_model=List[schemas.AdminTimetableEntry])
def replace_timetable(
    class_name: str,
    entries: List[schemas.TimetableEntryRequest],
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_class_exists(db, class_name)
    _validate_timetable_batch(entries)

    db.query(models.Timetable).filter(models.Timetable.class_name == class_name).delete()
    for entry in entries:
        db.add(models.Timetable(class_name=class_name, **entry.model_dump()))
    db.commit()

    saved_entries = db.query(models.Timetable).filter(
        models.Timetable.class_name == class_name,
    ).order_by(models.Timetable.day, models.Timetable.period).all()
    return [_format_timetable_entry(entry) for entry in saved_entries]


@router.post("/classes/{class_name}/timetable", response_model=schemas.AdminTimetableEntry, status_code=201)
def create_timetable_entry(
    class_name: str,
    request: schemas.TimetableEntryRequest,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_class_exists(db, class_name)
    _validate_no_timetable_conflicts(db, class_name, request)

    entry = models.Timetable(class_name=class_name, **request.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _format_timetable_entry(entry)


@router.patch("/timetable/{entry_id}", response_model=schemas.AdminTimetableEntry)
def update_timetable_entry(
    entry_id: int,
    request: schemas.TimetableEntryUpdate,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    entry = db.query(models.Timetable).filter(models.Timetable.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    values = {
        "day": request.day if request.day is not None else entry.day,
        "period": request.period if request.period is not None else entry.period,
        "subject_code": request.subject_code if request.subject_code is not None else entry.subject_code,
        "subject_name": request.subject_name if request.subject_name is not None else entry.subject_name,
        "start_time": request.start_time if request.start_time is not None else entry.start_time,
        "end_time": request.end_time if request.end_time is not None else entry.end_time,
        "is_break": request.is_break if request.is_break is not None else entry.is_break,
    }
    merged = schemas.TimetableEntryRequest(**values)
    _validate_no_timetable_conflicts(db, entry.class_name, merged, exclude_id=entry.id)

    for key, value in merged.model_dump().items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return _format_timetable_entry(entry)


@router.delete("/timetable/{entry_id}", status_code=204)
def delete_timetable_entry(
    entry_id: int,
    _: models.AdminUser = Depends(auth.get_current_admin),
    db: Session = Depends(get_db),
):
    entry = db.query(models.Timetable).filter(models.Timetable.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    db.delete(entry)
    db.commit()
    return None
