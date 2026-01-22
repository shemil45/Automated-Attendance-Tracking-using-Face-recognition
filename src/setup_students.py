"""
Student Database Setup Script
Creates and manages student database for attendance system
"""

import csv
from pathlib import Path

class StudentDatabase:
    def __init__(self):
        """Initialize student database manager"""
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.known_faces_dir = self.data_dir / "known_faces"
        self.students_file = self.data_dir / "students.csv"
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_available_students(self):
        """Get list of students from known_faces directory"""
        if not self.known_faces_dir.exists():
            return []
        
        students = [d.name for d in self.known_faces_dir.iterdir() if d.is_dir()]
        return sorted(students)
    
    def load_existing_students(self):
        """Load existing student database"""
        students = {}
        
        if self.students_file.exists():
            with open(self.students_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    students[row['Name']] = row
        
        return students
    
    def save_students(self, students):
        """Save student database to CSV"""
        fieldnames = ['RegNo', 'Name', 'Class', 'Email']
        
        with open(self.students_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for student in students.values():
                writer.writerow(student)
        
        print(f"\n✓ Student database saved to: {self.students_file}")
    
    def add_student_interactive(self, students):
        """Add a student interactively"""
        available = self.get_available_students()
        
        if not available:
            print("\n⚠ No student folders found in data/known_faces/")
            print("Please run capture_faces.py first to capture student images")
            return False
        
        print("\nAvailable students (from known_faces folders):")
        for i, name in enumerate(available, 1):
            status = "✓ In database" if name in students else "✗ Not in database"
            print(f"  {i}. {name} - {status}")
        
        print("\n" + "="*60)
        print("Add New Student")
        print("="*60)
        
        # Select student name
        while True:
            name_input = input("\nEnter student name (or number from list above): ").strip()
            
            if not name_input:
                return False
            
            # Check if it's a number
            if name_input.isdigit():
                idx = int(name_input) - 1
                if 0 <= idx < len(available):
                    name = available[idx]
                    break
                else:
                    print("Invalid number. Please try again.")
            elif name_input in available:
                name = name_input
                break
            else:
                print(f"'{name_input}' not found in known_faces. Please choose from the list.")
        
        # Check if already exists
        if name in students:
            print(f"\n⚠ {name} already exists in database:")
            print(f"  RegNo: {students[name]['RegNo']}")
            print(f"  Class: {students[name]['Class']}")
            print(f"  Email: {students[name]['Email']}")
            
            update = input("\nUpdate this student? (y/n): ").strip().lower()
            if update != 'y':
                return False
        
        # Get student details
        while True:
            regno = input("Registration Number: ").strip()
            if regno:
                # Check if regno already used
                regno_exists = any(s['RegNo'] == regno for n, s in students.items() if n != name)
                if regno_exists:
                    print("⚠ Registration number already exists. Please use a unique RegNo.")
                else:
                    break
            else:
                print("Registration number cannot be empty")
        
        class_name = input("Class/Section: ").strip()
        email = input("Email (optional): ").strip()
        
        # Add to database
        students[name] = {
            'RegNo': regno,
            'Name': name,
            'Class': class_name,
            'Email': email
        }
        
        print(f"\n✓ Added {name} to database")
        return True
    
    def setup(self):
        """Main setup function"""
        print("\n" + "="*60)
        print("Student Database Setup")
        print("="*60)
        
        # Load existing students
        students = self.load_existing_students()
        
        if students:
            print(f"\nFound {len(students)} existing students in database")
        else:
            print("\nNo existing database found. Creating new database...")
        
        # Interactive loop
        while True:
            print("\n" + "="*60)
            print("Options:")
            print("  1. Add new student")
            print("  2. View all students")
            print("  3. Save and exit")
            print("  4. Exit without saving")
            print("="*60)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.add_student_interactive(students)
            
            elif choice == '2':
                if not students:
                    print("\nNo students in database")
                else:
                    print(f"\n{'='*60}")
                    print(f"{'RegNo':<15} {'Name':<20} {'Class':<15} {'Email':<30}")
                    print(f"{'='*60}")
                    for student in students.values():
                        print(f"{student['RegNo']:<15} {student['Name']:<20} "
                              f"{student['Class']:<15} {student['Email']:<30}")
                    print(f"{'='*60}")
                    print(f"Total: {len(students)} students")
            
            elif choice == '3':
                if students:
                    self.save_students(students)
                    print(f"\n✓ Database saved with {len(students)} students")
                else:
                    print("\n⚠ No students to save")
                break
            
            elif choice == '4':
                print("\nExiting without saving...")
                break
            
            else:
                print("Invalid option. Please try again.")

def main():
    """Main function"""
    db = StudentDatabase()
    db.setup()

if __name__ == "__main__":
    main()
