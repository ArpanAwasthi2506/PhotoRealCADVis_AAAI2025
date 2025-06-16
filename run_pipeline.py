import os
import logging
import random  # ✅ Required for random material selection
import cv2     # ✅ Fix: Add OpenCV for reading composite images

from render_robust import simple_render as render_mesh
from backgrounds import generate_backgrounds
from compositor import main as composite_images
from dataset_manager import DatasetManager
from materials import load_materials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Configuration
    MESH_DIR = "mesh_data"
    BACKGROUND_DIR = "backgrounds"
    RENDER_DIR = "renders"
    COMPOSITE_DIR = "composites"
    DATASET_DIR = "dataset"

    # Create directories
    os.makedirs(BACKGROUND_DIR, exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)
    os.makedirs(COMPOSITE_DIR, exist_ok=True)
    os.makedirs(DATASET_DIR, exist_ok=True)

    # Step 1: Generate backgrounds
    logger.info("Generating backgrounds...")
    generate_backgrounds(BACKGROUND_DIR, num_backgrounds=10)

    # Step 2: Render CAD models
    logger.info("Rendering CAD models...")
    for file in os.listdir(MESH_DIR):
        if file.lower().endswith(('.obj', '.stp', '.step')):
            mesh_path = os.path.join(MESH_DIR, file)
            render_mesh(mesh_path, RENDER_DIR)

    # Step 3: Composite renders with backgrounds
    logger.info("Compositing images...")
    composite_images()

    # Step 4: Create dataset
    logger.info("Creating dataset...")
    dm = DatasetManager(DATASET_DIR)
    materials = load_materials()

    for comp_file in os.listdir(COMPOSITE_DIR):
        if comp_file.endswith('.jpg'):
            comp_path = os.path.join(COMPOSITE_DIR, comp_file)
            img = cv2.imread(comp_path)  # ✅ Fix applied here
            if img is None:
                logger.warning(f"Failed to load image: {comp_path}")
                continue
            material_name = random.choice(list(materials.keys()))
            dm.add_rendering(img, comp_path, "cad_model", material_name)

    dm.save_annotations()
    logger.info(f"✅ Dataset created with {len(dm.annotations)} samples")

if __name__ == "__main__":
    main()
