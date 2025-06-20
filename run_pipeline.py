import os
import logging
import random
import cv2
import trimesh
import json  # ✅ Fix: Required for camera metadata
os.environ['PYOPENGL_PLATFORM'] = 'egl'  # Use EGL for headless rendering

# Custom modules
from render_robust import simple_render as render_mesh
from backgrounds import generate_backgrounds
from compositor import main as composite_images
from dataset_manager import DatasetManager
from materials import load_materials
from camera import CameraSystem

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # --- Configuration ---
    MESH_DIR = "mesh_data"
    BACKGROUND_DIR = "backgrounds"
    RENDER_DIR = "renders"
    COMPOSITE_DIR = "composites"
    DATASET_DIR = "dataset"

    # --- Ensure required directories exist ---
    os.makedirs(BACKGROUND_DIR, exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)
    os.makedirs(COMPOSITE_DIR, exist_ok=True)
    os.makedirs(DATASET_DIR, exist_ok=True)

    # Step 1: Generate AI backgrounds
    logger.info("Step 1: Generating backgrounds...")
    generate_backgrounds(BACKGROUND_DIR, num_backgrounds=10)

    # Step 2: Render CAD models with camera metadata
    logger.info("Step 2: Rendering CAD models with camera metadata...")
    camera_system = CameraSystem()
    for file in os.listdir(MESH_DIR):
        if file.lower().endswith(('.obj', '.stp', '.step')):
            mesh_path = os.path.join(MESH_DIR, file)
            try:
                mesh = trimesh.load(mesh_path)
                base_name = os.path.splitext(file)[0]
                logger.info(f"Rendering mesh: {file}")

                # Render mesh with metadata
                camera_system.render_with_metadata(
                    mesh,
                    RENDER_DIR,
                    base_name
                )
            except Exception as e:
                logger.error(f"Failed to render {file}: {str(e)}")
                continue

    # Step 3: Composite renders with backgrounds
    logger.info("Step 3: Compositing images...")
    try:
        composite_images()
    except Exception as e:
        logger.error(f"Compositing failed: {str(e)}")

    # Step 4: Build final dataset with materials
    logger.info("Step 4: Creating dataset...")
    try:
        dm = DatasetManager(DATASET_DIR)
        materials = load_materials()

        for comp_file in os.listdir(COMPOSITE_DIR):
            if comp_file.endswith('.jpg'):
                comp_path = os.path.join(COMPOSITE_DIR, comp_file)
                img = cv2.imread(comp_path)
                if img is None:
                    logger.warning(f"Failed to load composite image: {comp_path}")
                    continue
                material_name = random.choice(list(materials.keys()))
                dm.add_rendering(img, comp_path, "cad_model", material_name)

        dm.save_annotations()
        logger.info(f"✅ Dataset created with {len(dm.annotations)} samples")
    except Exception as e:
        logger.error(f"Dataset creation failed: {str(e)}")

if __name__ == "__main__":
    main()
