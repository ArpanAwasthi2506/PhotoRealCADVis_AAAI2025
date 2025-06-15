import os
import numpy as np
import cv2
import trimesh
from OCC.Display.SimpleGui import init_display
from OCC.Extend.DataExchange import read_step_file
from OCC.Core.Graphic3d import Graphic3d_RenderingParams, Graphic3d_RM_RAYTRACING
from PIL import Image
import io

# Configuration
MESH_DIR = "mesh_data"
BREP_DIR = "brep_data"
RENDER_DIR = "renders"
os.makedirs(RENDER_DIR, exist_ok=True)

# Set software rendering flags
os.environ['PYTHONOCC_OFFSCREEN_RENDERER'] = '1'
os.environ['PYTHONOCC_HEADLESS'] = '1'

def render_mesh(mesh_path):
    """Render OBJ using trimesh's software rasterizer"""
    try:
        mesh = trimesh.load(mesh_path)
        scene = mesh.scene()
        
        # Set camera parameters
        scene.camera.resolution = (1024, 768)
        scene.camera.fov = (60, 45)
        
        # Render using software rasterizer
        png = scene.save_image(resolution=scene.camera.resolution, visible=False)
        img = Image.open(io.BytesIO(png))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error rendering mesh: {str(e)}")
        return None

def render_brep(brep_path):
    """Render STEP file using PythonOCC's headless raytracing"""
    try:
        # Initialize headless display
        display, _, _, _ = init_display("headless")
        display.View.SetRaytracingMode(True)
        
        # Load and display shape
        shape = read_step_file(brep_path)
        display.DisplayShape(shape, update=True)
        display.FitAll()
        
        # Configure rendering quality
        render_params = display.View.GetRenderingParams()
        render_params.Method = Graphic3d_RM_RAYTRACING
        render_params.IsShadowEnabled = True
        render_params.IsReflectionEnabled = True
        render_params.RaytracingDepth = 3
        display.View.SetRenderingParams(render_params)
        
        # Save to temporary image
        temp_path = os.path.join(RENDER_DIR, "temp_brep.png")
        display.View.Dump(temp_path)
        display.EraseAll()
        
        # Read and return image
        img = cv2.imread(temp_path)
        os.remove(temp_path)
        return img
    except Exception as e:
        print(f"Error rendering B-Rep: {str(e)}")
        return None

def process_dataset():
    """Main rendering pipeline"""
    # Render mesh files
    for i, file in enumerate(os.listdir(MESH_DIR)):
        if file.lower().endswith('.obj'):
            print(f"Rendering mesh {i+1}: {file}")
            mesh_path = os.path.join(MESH_DIR, file)
            img = render_mesh(mesh_path)
            if img is not None:
                output_path = os.path.join(RENDER_DIR, f"{os.path.splitext(file)[0]}.png")
                cv2.imwrite(output_path, img)
    
    # Render B-Rep files
    for i, file in enumerate(os.listdir(BREP_DIR)):
        if file.lower().endswith(('.stp', '.step')):
            print(f"Rendering B-Rep {i+1}: {file}")
            brep_path = os.path.join(BREP_DIR, file)
            img = render_brep(brep_path)
            if img is not None:
                output_path = os.path.join(RENDER_DIR, f"{os.path.splitext(file)[0]}.png")
                cv2.imwrite(output_path, img)

if __name__ == "__main__":
    print("Starting rendering pipeline...")
    process_dataset()
    print("Rendering completed! Check the 'renders' directory.")
