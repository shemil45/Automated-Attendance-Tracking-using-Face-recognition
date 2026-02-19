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
        """Initialize — ensure tables exist"""
        print("\nConnecting to database...")
        init_db()
        print("✓ Connected")

    def _new_session(self):
        """Return a fresh session. Caller must close it."""
        return SessionLocal()

    def close(self):
        pass  # No persistent session to close

    def get_trained_names(self):
        """Get distinct names from face_encodings table in Supabase"""
        db = self._new_session()
        try:
            rows = db.query(FaceEncoding.name).distinct().all()
            return sorted([r.name for r in rows])
        finally:
            db.close()

    def list_students(self):
        """List all students currently in the database"""
        db = self._new_session()
        try:
            students = db.query(Student).order_by(Student.reg_no).all()
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
        finally:
            db.close()

    def add_student_interactive(self):
        """Interactively add or update a student in the database"""
        trained_names = self.get_trained_names()

        # --- Collect all user input BEFORE opening a DB session ---
        if trained_names:
            print("\nTrained faces found in Supabase (face_encodings table):")
            # Quick read-only check for display only
            db_check = self._new_session()
            try:
                for i, name in enumerate(trained_names, 1):
                    exists = db_check.query(Student).filter(Student.name == name).first()
                    status = "✓ In DB" if exists else "✗ Not in DB"
                    print(f"  {i}. {name} — {status}")
            finally:
                db_check.close()
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

        # Quick check if student already exists (read-only, short-lived session)
        db_read = self._new_session()
        try:
            existing_data = db_read.query(Student).filter(Student.name == name).first()
            if existing_data:
                existing_info = {
                    "reg_no": existing_data.reg_no,
                    "class_name": existing_data.class_name,
                    "email": existing_data.email,
                }
                print(f"\n⚠ {name} already exists in DB:")
                print(f"   RegNo : {existing_info['reg_no']}")
                print(f"   Class : {existing_info['class_name']}")
                print(f"   Email : {existing_info['email']}")
                is_update = True
            else:
                existing_info = None
                is_update = False
        finally:
            db_read.close()

        if is_update:
            update = input("\nUpdate this student? (y/n): ").strip().lower()
            if update != 'y':
                return False

        # Registration number — collect input, do quick uniqueness read
        while True:
            regno = input("Registration Number: ").strip()
            if not regno:
                print("Registration number cannot be empty.")
                continue
            db_dup = self._new_session()
            try:
                duplicate = db_dup.query(Student).filter(Student.reg_no == regno).first()
                dup_name = duplicate.name if duplicate else None
            finally:
                db_dup.close()
            if dup_name and dup_name != name:
                print(f"⚠ RegNo '{regno}' already used by {dup_name}. Use a unique RegNo.")
            else:
                break

        class_name = input("Class/Section (e.g. AIML-A): ").strip()
        email = input("Email (optional): ").strip() or None

        # --- All input collected — NOW open a fresh session and commit quickly ---
        db = self._new_session()
        try:
            if is_update:
                student = db.query(Student).filter(Student.name == name).first()
                if student:
                    student.reg_no = regno
                    student.class_name = class_name
                    student.email = email
                    db.commit()
                    print(f"\n✓ Updated {name} in database")
            else:
                student = Student(
                    reg_no=regno,
                    name=name,
                    class_name=class_name,
                    email=email
                )
                db.add(student)
                db.commit()
                print(f"\n✓ Added {name} to database")
        except Exception as e:
            db.rollback()
            print(f"\n✗ Database error: {e}")
            return False
        finally:
            db.close()

        return True

    def delete_student_interactive(self):
        """Delete a student from the database"""
        self.list_students()
        regno = input("\nEnter RegNo of student to delete (or blank to cancel): ").strip()
        if not regno:
            return

        # Quick read to get student name for confirmation prompt
        db_read = self._new_session()
        try:
            student_data = db_read.query(Student).filter(Student.reg_no == regno).first()
            if not student_data:
                print(f"No student found with RegNo '{regno}'")
                return
            student_name = student_data.name
        finally:
            db_read.close()

        confirm = input(f"Delete {student_name} ({regno})? (y/n): ").strip().lower()
        if confirm == 'y':
            # Fresh session — commit immediately after deletes
            db = self._new_session()
            try:
                student = db.query(Student).filter(Student.reg_no == regno).first()
                if not student:
                    print("Student not found (may have been deleted already).")
                    return
                # 1. Delete attendance records (NOT NULL FK — must go first)
                rec_count = db.query(AttendanceRecord).filter(AttendanceRecord.reg_no == regno).delete()
                # 2. Delete face encodings
                enc_count = db.query(FaceEncoding).filter(FaceEncoding.name == student.name).delete()
                # 3. Delete student
                db.delete(student)
                db.commit()
                print(f"✓ Deleted {student_name}")
                print(f"  └─ {rec_count} attendance record(s) removed")
                print(f"  └─ {enc_count} face encoding(s) removed")
            except Exception as e:
                db.rollback()
                print(f"✗ Database error: {e}")
            finally:
                db.close()

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
