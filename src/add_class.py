"""
add_class.py — Add a new class account to the AttendNet database.

Usage (from the project root):
    python src/add_class.py                        # interactive prompts
    python src/add_class.py AIML-B mypassword      # pass args directly
    python src/add_class.py AIML-B mypassword --csv data/aiml_b_students.csv
"""

import sys
import csv
import argparse
from pathlib import Path

# Make sure the project root is on the path so backend imports resolve
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from backend.database import SessionLocal, init_db
from backend.models import Class, Student, Timetable
from backend.auth import get_password_hash


# ──────────────────────────────────────────────────────────────────────────────
# Timetable template
# Each entry: (day, period, start, end, subject_code, subject_name, is_break)
# Edit this to match the new class's actual timetable, or leave empty ([])
# to skip timetable creation.
# ──────────────────────────────────────────────────────────────────────────────
NEW_CLASS_TIMETABLE = [
    # Monday
    ("MON", 1, "8:00",  "8:50",  "21CSC305J", "Operating Systems",                  False),
    ("MON", 2, "8:50",  "9:40",  "21CSE357T", "Machine Learning",                   False),
    ("MON", 3, "9:50",  "10:40", "21CSS304T", "Big Data Analytics",                 False),
    ("MON", 4, "10:40", "11:30", "21CSC306J", "Computer Networks",                  False),
    ("MON", 5, "12:20", "1:10",  None,         "LUNCH",                             True),
    ("MON", 6, "1:10",  "2:00",  "21CSP303L", "Mini Project",                       False),
    ("MON", 7, "2:00",  "2:50",  "21LEM303T", "Environmental Science",              False),
    ("MON", 8, "2:50",  "3:40",  None,         None,                                False),

    # Tuesday
    ("TUE", 1, "8:00",  "8:50",  "21CSE357T", "Machine Learning",                   False),
    ("TUE", 2, "8:50",  "9:40",  "21CSC305J", "Operating Systems",                  False),
    ("TUE", 3, "9:50",  "10:40", "21CSE358T", "Deep Learning",                      False),
    ("TUE", 4, "10:40", "11:30", "21CSS304T", "Big Data Analytics",                 False),
    ("TUE", 5, "12:20", "1:10",  None,         "LUNCH",                             True),
    ("TUE", 6, "1:10",  "2:00",  None,         None,                                False),
    ("TUE", 7, "2:00",  "2:50",  "21CSP303L", "Mini Project",                       False),
    ("TUE", 8, "2:50",  "3:40",  None,         None,                                False),

    # Wednesday
    ("WED", 1, "8:00",  "8:50",  "21CSE358T", "Deep Learning",                      False),
    ("WED", 2, "8:50",  "9:40",  "21CSC306J", "Computer Networks",                  False),
    ("WED", 3, "9:50",  "10:40", "21CSE357T", "Machine Learning",                   False),
    ("WED", 4, "10:40", "11:30", "21CSC305J", "Operating Systems",                  False),
    ("WED", 5, "12:20", "1:10",  None,         "LUNCH",                             True),
    ("WED", 6, "1:10",  "2:00",  "21LEM303T", "Environmental Science",              False),
    ("WED", 7, "2:00",  "2:50",  None,         None,                                False),
    ("WED", 8, "2:50",  "3:40",  None,         None,                                False),

    # Thursday
    ("THU", 1, "8:00",  "8:50",  "21CSC306J", "Computer Networks",                  False),
    ("THU", 2, "8:50",  "9:40",  "21CSE358T", "Deep Learning",                      False),
    ("THU", 3, "9:50",  "10:40", "21CSS304T", "Big Data Analytics",                 False),
    ("THU", 4, "10:40", "11:30", None,         None,                                False),
    ("THU", 5, "12:20", "1:10",  None,         "LUNCH",                             True),
    ("THU", 6, "1:10",  "2:00",  "21CSC305J", "Operating Systems",                  False),
    ("THU", 7, "2:00",  "2:50",  "21CSP303L", "Mini Project",                       False),
    ("THU", 8, "2:50",  "3:40",  "21PDM302L", "Employability Skills and Practices", False),

    # Friday
    ("FRI", 1, "8:00",  "8:50",  "21CSS304T", "Big Data Analytics",                 False),
    ("FRI", 2, "8:50",  "9:40",  "21CSE358T", "Deep Learning",                      False),
    ("FRI", 3, "9:50",  "10:40", "21CSC306J", "Computer Networks",                  False),
    ("FRI", 4, "10:40", "11:30", None,         None,                                False),
    ("FRI", 5, "12:20", "1:10",  None,         "LUNCH",                             True),
    ("FRI", 6, "1:10",  "2:00",  "21LEM303T", "Environmental Science",              False),
    ("FRI", 7, "2:00",  "2:50",  None,         None,                                False),
    ("FRI", 8, "2:50",  "3:40",  None,         None,                                False),
]


def add_class(class_name: str, password: str, csv_path: str | None = None):
    print("\n" + "=" * 60)
    print(f"Adding Class: {class_name}")
    print("=" * 60)

    # Ensure tables exist
    init_db()

    db = SessionLocal()
    try:
        # ── 1. Create class account ──────────────────────────────────────────
        print("\n1. Creating class account...")
        existing = db.query(Class).filter(Class.class_name == class_name).first()
        if existing:
            print(f"  ⚠  Class '{class_name}' already exists — skipping creation.")
        else:
            new_class = Class(
                class_name=class_name,
                password_hash=get_password_hash(password),
            )
            db.add(new_class)
            db.commit()
            print(f"  ✓ Created class '{class_name}' with the provided password.")

        # ── 2. Import students ───────────────────────────────────────────────
        print("\n2. Importing students...")
        if csv_path:
            csv_file = Path(csv_path)
            if not csv_file.is_absolute():
                csv_file = ROOT / csv_path

            if csv_file.exists():
                count = 0
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if not db.query(Student).filter(
                            Student.reg_no == row["RegNo"]
                        ).first():
                            db.add(Student(
                                reg_no=row["RegNo"],
                                name=row["Name"],
                                class_name=class_name,
                                email=row.get("Email", ""),
                            ))
                            count += 1
                db.commit()
                print(f"  ✓ Imported {count} new students from {csv_file.name}")
            else:
                print(f"  ✗ CSV not found at: {csv_file}")
                print("    Students were NOT imported — add them later via the admin.")
        else:
            print("  — No CSV provided. Students can be added later.")

        # ── 3. Create timetable ──────────────────────────────────────────────
        print("\n3. Creating timetable...")
        if NEW_CLASS_TIMETABLE:
            existing_tt = db.query(Timetable).filter(
                Timetable.class_name == class_name
            ).first()

            if existing_tt:
                print(f"  ⚠  Timetable already exists for '{class_name}' — skipping.")
            else:
                from datetime import time as dtime
                for day, period, start, end, code, name, is_break in NEW_CLASS_TIMETABLE:
                    sh, sm = map(int, start.split(":"))
                    eh, em = map(int, end.split(":"))
                    db.add(Timetable(
                        class_name=class_name,
                        day=day,
                        period=period,
                        subject_code=code,
                        subject_name=name,
                        start_time=dtime(sh, sm),
                        end_time=dtime(eh, em),
                        is_break=is_break,
                    ))
                db.commit()
                print(f"  ✓ Created timetable for '{class_name}' "
                      f"({len(NEW_CLASS_TIMETABLE)} periods)")
        else:
            print("  — NEW_CLASS_TIMETABLE is empty. Edit add_class.py to add periods.")

        # ── Summary ──────────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("✓ Done!")
        print("=" * 60)
        print(f"\n  Login with:")
        print(f"    Username : {class_name}")
        print(f"    Password : {password}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new class to AttendNet")
    parser.add_argument("class_name", nargs="?", help="Class name, e.g. AIML-B")
    parser.add_argument("password",   nargs="?", help="Login password for the class")
    parser.add_argument("--csv",      help="Path to students CSV (columns: RegNo, Name, Email)")
    args = parser.parse_args()

    # Fall back to interactive prompts if args not supplied
    class_name = args.class_name or input("Enter class name (e.g. AIML-B): ").strip()
    password   = args.password   or input("Enter password for this class : ").strip()

    if not class_name or not password:
        print("✗ Class name and password are required.")
        sys.exit(1)

    add_class(class_name, password, args.csv)
