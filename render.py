import os
import cv2
import trimesh
import numpy as np
from PIL import Image
import io
import logging
from OCC.Display.SimpleGui import init_display
from OCC.Extend.DataExchange import read_step_file
from OCC.Core.Graphic3d import Graphic3d_RenderingParams, Graphic3d_RM_RAYTRACING

# Suppress noisy logs
logging.getLogger('trimesh').setLevel(logging.ERROR)
logging.getLogger('OCC').setLevel(logging.ERROR)

# === Paths and Directories ===
BASE_DIR = os.getcwd()
MESH_DIR = os.path.join(BASE_DIR, "mesh_data")
BREP_DIR = os.path.join(BASE_DIR, "brep_data")
RENDER_DIR = os.path.join(BASE_DIR, "renders")
os.makedirs(RENDER_DIR, exist_ok=True)

# === Force software rendering for compatibility ===
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['GALLIUM_DRIVER'] = 'llvmpipe'

# === Camera system for multiple views ===
class CameraSystem:
    def __init__(self, resolution=(1024, 768)):
        self.resolution = resolution
        self.positions = [
            (0, 0, 1.5),     # Front
            (1.5, 0, 1.5),   # Front-right
            (0, 1.5, 1.5),   # Front-top
            (-1.5, 0, 1.5),  # Front-left
            (0, -1.5, 1.5),  # Front-bottom
            (0, 0, -1.5)     # Back
        ]

    def get_view_matrix(self, index):
        eye = np.array(self.positions[index])
        target = np.array([0, 0, 0])
        up = np.array([0, 1, 0])
        
        f = (target - eye)
        f /= np.linalg.norm(f)
        s = np.cross(f, up)
        s /= np.linalg.norm(s)
        u = np.cross(s, f)

        view = np.eye(4)
        view[0, :3] = s
        view[1, :3] = u
        view[2, :3] = -f
        view[:3, 3] = -view[:3, :3] @ eye
        return view

    def render_multiview(self, mesh_path, output_dir):
        mesh = trimesh.load(mesh_path)
        for i in range(len(self.positions)):
            scene = mesh.scene()
            scene.camera_transform = self.get_view_matrix(i)
            scene.camera.resolution = self.resolution
            png = scene.save_image(visible=False)
            img = Image.open(io.BytesIO(png))
            out_name = f"{os.path.splitext(os.path.basename(mesh_path))[0]}_view{i}.png"
            img.save(os.path.join(output_dir, out_name))


def render_mesh(mesh_path):
    """Single-view mesh rendering using trimesh."""
    try:
        mesh = trimesh.load(mesh_path)
        scene = mesh.scene()
        scene.camera.resolution = (1024, 768)
        scene.camera.fov = (60, 45)
        png = scene.save_image(resolution=scene.camera.resolution, visible=False)
        img = Image.open(io.BytesIO(png))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error rendering mesh {mesh_path}: {str(e)}")
        return None


def render_brep(brep_path):
    """High-quality raytraced B-Rep rendering using PythonOCC."""
    try:
        display, _, _, _ = init_display("headless", size=(1024, 768))
        display.View.SetRaytracingMode(True)
        display.View.SetRaytracingShadows(True)
        display.View.SetRaytracingReflections(True)
        display.View.SetRaytracingAmbientOcclusion(True)

        params = display.View.GetRenderingParams()
        params.Method = Graphic3d_RM_RAYTRACING
        params.RaytracingDepth = 4
        params.IsAntialiasingEnabled = True
        params.NbMsaaSamples = 4
        display.View.SetRenderingParams(params)

        shape = read_step_file(brep_path)
        display.DisplayShape(shape, update=True)
        display.FitAll()

        env_path = os.path.join(BASE_DIR, "textures", "environment.hdr")
        if os.path.exists(env_path):
            display.View.SetEnvironmentMap(env_path, True)

        temp_path = os.path.join(RENDER_DIR, f"temp_brep_{os.path.basename(brep_path)}.png")
        display.View.Dump(temp_path)
        display.EraseAll()
        display.Close()

        img = cv2.imread(temp_path)
        os.remove(temp_path)
        img = np.clip(img**0.7, 0, 255).astype(np.uint8)
        return img
    except Exception as e:
        print(f"Error rendering B-Rep {brep_path}: {str(e)}")
        return None


def process_dataset():
    print("Starting rendering pipeline...\n")

    cam = CameraSystem()

    mesh_files = [f for f in os.listdir(MESH_DIR) if f.lower().endswith('.obj')]
    print(f"Found {len(mesh_files)} mesh files")

    for i, file in enumerate(mesh_files):
        print(f"Rendering mesh {i+1}/{len(mesh_files)}: {file}")
        mesh_path = os.path.join(MESH_DIR, file)
        
        # Single-view render
        img = render_mesh(mesh_path)
        if img is not None:
            cv2.imwrite(os.path.join(RENDER_DIR, f"{os.path.splitext(file)[0]}.png"), img)

        # Multi-view render
        cam.render_multiview(mesh_path, RENDER_DIR)

    brep_files = [f for f in os.listdir(BREP_DIR) if f.lower().endswith(('.stp', '.step'))]
    print(f"\nFound {len(brep_files)} B-Rep files")

    for i, file in enumerate(brep_files):
        print(f"Rendering B-Rep {i+1}/{len(brep_files)}: {file}")
        brep_path = os.path.join(BREP_DIR, file)
        img = render_brep(brep_path)
        if img is not None:
            cv2.imwrite(os.path.join(RENDER_DIR, f"{os.path.splitext(file)[0]}.png"), img)

    print("\nRendering completed! Check the 'renders' directory.")
# In render.py after rendering:
from dataset_manager import DatasetManager

dm = DatasetManager("dataset")
for img_file in os.listdir(RENDER_DIR):
    img = cv2.imread(os.path.join(RENDER_DIR, img_file))
    dm.add_rendering(img, img_file, "mesh")
dm.save_annotations()

if __name__ == "__main__":
    process_dataset()
