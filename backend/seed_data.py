"""
Database Seeding Script
Populates database with initial data for AIML-A class
"""
import sys
from pathlib import Path
from datetime import time, date
import csv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import SessionLocal, init_db
from backend.models import Class, Student, Timetable, DayEnum
from backend.auth import get_password_hash


def seed_database():
    """Seed database with initial data"""
    print("\n" + "="*60)
    print("Database Seeding - Faculty Attendance Portal")
    print("="*60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database tables created")
    
    db = SessionLocal()
    
    try:
        # 1. Create class (faculty)
        print("\n1. Creating class account...")
        existing_class = db.query(Class).filter(Class.class_name == "AIML-A").first()
        
        if not existing_class:
            aiml_class = Class(
                class_name="AIML-A",
                password_hash=get_password_hash("faculty@123")
            )
            db.add(aiml_class)
            db.commit()
            print("✓ Created class: AIML-A (password: faculty@123)")
        else:
            print("  Class AIML-A already exists")
        
        # 2. Import students from CSV
        print("\n2. Importing students from CSV...")
        students_csv = Path(__file__).parent.parent / "data" / "students.csv"
        
        if students_csv.exists():
            with open(students_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                student_count = 0
                
                for row in reader:
                    # Check if student already exists
                    existing_student = db.query(Student).filter(
                        Student.reg_no == row['RegNo']
                    ).first()
                    
                    if not existing_student:
                        student = Student(
                            reg_no=row['RegNo'],
                            name=row['Name'],
                            class_name=row['Class'],
                            email=row.get('Email', '')
                        )
                        db.add(student)
                        student_count += 1
                
                db.commit()
                print(f"✓ Imported {student_count} students from CSV")
        else:
            print(f"  Warning: students.csv not found at {students_csv}")
            print("  Creating sample student...")
            
            # Create sample student if CSV doesn't exist
            existing_student = db.query(Student).filter(
                Student.reg_no == "RA2311026020045"
            ).first()
            
            if not existing_student:
                student = Student(
                    reg_no="RA2311026020045",
                    name="Shemil Sainudeen",
                    class_name="AIML-A",
                    email="ss6337@srmist.edu.in"
                )
                db.add(student)
                db.commit()
                print("✓ Created sample student")
        
        # 3. Create timetable from provided sample (AIML-A, Semester III/IV)
        print("\n3. Creating timetable...")
        
        # Check if timetable already exists
        existing_tt = db.query(Timetable).filter(
            Timetable.class_name == "AIML-A"
        ).first()
        
        if not existing_tt:
            timetable_data = [
                # Monday
                ("MON", 1, "8:00", "8:50", "21CSC304J", "Compiler Design", False),
                ("MON", 2, "8:50", "9:40", "21ECO105T", "Fiber Optics and Optoelectronics", False),
                ("MON", 3, "9:50", "10:40", "21CSE355T", "Data Mining and Analytics", False),
                ("MON", 4, "10:40", "11:30", "21CSC303J", "Software Engineering and Project Management", False),
                ("MON", 5, "12:20", "1:10", None, "LUNCH", True),
                ("MON", 6, "1:10", "2:00", None, None, False),  # Free
                ("MON", 7, "2:00", "2:50", "21CSP302L", "Project", False),
                ("MON", 8, "2:50", "3:40", None, None, False),  # Free
                
                # Tuesday
                ("TUE", 1, "8:00", "8:50", "21CSE355T", "Data Mining and Analytics", False),
                ("TUE", 2, "8:50", "9:40", "21CSE356T", "Natural Language Processing", False),
                ("TUE", 3, "9:50", "10:40", "21ECO105T", "Fiber Optics and Optoelectronics", False),
                ("TUE", 4, "10:40", "11:30", "21CSS303T", "Data Science", False),
                ("TUE", 5, "12:20", "1:10", None, "LUNCH", True),
                ("TUE", 6, "1:10", "2:00", None, None, False),  # Free
                ("TUE", 7, "2:00", "2:50", None, None, False),  # Free
                ("TUE", 8, "2:50", "3:40", None, None, False),  # Free
                
                # Wednesday
                ("WED", 1, "8:00", "8:50", "21CSS303T", "Data Science", False),
                ("WED", 2, "8:50", "9:40", "21ECO105T", "Fiber Optics and Optoelectronics", False),
                ("WED", 3, "9:50", "10:40", "21CSE356T", "Natural Language Processing", False),
                ("WED", 4, "10:40", "11:30", "21CSC303J", "Software Engineering and Project Management", False),
                ("WED", 5, "12:20", "1:10", None, "LUNCH", True),
                ("WED", 6, "1:10", "2:00", None, None, False),  # Free
                ("WED", 7, "2:00", "2:50", "21LEM302T", "Indian Traditional Knowledge", False),
                ("WED", 8, "2:50", "3:40", None, None, False),  # Free
                
                # Thursday
                ("THU", 1, "8:00", "8:50", "21CSC303J", "Software Engineering and Project Management", False),
                ("THU", 2, "8:50", "9:40", None, None, False),  # Free
                ("THU", 3, "9:50", "10:40", "21CSP302L", "Project", False),
                ("THU", 4, "10:40", "11:30", None, None, False),  # Free
                ("THU", 5, "12:20", "1:10", None, "LUNCH", True),
                ("THU", 6, "1:10", "2:00", "21CSC304J", "Compiler Design", False),
                ("THU", 7, "2:00", "2:50", None, None, False),  # Free
                ("THU", 8, "2:50", "3:40", "21PDM302L", "Employability Skills and Practices", False),
                
                # Friday
                ("FRI", 1, "8:00", "8:50", "21CSE356T", "Natural Language Processing", False),
                ("FRI", 2, "8:50", "9:40", "21CSE355T", "Data Mining and Analytics", False),
                ("FRI", 3, "9:50", "10:40", "21CSC304J", "Compiler Design", False),
                ("FRI", 4, "10:40", "11:30", None, None, False),  # Free
                ("FRI", 5, "12:20", "1:10", None, "LUNCH", True),
                ("FRI", 6, "1:10", "2:00", None, None, False),  # Free
                ("FRI", 7, "2:00", "2:50", None, None, False),  # Free
                ("FRI", 8, "2:50", "3:40", None, None, False),  # Free
            ]
            
            for day, period, start, end, code, name, is_break in timetable_data:
                # Parse time
                start_time = time(*map(int, start.split(":")))
                end_time = time(*map(int, end.split(":")))
                
                entry = Timetable(
                    class_name="AIML-A",
                    day=day,
                    period=period,
                    subject_code=code,
                    subject_name=name,
                    start_time=start_time,
                    end_time=end_time,
                    is_break=is_break
                )
                db.add(entry)
            
            db.commit()
            print("✓ Created timetable for AIML-A (40 periods)")
        else:
            print("  Timetable already exists for AIML-A")
        
        print("\n" + "="*60)
        print("✓ Database seeding completed successfully!")
        print("="*60)
        print("\nYou can now:")
        print("  1. Start the backend server: uvicorn backend.main:app --reload")
        print("  2. Login with:")
        print("     Username: AIML-A")
        print("     Password: faculty@123")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
