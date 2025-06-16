import os
import sys
import time
import io
import json
import logging
import numpy as np
import cv2
import trimesh
from PIL import Image

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("render.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---
MESH_DIR = "mesh_data"
RENDER_DIR = "renders"
os.makedirs(RENDER_DIR, exist_ok=True)

# --- Set headless OpenGL backend ---
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
logger.info("Set PYOPENGL_PLATFORM=osmesa")

logger.info("Starting rendering process")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Mesh directory: {MESH_DIR}")
logger.info(f"Render output directory: {RENDER_DIR}")

def simple_render(mesh_path, output_dir=RENDER_DIR):
    """Render a mesh with transparent background and save as PNG"""
    try:
        logger.info(f"Processing: {os.path.basename(mesh_path)}")

        # 1. Load the mesh
        start_time = time.time()
        mesh = trimesh.load(mesh_path, force='mesh')
        logger.info(f"Loaded mesh in {time.time() - start_time:.2f}s")
        logger.info(f"Mesh stats: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

        # 2. Normalize the mesh
        mesh.apply_translation(-mesh.centroid)
        scale = 1.0 / max(mesh.extents)
        mesh.apply_scale(scale)
        logger.info("Normalized mesh to unit size")

        # 3. Create scene with transparent background
        scene = trimesh.Scene(mesh)
        scene.camera.resolution = (1024, 768)
        scene.background = [0, 0, 0, 0]  # Transparent RGBA

        # 4. Set camera position
        scene.camera_transform = scene.camera.look_at(
            points=mesh.vertices,
            distance=2.0
        )

        # 5. Render the image
        start_render = time.time()
        png_data = scene.save_image(
            resolution=scene.camera.resolution,
            visible=False,
            timeout=60
        )
        logger.info(f"Rendered in {time.time() - start_render:.2f}s")

        # 6. Convert to RGBA and make black fully transparent
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        data = np.array(img)

        height, width = data.shape[:2]
        r = data[:, :, 0]
        g = data[:, :, 1]
        b = data[:, :, 2]
        a = data[:, :, 3]

        black_mask = (r == 0) & (g == 0) & (b == 0)
        a[black_mask] = 0
        data[:, :, 3] = a

        img = Image.fromarray(data)

        # 7. Save output image
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, os.path.basename(mesh_path).replace(".obj", ".png"))
        img.save(out_path)
        logger.info(f"Saved render: {out_path}")

        return True

    except Exception as e:
        logger.error(f"Failed to render {mesh_path}: {str(e)}")
        return False

# Alias for import
render_mesh = simple_render

def main():
    obj_files = [f for f in os.listdir(MESH_DIR) if f.lower().endswith('.obj')]
    if not obj_files:
        logger.error("No OBJ files found in mesh_data directory")
        return

    logger.info(f"Found {len(obj_files)} OBJ files")

    success_count = 0
    for i, obj_file in enumerate(obj_files):
        logger.info(f"\nProcessing file {i+1}/{len(obj_files)}")
        mesh_path = os.path.join(MESH_DIR, obj_file)
        if simple_render(mesh_path):
            success_count += 1

    logger.info(f"\nRendering complete! Success: {success_count}/{len(obj_files)}")
    logger.info(f"All renders saved in: {os.path.abspath(RENDER_DIR)}")

if __name__ == "__main__":
    try:
        # Check required packages
        import numpy
        import trimesh
        import PIL
        import cv2
        logger.info("All required packages are available")
        main()

    except ImportError as e:
        logger.error(f"Missing package: {str(e)}")
        logger.info("Installing missing packages...")
        os.system(f"{sys.executable} -m pip install numpy trimesh opencv-python Pillow")
        logger.info("Packages installed. Restarting script...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
