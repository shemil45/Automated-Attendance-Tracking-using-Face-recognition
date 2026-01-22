"""
Face Capture Script
Captures training images from webcam using OpenCV face detection
"""

import cv2
import os
from pathlib import Path

class FaceCapture:
    def __init__(self, person_name):
        """
        Initialize face capture system
        
        Args:
            person_name: Name of the person whose face is being captured
        """
        self.person_name = person_name
        
        # Initialize OpenCV Haar Cascade Face Detection
        # Using Haar Cascade as it's more reliable and doesn't depend on MediaPipe solutions
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("Error loading face cascade classifier")
        
        # Setup directories
        self.base_dir = Path(__file__).parent.parent
        self.save_dir = self.base_dir / "data" / "known_faces" / person_name
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Capture settings
        self.image_count = 0
        self.target_images = 30
        
    def capture_images(self, camera_index=0):
        """
        Capture face images from webcam
        
        Args:
            camera_index: Camera index to use (0, 1, 2, etc.)
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return 0
        
        print(f"\n{'='*60}")
        print(f"Face Capture Mode - {self.person_name}")
        print(f"{'='*60}")
        print(f"Target: {self.target_images} images")
        print(f"Save location: {self.save_dir}")
        print(f"\nInstructions:")
        print(f"  - Press SPACEBAR to capture an image")
        print(f"  - Press 'q' to quit")
        print(f"  - Vary your angles, expressions, and distance")
        print(f"{'='*60}\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert to grayscale for Haar Cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces using Haar Cascade
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Draw detection results
            display_frame = frame.copy()
            face_detected = len(faces) > 0
            
            for (x, y, w, h) in faces:
                # Draw rectangle around face
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), 
                            (0, 255, 0), 2)
                
                # Display "Face Detected" text
                cv2.putText(display_frame, "Face Detected", 
                          (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                          0.5, (0, 255, 0), 2)
            
            # Display status
            status_color = (0, 255, 0) if face_detected else (0, 0, 255)
            status_text = "Face Detected - Press SPACE" if face_detected else "No Face Detected"
            cv2.putText(display_frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # Display progress
            progress_text = f"Captured: {self.image_count}/{self.target_images}"
            cv2.putText(display_frame, progress_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show frame
            cv2.imshow('Face Capture', display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\nCapture cancelled by user")
                break
            elif key == ord(' ') and face_detected:
                # Save image
                filename = f"{self.person_name}_{self.image_count + 1:03d}.jpg"
                filepath = self.save_dir / filename
                cv2.imwrite(str(filepath), frame)
                self.image_count += 1
                print(f"✓ Captured image {self.image_count}/{self.target_images}: {filename}")
                
                if self.image_count >= self.target_images:
                    print(f"\n{'='*60}")
                    print(f"✓ Successfully captured {self.image_count} images!")
                    print(f"{'='*60}\n")
                    break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        return self.image_count

def detect_cameras():
    """Detect available cameras"""
    available_cameras = []
    for i in range(5):  # Check first 5 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def main():
    """Main function"""
    print("\n" + "="*60)
    print("Face Recognition - Image Capture")
    print("="*60)
    
    # Detect available cameras
    print("\nDetecting available cameras...")
    cameras = detect_cameras()
    
    if not cameras:
        print("Error: No cameras detected")
        return
    
    print(f"Found {len(cameras)} camera(s): {cameras}")
    
    # Let user select camera
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
    
    person_name = input("\nEnter person's name: ").strip()
    
    if not person_name:
        print("Error: Name cannot be empty")
        return
    
    # Create capture instance and start capturing
    capturer = FaceCapture(person_name)
    images_captured = capturer.capture_images(camera_index)
    
    if images_captured > 0:
        print(f"\nNext step: Run train_model.py to generate face encodings")
    else:
        print("\nNo images captured. Please try again.")

if __name__ == "__main__":
    main()
