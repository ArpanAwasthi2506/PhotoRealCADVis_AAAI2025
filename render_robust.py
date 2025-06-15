import os
import sys
import logging
import time
import cv2
import numpy as np
import trimesh
from PIL import Image
import io

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("render.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
MESH_DIR = "mesh_data"
RENDER_DIR = "renders"
os.makedirs(RENDER_DIR, exist_ok=True)

logger.info("Starting rendering process")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Mesh directory: {MESH_DIR}")
logger.info(f"Render output directory: {RENDER_DIR}")

# Software rendering configuration
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
logger.info("Set PYOPENGL_PLATFORM=osmesa")

def simple_render(mesh_path):
    """Simplified but robust rendering function"""
    try:
        logger.info(f"Processing: {os.path.basename(mesh_path)}")
        
        # 1. Load the mesh
        start_time = time.time()
        mesh = trimesh.load(mesh_path, force='mesh')
        logger.info(f"Loaded mesh in {time.time()-start_time:.2f}s")
        logger.info(f"Mesh stats: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        
        # 2. Center and scale the mesh
        mesh.apply_translation(-mesh.centroid)
        scale = 1.0 / max(mesh.extents)
        mesh.apply_scale(scale)
        logger.info(f"Normalized mesh")
        
        # 3. Create a scene with basic lighting
        scene = trimesh.Scene(mesh)
        scene.camera.resolution = (1024, 768)
        
        # 4. Set camera position to ensure visibility
        scene.camera_transform = scene.camera.look_at(
            points=mesh.vertices,
            distance=2.0
        )
        
        # 5. Render with increased timeout
        start_render = time.time()
        png_data = scene.save_image(resolution=scene.camera.resolution, 
                                   visible=False, 
                                   timeout=60)
        logger.info(f"Rendered in {time.time()-start_render:.2f}s")
        
        # 6. Convert to OpenCV format
        img = Image.open(io.BytesIO(png_data))
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # 7. Save the image
        output_path = os.path.join(RENDER_DIR, os.path.basename(mesh_path).replace('.obj', '.png'))
        cv2.imwrite(output_path, img_cv)
        logger.info(f"Saved render: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to render {mesh_path}: {str(e)}")
        return False

def main():
    # Get all OBJ files
    obj_files = [f for f in os.listdir(MESH_DIR) if f.lower().endswith('.obj')]
    
    if not obj_files:
        logger.error("No OBJ files found in mesh_data directory")
        return
    
    logger.info(f"Found {len(obj_files)} OBJ files to process")
    
    # Process each file
    success_count = 0
    for i, obj_file in enumerate(obj_files):
        logger.info(f"\nProcessing file {i+1}/{len(obj_files)}")
        mesh_path = os.path.join(MESH_DIR, obj_file)
        
        if simple_render(mesh_path):
            success_count += 1
    
    logger.info(f"\nRendering complete! Success: {success_count}/{len(obj_files)}")
    logger.info(f"Output saved to: {os.path.abspath(RENDER_DIR)}")

if __name__ == "__main__":
    try:
        # Verify essential packages
        import numpy
        import trimesh
        import cv2
        import PIL
        logger.info("All required packages are available")
        
        main()
    except ImportError as e:
        logger.error(f"Missing package: {str(e)}")
        logger.info("Attempting to install required packages...")
        os.system(f"{sys.executable} -m pip install numpy trimesh opencv-python Pillow")
        logger.info("Packages installed, restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
