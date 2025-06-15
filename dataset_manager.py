import os
import json
import cv2
from datetime import datetime

class DatasetManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.structure = {
            "images": "images",
            "annotations": "annotations",
            "meshes": "meshes",
            "breps": "breps",
            "materials": "materials",
            "backgrounds": "backgrounds"
        }
        self.create_structure()
        self.annotations = []
        self.counter = 0
    
    def create_structure(self):
        """Create dataset directory structure"""
        for path in self.structure.values():
            os.makedirs(os.path.join(self.base_dir, path), exist_ok=True)
    
    def add_rendering(self, image, source_file, obj_type, material=None):
        """Add a rendered image to the dataset"""
        # Save image
        img_name = f"render_{self.counter:06d}.jpg"
        img_path = os.path.join(self.base_dir, self.structure["images"], img_name)
        cv2.imwrite(img_path, image)
        
        # Create annotation
        annotation = {
            "id": self.counter,
            "file_name": img_name,
            "source_file": os.path.basename(source_file),
            "type": obj_type,
            "material": material,
            "timestamp": datetime.now().isoformat()
        }
        self.annotations.append(annotation)
        self.counter += 1
        return annotation
    
    def save_annotations(self):
        """Save annotations to JSON file"""
        anno_path = os.path.join(self.base_dir, self.structure["annotations"], "dataset.json")
        with open(anno_path, "w") as f:
            json.dump({
                "info": {
                    "description": "CAD Rendering Dataset",
                    "created": datetime.now().isoformat()
                },
                "images": self.annotations
            }, f, indent=2)
        return anno_path
