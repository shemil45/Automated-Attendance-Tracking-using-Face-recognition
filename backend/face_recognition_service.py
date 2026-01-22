"""
Face Recognition Service
Integrates with existing FaceNet recognition system for attendance
"""
import cv2
import numpy as np
from pathlib import Path
from keras_facenet import FaceNet
import urllib.request
import threading
from typing import Dict, Set, Optional

from .database import SessionLocal, init_db
from .models import FaceEncoding

class FaceRecognitionService:
    """Service for real-time face recognition during attendance sessions"""
    
    def __init__(self):
        """Initialize the face recognition service"""
        self.base_dir = Path(__file__).parent.parent
        
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
        
        # Load known face encodings from DB
        self.known_encodings = []
        self.known_names = []
        
        try:
            # Try loading from DB
            self.load_encodings_from_db()
        except Exception as e:
            print(f"Database unavailable for encodings: {e}")
            print("Attempting to load from local backup...")
            self.load_encodings_from_file()
        
        # Active sessions tracking
        self.active_sessions: Dict[int, dict] = {}
        self.session_locks: Dict[int, threading.Lock] = {}
    
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
            print("  Downloading model file...")
            url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
            urllib.request.urlretrieve(url, str(model_path))
        
        return cv2.dnn.readNetFromCaffe(str(prototxt_path), str(model_path))
    
    def load_encodings_from_db(self):
        """Load encodings from database"""
        print("Loading encodings from database...")
        # Ensure tables exist (helpful for first run)
        try:
            init_db()
        except:
            pass

        db = SessionLocal()
        try:
            encodings = db.query(FaceEncoding).all()
            
            self.known_encodings = []
            self.known_names = []
            
            for item in encodings:
                self.known_names.append(item.name)
                # Convert bytes back to numpy array
                nparr = np.frombuffer(item.encoding, dtype=np.float32)
                self.known_encodings.append(nparr)
                
            print(f"✓ Loaded {len(self.known_encodings)} encodings from database")
            return True
        finally:
            db.close()

    def load_encodings_from_file(self):
        """Fallback: Load saved face encodings from pickle"""
        import pickle
        encodings_path = self.base_dir / "models" / "encodings.pkl"
        
        if not encodings_path.exists():
            print(f"Warning: Encodings file not found: {encodings_path}")
            return False
        
        with open(encodings_path, "rb") as f:
            data = pickle.load(f)
        
        self.known_encodings = data["encodings"]
        self.known_names = data["names"]
            
        print(f"✓ Loaded {len(self.known_encodings)} encodings from file backup")
        return True
    
    def reload_encodings(self):
        """Reload encodings (for new students)"""
        print("Reloading face encodings...")
        try:
            return self.load_encodings_from_db()
        except:
            return self.load_encodings_from_file()
    
    def get_face_encoding(self, face_image):
        """Generate face encoding using FaceNet"""
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
        """Compare face encoding with known encodings"""
        if not self.known_encodings:
            return None, None
        
        # Calculate distances to all known faces
        distances = []
        for known_encoding in self.known_encodings:
            # Ensure safe comparison
            try:
                distance = np.linalg.norm(known_encoding - face_encoding)
            except:
                distance = 100.0 # High distance on error
            distances.append(distance)
        
        # Find best match
        min_distance_idx = np.argmin(distances)
        min_distance = distances[min_distance_idx]
        
        # Check if distance is below threshold
        if min_distance < self.recognition_threshold:
            name = self.known_names[min_distance_idx]
            return name, min_distance
        
        return None, min_distance

    def process_frame(self, session_id: int, image_bytes: bytes, recognized_callback) -> list:
        """
        Process a single frame from the frontend
        
        Args:
            session_id: The attendance session ID
            image_bytes: Raw image bytes from upload
            recognized_callback: Callback function(name) when a face is recognized
            
        Returns:
            list: List of recognized names in this frame
        """
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return []

        # Initialize session tracking if not exists
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                'recognized_students': set()
            }
            self.session_locks[session_id] = threading.Lock()
            
        recognized_in_frame = []
        
        # Detect faces
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.face_detector.setInput(blob)
        detections = self.face_detector.forward()
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > 0.5:
                h, w = frame.shape[:2]
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x2, y2) = box.astype("int")
                
                # Add padding
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
                    
                    if name:
                        recognized_in_frame.append(name)
                        
                        # Check if already recognized in this session
                        is_new = False
                        with self.session_locks[session_id]:
                            if name not in self.active_sessions[session_id]['recognized_students']:
                                self.active_sessions[session_id]['recognized_students'].add(name)
                                is_new = True
                        
                        # Call callback if new
                        if is_new:
                            recognized_callback(name)
                            print(f"Session {session_id}: Recognized {name}")

        return recognized_in_frame
    
    def get_recognized_students(self, session_id: int) -> Set[str]:
        """Get the set of recognized student names for a session"""
        if session_id not in self.active_sessions:
            return set()
        
        with self.session_locks[session_id]:
            return self.active_sessions[session_id]['recognized_students'].copy()

# Global face recognition service instance
face_recognition_service = FaceRecognitionService()
