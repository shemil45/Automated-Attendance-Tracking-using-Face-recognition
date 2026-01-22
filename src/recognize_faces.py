"""
Real-time Face Recognition Script
Uses MediaPipe for detection and FaceNet for recognition
"""

import cv2
import numpy as np
import pickle
from pathlib import Path
from keras_facenet import FaceNet
import urllib.request
import time

class FaceRecognizer:
    def __init__(self):
        """Initialize the face recognizer"""
        # Setup paths first (needed by face detector loader)
        self.base_dir = Path(__file__).parent.parent
        self.encodings_path = self.base_dir / "models" / "encodings.pkl"
        
        # Initialize FaceNet
        print("Loading FaceNet model...")
        self.facenet = FaceNet()
        print("✓ FaceNet model loaded")
        
        # Initialize OpenCV DNN Face Detector
        print("Loading face detector...")
        self.face_detector = self._load_face_detector()
        print("✓ Face detector loaded")
        
        # Recognition settings
        self.recognition_threshold = 0.6  # Lower = stricter matching
        
        # Load known face encodings
        self.known_encodings = []
        self.known_names = []
        self.load_encodings()
        
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
        
        unique_names = set(self.known_names)
        print(f"✓ Loaded {len(self.known_encodings)} encodings for {len(unique_names)} people")
        print(f"  People: {', '.join(unique_names)}")
        
        return True
    
    def get_face_encoding(self, face_image):
        """
        Generate face encoding using FaceNet
        
        Args:
            face_image: Cropped face image
            
        Returns:
            128-dimensional face encoding
        """
        try:
            # Resize to 160x160 (FaceNet input size)
            face_resized = cv2.resize(face_image, (160, 160))
            
            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            
            # Expand dimensions for batch processing
            face_array = np.expand_dims(face_rgb, axis=0)
            
            # Generate embedding
            embedding = self.facenet.embeddings(face_array)
            
            return embedding[0]
        except Exception as e:
            print(f"Error generating encoding: {e}")
            return None
    
    def recognize_face(self, face_encoding):
        """
        Compare face encoding with known encodings
        
        Args:
            face_encoding: 128-dimensional face encoding
            
        Returns:
            Tuple of (name, distance) or (None, None) if no match
        """
        if not self.known_encodings:
            return None, None
        
        # Calculate distances to all known faces
        distances = []
        for known_encoding in self.known_encodings:
            distance = np.linalg.norm(known_encoding - face_encoding)
            distances.append(distance)
        
        # Find best match
        min_distance_idx = np.argmin(distances)
        min_distance = distances[min_distance_idx]
        
        # Check if distance is below threshold
        if min_distance < self.recognition_threshold:
            name = self.known_names[min_distance_idx]
            return name, min_distance
        
        return "Unknown", min_distance
    
    def update_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time > 1.0:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self, camera_index=0):
        """
        Main recognition loop (optimized for better FPS)
        
        Args:
            camera_index: Camera index to use (0, 1, 2, etc.)
        """
        if not self.known_encodings:
            print("Error: No encodings loaded. Cannot start recognition.")
            return
        
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return
        
        print(f"\n{'='*60}")
        print("Face Recognition - Live Mode (Optimized)")
        print(f"{'='*60}")
        print(f"Recognition threshold: {self.recognition_threshold}")
        print(f"Press 'q' to quit")
        print(f"{'='*60}\n")
        
        # Performance optimization variables
        frame_count = 0
        process_every_n_frames = 3  # Process every 3rd frame for recognition
        cached_results = []  # Cache recognition results
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Only process face recognition every N frames
            if frame_count % process_every_n_frames == 0:
                # Prepare image for DNN
                blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
                self.face_detector.setInput(blob)
                detections = self.face_detector.forward()
                
                # Clear cached results
                cached_results = []
                
                # Process detections
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    if confidence > 0.5:
                        # Get bounding box
                        h, w = frame.shape[:2]
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (x, y, x2, y2) = box.astype("int")
                        
                        # Add padding for better face extraction
                        padding = 20
                        x_pad = max(0, x - padding)
                        y_pad = max(0, y - padding)
                        x2_pad = min(w, x2 + padding)
                        y2_pad = min(h, y2 + padding)
                        
                        # Extract face
                        face = frame[y_pad:y2_pad, x_pad:x2_pad]
                        
                        if face.size == 0:
                            continue
                        
                        # Get face encoding
                        face_encoding = self.get_face_encoding(face)
                        
                        if face_encoding is not None:
                            # Recognize face
                            name, distance = self.recognize_face(face_encoding)
                            
                            # Cache result (use original bbox coordinates)
                            cached_results.append({
                                'bbox': (x, y, x2 - x, y2 - y),
                                'name': name,
                                'distance': distance
                            })
            
            # Draw cached results on every frame (fast)
            for result in cached_results:
                x, y, width, height = result['bbox']
                name = result['name']
                distance = result['distance']
                
                # Determine color based on recognition
                if name and name != "Unknown":
                    color = (0, 255, 0)  # Green for recognized
                    label = f"{name} ({distance:.2f})"
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = f"Unknown ({distance:.2f})"
                
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + width, y + height), color, 2)
                
                # Draw label background
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x, y - 30), (x + label_size[0], y), color, -1)
                
                # Draw label text
                cv2.putText(frame, label, (x, y - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Update FPS
            self.update_fps()
            frame_count += 1
            
            # Display FPS
            h, w, _ = frame.shape
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display instructions
            cv2.putText(frame, "Press 'q' to quit", (10, h - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('Face Recognition', frame)
            
            # Handle key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nRecognition stopped by user")
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

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
    
    recognizer = FaceRecognizer()
    recognizer.run(camera_index)

if __name__ == "__main__":
    main()
