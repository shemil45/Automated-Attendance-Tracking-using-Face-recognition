import cv2
import numpy as np
import pickle
from pathlib import Path
from keras_facenet import FaceNet
import urllib.request
import sys
import os

# Add root directory to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))
from backend.database import SessionLocal, init_db
from backend.models import FaceEncoding

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
        
        # In-memory storage for current training session
        self.new_encodings = []
    
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
        """Detect face in image and return cropped face"""
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
        """Generate face encoding using FaceNet"""
        # Resize to 160x160 (FaceNet input size)
        face_resized = cv2.resize(face_image, (160, 160))
        
        # Convert BGR to RGB
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        
        # Expand dimensions for batch processing
        face_array = np.expand_dims(face_rgb, axis=0)
        
        # Generate embedding
        embedding = self.facenet.embeddings(face_array)
        
        return embedding[0]
    
    def process_images(self):
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
        self.new_encodings = []
        
        for person_dir in person_dirs:
            person_name = person_dir.name
            image_files = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png"))
            
            if not image_files:
                print(f"⚠ No images found for {person_name}")
                continue

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
                    self.new_encodings.append({
                        "name": person_name,
                        "encoding": encoding
                    })
                    print(f"  ✓ Encoded: {img_path.name}")
                except Exception as e:
                    print(f"  ✗ Encoding failed for {img_path.name}: {e}")
            
            print()
        
        print(f"{'='*60}")
        print(f"Summary:")
        print(f"  Total images processed: {total_images}")
        print(f"  New encodings generated: {len(self.new_encodings)}")
        print(f"{'='*60}\n")
        
        return True
    
    def save_encodings_to_db(self):
        """Save encodings to PostgreSQL database"""
        if not self.new_encodings:
            print("Error: No encodings to save")
            return False
            
        print("Saving encodings to database...")
        db = SessionLocal()
        try:
            # Optional: Clear existing encodings to avoid duplicates if re-training completely?
            # Ideally we might want to sync, but for now let's wipe and replace for simplicity 
            # OR only add new ones? 
            # Strategy: Delete all encodings for the people we just processed
            
            processed_people = set(item["name"] for item in self.new_encodings)
            print(f"Updating data for: {', '.join(processed_people)}")
            
            for person in processed_people:
                db.query(FaceEncoding).filter(FaceEncoding.name == person).delete()
            
            # Add new encodings
            count = 0
            for item in self.new_encodings:
                # Convert numpy array to bytes
                encoding_bytes = item["encoding"].tobytes()
                
                db_obj = FaceEncoding(
                    name=item["name"],
                    encoding=encoding_bytes
                )
                db.add(db_obj)
                count += 1
            
            db.commit()
            print(f"✓ Successfully saved {count} encodings to database")
            return True
            
        except Exception as e:
            print(f"Error saving to database: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def save_local_backup(self):
        """Save local backup for offline use"""
        output_path = self.models_dir / "encodings.pkl"
        
        names = [item["name"] for item in self.new_encodings]
        encodings = [item["encoding"] for item in self.new_encodings]
        
        data = {
            "encodings": encodings,
            "names": names
        }
        
        with open(output_path, "wb") as f:
            pickle.dump(data, f)
        print(f"✓ Local backup saved to: {output_path}")

    def train(self):
        """Main training function"""
        print("\n" + "="*60)
        print("Face Recognition - Model Training")
        print("="*60)
        
        # Ensure tables exist (helpful if running locally newly)
        init_db()
        
        # Load and process images
        if not self.process_images():
            return False
        
        # Save to Database
        if self.save_encodings_to_db():
             # Save local backup as well
            self.save_local_backup()
            
            print(f"\n{'='*60}")
            print("✓ Training completed successfully!")
            print(f"{'='*60}")
            print("\nEncodings are now in the database and accessible by the backend.")
            return True
        else:
            return False

def main():
    """Main function"""
    trainer = FaceTrainer()
    trainer.train()

if __name__ == "__main__":
    main()
