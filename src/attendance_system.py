"""
Automated Attendance System
Real-time face recognition attendance tracking with duplicate prevention
"""

import cv2
import numpy as np
import pickle
import csv
from pathlib import Path
from keras_facenet import FaceNet
import urllib.request
import time
from datetime import datetime

class AttendanceSystem:
    def __init__(self):
        """Initialize attendance system"""
        # Setup paths first (needed by face detector loader)
        self.base_dir = Path(__file__).parent.parent
        self.encodings_path = self.base_dir / "models" / "encodings.pkl"
        self.students_file = self.base_dir / "data" / "students.csv"
        self.attendance_dir = self.base_dir / "attendance"
        self.attendance_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize FaceNet
        print("Loading FaceNet model...")
        self.facenet = FaceNet()
        print("✓ FaceNet model loaded")
        
        # Initialize OpenCV DNN Face Detector
        print("Loading face detector...")
        self.face_detector = self._load_face_detector()
        print("✓ Face detector loaded")
        
        # Recognition settings
        self.recognition_threshold = 0.6
        
        # Load known face encodings
        self.known_encodings = []
        self.known_names = []
        self.load_encodings()
        
        # Load student database
        self.students = {}
        self.load_students()
        
        # Attendance tracking
        self.marked_students = set()  # Set of RegNos already marked
        self.attendance_log = []  # List of attendance records
        
        # Session info
        self.session_start = datetime.now()
        self.session_file = self.attendance_dir / f"attendance_{self.session_start.strftime('%Y%m%d_%H%M%S')}.csv"
        
        # FPS calculation
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
    
    def _load_face_detector(self):
        """Load OpenCV DNN face detector"""
        model_dir = self.base_dir / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        prototxt_path = model_dir / "deploy.prototxt"
        model_path = model_dir / "res10_300x300_ssd_iter_140000.caffemodel"
        
        # Download model files if they don't exist
        if not prototxt_path.exists():
            print("  Downloading prototxt file...")
            url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
            urllib.request.urlretrieve(url, str(prototxt_path))
        
        if not model_path.exists():
            print("  Downloading model file (this may take a moment)...")
            url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
            urllib.request.urlretrieve(url, str(model_path))
        
        return cv2.dnn.readNetFromCaffe(str(prototxt_path), str(model_path))
        
    def load_encodings(self):
        """Load saved face encodings"""
        if not self.encodings_path.exists():
            print(f"Error: Encodings file not found: {self.encodings_path}")
            print("Please run train_model.py first")
            return False
        
        with open(self.encodings_path, "rb") as f:
            data = pickle.load(f)
        
        self.known_encodings = data["encodings"]
        self.known_names = data["names"]
        
        print(f"✓ Loaded {len(self.known_encodings)} face encodings")
        return True
    
    def load_students(self):
        """Load student database"""
        if not self.students_file.exists():
            print(f"\n⚠ Warning: Student database not found: {self.students_file}")
            print("Please run setup_students.py first to create student database")
            return False
        
        with open(self.students_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.students[row['Name']] = row
        
        print(f"✓ Loaded {len(self.students)} students from database")
        return True
    
    def get_face_encoding(self, face_image):
        """Generate face encoding using FaceNet"""
        try:
            face_resized = cv2.resize(face_image, (160, 160))
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            face_array = np.expand_dims(face_rgb, axis=0)
            embedding = self.facenet.embeddings(face_array)
            return embedding[0]
        except Exception as e:
            return None
    
    def recognize_face(self, face_encoding):
        """Compare face encoding with known encodings"""
        if not self.known_encodings:
            return None, None
        
        distances = []
        for known_encoding in self.known_encodings:
            distance = np.linalg.norm(known_encoding - face_encoding)
            distances.append(distance)
        
        min_distance_idx = np.argmin(distances)
        min_distance = distances[min_distance_idx]
        
        if min_distance < self.recognition_threshold:
            name = self.known_names[min_distance_idx]
            return name, min_distance
        
        return "Unknown", min_distance
    
    def mark_attendance(self, name):
        """Mark attendance for a student"""
        # Check if student exists in database
        if name not in self.students:
            return False, "Not in database"
        
        student = self.students[name]
        regno = student['RegNo']
        
        # Check if already marked
        if regno in self.marked_students:
            return False, "Already marked"
        
        # Mark attendance
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        attendance_record = {
            'RegNo': regno,
            'Name': name,
            'Class': student['Class'],
            'Timestamp': timestamp,
            'Status': 'Present'
        }
        
        self.attendance_log.append(attendance_record)
        self.marked_students.add(regno)
        
        print(f"✓ Marked attendance: {name} ({regno}) at {timestamp}")
        
        return True, "Marked"
    
    def save_attendance(self):
        """Save attendance log to CSV"""
        if not self.attendance_log:
            print("\n⚠ No attendance records to save")
            return
        
        fieldnames = ['RegNo', 'Name', 'Class', 'Timestamp', 'Status']
        
        with open(self.session_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.attendance_log)
        
        print(f"\n✓ Attendance saved to: {self.session_file}")
        print(f"  Total students marked: {len(self.marked_students)}")
    
    def update_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time > 1.0:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self, camera_index=0):
        """Main attendance tracking loop"""
        if not self.known_encodings:
            print("Error: No encodings loaded")
            return
        
        if not self.students:
            print("Error: No student database loaded")
            return
        
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return
        
        print(f"\n{'='*60}")
        print("Attendance System - Active")
        print(f"{'='*60}")
        print(f"Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total students in database: {len(self.students)}")
        print(f"Press 'q' to end session and save attendance")
        print(f"{'='*60}\n")
        
        # Performance optimization
        frame_count = 0
        process_every_n_frames = 3
        cached_results = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            # Process recognition every N frames
            if frame_count % process_every_n_frames == 0:
                # Prepare image for DNN
                blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
                self.face_detector.setInput(blob)
                detections = self.face_detector.forward()
                cached_results = []
                
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    if confidence > 0.5:
                        # Get bounding box
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (x, y, x2, y2) = box.astype("int")
                        
                        padding = 20
                        x_pad = max(0, x - padding)
                        y_pad = max(0, y - padding)
                        x2_pad = min(w, x2 + padding)
                        y2_pad = min(h, y2 + padding)
                        
                        face = frame[y_pad:y2_pad, x_pad:x2_pad]
                        
                        if face.size == 0:
                            continue
                        
                        face_encoding = self.get_face_encoding(face)
                        
                        if face_encoding is not None:
                            name, distance = self.recognize_face(face_encoding)
                            
                            # Try to mark attendance
                            if name != "Unknown":
                                marked, status = self.mark_attendance(name)
                            else:
                                marked, status = False, "Unknown"
                            
                            cached_results.append({
                                'bbox': (x, y, x2 - x, y2 - y),
                                'name': name,
                                'distance': distance,
                                'status': status
                            })
            
            # Draw cached results
            for result in cached_results:
                x, y, width, height = result['bbox']
                name = result['name']
                distance = result['distance']
                status = result['status']
                
                # Color based on status
                if status == "Marked":
                    color = (0, 255, 0)  # Green - newly marked
                    label = f"{name} - MARKED"
                elif status == "Already marked":
                    color = (0, 255, 255)  # Yellow - already marked
                    label = f"{name} - PRESENT"
                elif status == "Not in database":
                    color = (255, 165, 0)  # Orange - recognized but not in DB
                    label = f"{name} - NOT IN DB"
                else:  # Unknown
                    color = (0, 0, 255)  # Red - unknown
                    label = "Unknown"
                
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + width, y + height), color, 2)
                
                # Draw label
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x, y - 30), (x + label_size[0] + 10, y), color, -1)
                cv2.putText(frame, label, (x + 5, y - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Update FPS
            self.update_fps()
            frame_count += 1
            
            # Display info overlay
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, f"Present: {len(self.marked_students)}/{len(self.students)}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.putText(frame, "Press 'q' to end session", (10, h - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Attendance System', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n\nEnding attendance session...")
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Save attendance
        self.save_attendance()
        
        # Print summary
        print(f"\n{'='*60}")
        print("Session Summary")
        print(f"{'='*60}")
        print(f"Total students in database: {len(self.students)}")
        print(f"Students marked present: {len(self.marked_students)}")
        print(f"Attendance rate: {len(self.marked_students)/len(self.students)*100:.1f}%")
        print(f"{'='*60}\n")

def detect_cameras():
    """Detect available cameras"""
    available_cameras = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def main():
    """Main function"""
    # Detect cameras
    print("\nDetecting available cameras...")
    cameras = detect_cameras()
    
    if not cameras:
        print("Error: No cameras detected")
        return
    
    print(f"Found {len(cameras)} camera(s): {cameras}")
    
    # Select camera
    if len(cameras) == 1:
        camera_index = cameras[0]
        print(f"Using camera {camera_index}")
    else:
        print("\nAvailable cameras:")
        for idx in cameras:
            print(f"  {idx}: Camera {idx}")
        
        while True:
            try:
                camera_input = input(f"\nSelect camera index (default 0): ").strip()
                camera_index = int(camera_input) if camera_input else 0
                
                if camera_index in cameras:
                    break
                else:
                    print(f"Invalid camera index. Choose from: {cameras}")
            except ValueError:
                print("Please enter a valid number")
    
    # Start attendance system
    system = AttendanceSystem()
    system.run(camera_index)

if __name__ == "__main__":
    main()
