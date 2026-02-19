"""
Student Database Setup Script
Adds/updates students directly in the Supabase (PostgreSQL) database.
"""

import sys
from pathlib import Path

# Add project root to path so backend modules are importable
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import SessionLocal, init_db
from backend.models import Student, FaceEncoding, AttendanceRecord


class StudentDatabase:
    def __init__(self):
        """Initialize — connect to DB"""
        print("\nConnecting to database...")
        init_db()
        self.db = SessionLocal()
        print("✓ Connected")

    def close(self):
        self.db.close()

    def get_trained_names(self):
        """Get distinct names from face_encodings table in Supabase"""
        rows = self.db.query(FaceEncoding.name).distinct().all()
        return sorted([r.name for r in rows])

    def list_students(self):
        """List all students currently in the database"""
        students = self.db.query(Student).order_by(Student.reg_no).all()
        if not students:
            print("\nNo students in database.")
            return
        print(f"\n{'='*70}")
        print(f"{'RegNo':<18} {'Name':<25} {'Class':<12} {'Email':<20}")
        print(f"{'='*70}")
        for s in students:
            print(f"{s.reg_no:<18} {s.name:<25} {s.class_name:<12} {s.email or '':<20}")
        print(f"{'='*70}")
        print(f"Total: {len(students)} student(s)")

    def add_student_interactive(self):
        """Interactively add or update a student in the database"""
        trained_names = self.get_trained_names()

        if trained_names:
            print("\nTrained faces found in Supabase (face_encodings table):")
            for i, name in enumerate(trained_names, 1):
                exists = self.db.query(Student).filter(Student.name == name).first()
                status = "✓ In DB" if exists else "✗ Not in DB"
                print(f"  {i}. {name} — {status}")
        else:
            print("\n⚠ No trained faces found in Supabase. Run train_model.py first.")

        print("\n" + "="*50)
        print("Add / Update Student")
        print("="*50)

        # Name
        while True:
            name_input = input("\nEnter student name (or number from list above): ").strip()
            if not name_input:
                return False
            if name_input.isdigit():
                idx = int(name_input) - 1
                if trained_names and 0 <= idx < len(trained_names):
                    name = trained_names[idx]
                    break
                else:
                    print("Invalid number.")
            else:
                name = name_input
                break

        # Check if already exists
        existing = self.db.query(Student).filter(Student.name == name).first()
        if existing:
            print(f"\n⚠ {name} already exists in DB:")
            print(f"   RegNo : {existing.reg_no}")
            print(f"   Class : {existing.class_name}")
            print(f"   Email : {existing.email}")
            update = input("\nUpdate this student? (y/n): ").strip().lower()
            if update != 'y':
                return False

        # Registration number
        while True:
            regno = input("Registration Number: ").strip()
            if not regno:
                print("Registration number cannot be empty.")
                continue
            # Check uniqueness (ignore current student if updating)
            duplicate = self.db.query(Student).filter(
                Student.reg_no == regno
            ).first()
            if duplicate and duplicate.name != name:
                print(f"⚠ RegNo '{regno}' already used by {duplicate.name}. Use a unique RegNo.")
            else:
                break

        class_name = input("Class/Section (e.g. AIML-A): ").strip()
        email = input("Email (optional): ").strip() or None

        if existing:
            # Update
            existing.reg_no = regno
            existing.class_name = class_name
            existing.email = email
            self.db.commit()
            print(f"\n✓ Updated {name} in database")
        else:
            # Insert
            student = Student(
                reg_no=regno,
                name=name,
                class_name=class_name,
                email=email
            )
            self.db.add(student)
            self.db.commit()
            print(f"\n✓ Added {name} to database")

        return True

    def delete_student_interactive(self):
        """Delete a student from the database"""
        self.list_students()
        regno = input("\nEnter RegNo of student to delete (or blank to cancel): ").strip()
        if not regno:
            return

        student = self.db.query(Student).filter(Student.reg_no == regno).first()
        if not student:
            print(f"No student found with RegNo '{regno}'")
            return

        confirm = input(f"Delete {student.name} ({regno})? (y/n): ").strip().lower()
        if confirm == 'y':
            # 1. Delete attendance records (NOT NULL FK — must go first)
            rec_count = self.db.query(AttendanceRecord).filter(AttendanceRecord.reg_no == regno).delete()
            # 2. Delete face encodings
            enc_count = self.db.query(FaceEncoding).filter(FaceEncoding.name == student.name).delete()
            # 3. Delete student
            self.db.delete(student)
            self.db.commit()
            print(f"✓ Deleted {student.name}")
            print(f"  └─ {rec_count} attendance record(s) removed")
            print(f"  └─ {enc_count} face encoding(s) removed")

    def setup(self):
        """Main interactive menu"""
        print("\n" + "="*50)
        print("  AttendNet — Student Manager (Supabase)")
        print("="*50)

        while True:
            print("\nOptions:")
            print("  1. Add / Update student")
            print("  2. View all students")
            print("  3. Delete a student")
            print("  4. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == '1':
                self.add_student_interactive()
            elif choice == '2':
                self.list_students()
            elif choice == '3':
                self.delete_student_interactive()
            elif choice == '4':
                print("\nExiting...")
                break
            else:
                print("Invalid option.")

        self.close()


def main():
    db = StudentDatabase()
    db.setup()


if __name__ == "__main__":
    main()
