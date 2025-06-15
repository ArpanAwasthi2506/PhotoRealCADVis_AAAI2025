import os
import trimesh
import pyrender
import numpy as np
import cv2
from OCC.Display.SimpleGui import init_display
from OCC.Extend.DataExchange import read_step_file

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESH_DIR = os.path.join(BASE_DIR, '../mesh_data')
BREP_DIR = os.path.join(BASE_DIR, '../brep_data')
RENDER_DIR = os.path.join(BASE_DIR, '../renders')
BACKGROUND_DIR = os.path.join(BASE_DIR, '../backgrounds')
MATERIAL_DIR = os.path.join(BASE_DIR, '../materials')

os.makedirs(RENDER_DIR, exist_ok=True)
os.makedirs(BACKGROUND_DIR, exist_ok=True)

# Initialize renderer (works without GPU)
renderer = pyrender.OffscreenRenderer(1024, 768)

def render_mesh(mesh_path):
    """Render OBJ mesh with consistent coloring"""
    mesh = trimesh.load(mesh_path)
    mesh = pyrender.Mesh.from_trimesh(mesh)
    
    scene = pyrender.Scene(ambient_light=[0.2, 0.2, 0.2])
    scene.add(mesh)
    
    # Camera setup
    camera = pyrender.PerspectiveCamera(yfov=np.pi/3.0)
    camera_pose = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 1.5],
        [0, 0, 0, 1]
    ])
    scene.add(camera, pose=camera_pose)
    
    # Lighting
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
    scene.add(light, pose=camera_pose)
    
    # Render
    color, _ = renderer.render(scene)
    return color

def render_brep(brep_path):
    """Render B-Rep without mesh conversion"""
    # Initialize offscreen display
    display, _, _, _ = init_display()
    display.View.SetProj(0, 0, 1)  # Standard view direction
    
    shape = read_step_file(brep_path)
    display.DisplayShape(shape)
    display.FitAll()
    
    # Save to temporary file
    temp_path = os.path.join(RENDER_DIR, 'temp_brep.png')
    display.View.Dump(temp_path)
    display.Close()
    
    # Load and return image
    return cv2.imread(temp_path)

def add_background(foreground, background=None):
    """Composite foreground object onto background"""
    if background is None:
        # Create gradient background
        bg = np.zeros((foreground.shape[0], foreground.shape[1], 3), dtype=np.uint8)
        cv2.rectangle(bg, (0,0), (bg.shape[1], bg.shape[0]), (200,230,255), -1)
        cv2.rectangle(bg, (0,0), (bg.shape[1], bg.shape[0]//2), (180,220,255), -1)
    else:
        bg = cv2.resize(background, (foreground.shape[1], foreground.shape[0]))
    
    # Simple compositing - assumes foreground has alpha channel
    if foreground.shape[2] == 4:
        alpha = foreground[:,:,3:4]/255.0
        fg_rgb = foreground[:,:,:3]
        return (fg_rgb * alpha + bg * (1-alpha)).astype(np.uint8)
    else:
        return foreground

def process_dataset():
    """Main processing pipeline"""
    # Process mesh files
    for mesh_file in os.listdir(MESH_DIR):
        if mesh_file.endswith('.obj'):
            print(f"Rendering {mesh_file}...")
            mesh_path = os.path.join(MESH_DIR, mesh_file)
            render = render_mesh(mesh_path)
            composite = add_background(render)
            
            output_path = os.path.join(RENDER_DIR, f"{os.path.splitext(mesh_file)[0]}.png")
            cv2.imwrite(output_path, cv2.cvtColor(composite, cv2.COLOR_RGB2BGR))
    
    # Process B-Rep files
    for brep_file in os.listdir(BREP_DIR):
        if brep_file.endswith('.stp'):
            print(f"Rendering {brep_file}...")
            brep_path = os.path.join(BREP_DIR, brep_file)
            render = render_brep(brep_path)
            
            output_path = os.path.join(RENDER_DIR, f"{os.path.splitext(brep_file)[0]}.png")
            cv2.imwrite(output_path, render)

if __name__ == "__main__":
    process_dataset()
    print("Rendering complete! Check the renders directory.")
