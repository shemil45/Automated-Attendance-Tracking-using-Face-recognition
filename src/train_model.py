"""
Face Recognition Training Script
Generates face encodings using FaceNet and saves them for recognition
"""

import cv2
import numpy as np
import pickle
from pathlib import Path
from keras_facenet import FaceNet
import urllib.request

class FaceTrainer:
    def __init__(self):
        """Initialize the face trainer"""
        # Setup paths first (needed by face detector loader)
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / "known_faces"
        self.models_dir = self.base_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize FaceNet
        print("Loading FaceNet model...")
        self.facenet = FaceNet()
        print("✓ FaceNet model loaded")
        
        # Initialize OpenCV DNN Face Detector
        print("Loading face detector...")
        self.face_detector = self._load_face_detector()
        print("✓ Face detector loaded")
        
        # Storage for encodings
        self.encodings = []
        self.names = []
    
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
        
    def detect_and_crop_face(self, image):
        """
        Detect face in image and return cropped face
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Cropped face image or None if no face detected
        """
        h, w = image.shape[:2]
        
        # Prepare image for DNN
        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.face_detector.setInput(blob)
        detections = self.face_detector.forward()
        
        # Find detection with highest confidence
        max_confidence = 0
        best_detection = None
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5 and confidence > max_confidence:
                max_confidence = confidence
                best_detection = detections[0, 0, i, 3:7]
        
        if best_detection is None:
            return None
        
        # Get bounding box
        box = best_detection * np.array([w, h, w, h])
        (x, y, x2, y2) = box.astype("int")
        
        # Add padding
        padding = 20
        x = max(0, x - padding)
        y = max(0, y - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        # Crop face
        face = image[y:y2, x:x2]
        
        return face
    
    def get_face_encoding(self, face_image):
        """
        Generate face encoding using FaceNet
        
        Args:
            face_image: Cropped face image
            
        Returns:
            128-dimensional face encoding
        """
        # Resize to 160x160 (FaceNet input size)
        face_resized = cv2.resize(face_image, (160, 160))
        
        # Convert BGR to RGB
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        
        # Expand dimensions for batch processing
        face_array = np.expand_dims(face_rgb, axis=0)
        
        # Generate embedding
        embedding = self.facenet.embeddings(face_array)
        
        return embedding[0]
    
    def load_encodings(self):
        """Load existing encodings if available"""
        output_path = self.models_dir / "encodings.pkl"
        if output_path.exists():
            print(f"Loading existing encodings from: {output_path}")
            try:
                with open(output_path, "rb") as f:
                    data = pickle.load(f)
                    self.encodings = data.get("encodings", [])
                    self.names = data.get("names", [])
                    print(f"✓ Loaded {len(self.encodings)} existing encodings for {len(set(self.names))} people")
            except Exception as e:
                print(f"⚠ Warning: Could not load existing encodings: {e}")
                print("Starting with empty encodings.")

    def load_training_data(self):
        """Load and process all training images"""
        if not self.data_dir.exists():
            print(f"Error: Data directory not found: {self.data_dir}")
            return False
        
        person_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        
        if not person_dirs:
            print(f"Error: No person directories found in {self.data_dir}")
            print("Please run capture_faces.py first to collect training images")
            return False
        
        print(f"\n{'='*60}")
        print("Processing Training Images")
        print(f"{'='*60}\n")
        
        total_images = 0
        successful_encodings = 0
        
        for person_dir in person_dirs:
            person_name = person_dir.name
            image_files = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png"))
            
            if not image_files:
                print(f"⚠ No images found for {person_name}")
                continue

            # Deduplication: Remove existing encodings for this person
            if person_name in self.names:
                print(f"↻ Re-processing {person_name}: Removing old encodings...")
                # Create a new list keeping only those NOT matching the current person
                new_encodings = []
                new_names = []
                for enc, name in zip(self.encodings, self.names):
                    if name != person_name:
                        new_encodings.append(enc)
                        new_names.append(name)
                
                removed_count = len(self.names) - len(new_names)
                self.encodings = new_encodings
                self.names = new_names
                print(f"  - Removed {removed_count} old encodings")

            print(f"Processing {person_name}: {len(image_files)} images")
            
            for img_path in image_files:
                total_images += 1
                
                # Load image
                image = cv2.imread(str(img_path))
                
                if image is None:
                    print(f"  ✗ Failed to load: {img_path.name}")
                    continue
                
                # Detect and crop face
                face = self.detect_and_crop_face(image)
                
                if face is None:
                    print(f"  ✗ No face detected: {img_path.name}")
                    continue
                
                # Generate encoding
                try:
                    encoding = self.get_face_encoding(face)
                    self.encodings.append(encoding)
                    self.names.append(person_name)
                    successful_encodings += 1
                    print(f"  ✓ Encoded: {img_path.name}")
                except Exception as e:
                    print(f"  ✗ Encoding failed for {img_path.name}: {e}")
            
            print()
        
        print(f"{'='*60}")
        print(f"Summary:")
        print(f"  Total images processed: {total_images}")
        print(f"  Successful new encodings: {successful_encodings}")
        print(f"  Total encodings in memory: {len(self.encodings)}")
        print(f"{'='*60}\n")
        
        # Return true even if no new encodings, as we might just be saving loaded ones
        return True
    
    def save_encodings(self):
        """Save encodings to file"""
        if not self.encodings:
            print("Error: No encodings to save")
            return False
        
        output_path = self.models_dir / "encodings.pkl"
        
        data = {
            "encodings": self.encodings,
            "names": self.names
        }
        
        with open(output_path, "wb") as f:
            pickle.dump(data, f)
        
        print(f"✓ Encodings saved to: {output_path}")
        print(f"  Total encodings: {len(self.encodings)}")
        print(f"  Unique people: {len(set(self.names))}")
        
        return True
    
    def train(self):
        """Main training function"""
        print("\n" + "="*60)
        print("Face Recognition - Model Training")
        print("="*60)
        
        # Load existing encodings
        self.load_encodings()
        
        # Load and process images
        if not self.load_training_data():
            return False
        
        # Save encodings
        if not self.save_encodings():
            return False
        
        print(f"\n{'='*60}")
        print("✓ Training completed successfully!")
        print(f"{'='*60}")
        print("\nNext step: Run recognize_faces.py for real-time recognition")
        
        return True

def main():
    """Main function"""
    trainer = FaceTrainer()
    trainer.train()

if __name__ == "__main__":
    main()
