import os
import cv2
import numpy as np
import trimesh
import pyglet
from pyglet.gl import GL_DEPTH_TEST, glEnable, glDisable
from OCC.Display.SimpleGui import init_display
from OCC.Extend.DataExchange import read_step_file
from PIL import Image
import io
import logging
import time
import pymeshfix

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Configuration
MESH_DIR = "mesh_data"
BREP_DIR = "brep_data"
RENDER_DIR = "renders"
os.makedirs(RENDER_DIR, exist_ok=True)

# Force pure software rendering
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['GALLIUM_DRIVER'] = 'llvmpipe'

def repair_mesh(mesh):
    """Repair mesh geometry using pymeshfix"""
    try:
        # Convert to pymeshfix object
        fix = pymeshfix.MeshFix(mesh.vertices, mesh.faces)
        
        # Repair holes and self-intersections
        fix.repair(joincomp=True, remove_smallest_components=False)
        
        # Get repaired mesh
        vclean, fclean = fix.v, fix.f
        
        # Create new trimesh object
        return trimesh.Trimesh(vertices=vclean, faces=fclean)
    except Exception as e:
        logger.error(f"Mesh repair failed: {str(e)}")
        return mesh

def normalize_mesh(mesh):
    """Center and scale mesh to fit in unit cube with validation"""
    try:
        # Handle invalid meshes
        if not hasattr(mesh, 'vertices') or len(mesh.vertices) < 3:
            logger.warning("Invalid mesh - no vertices")
            return None
            
        # Center mesh at origin
        centroid = mesh.centroid
        mesh.vertices -= centroid
        
        # Scale to fit in unit cube
        max_dim = max(mesh.extents) or 1.0  # Handle zero extents
        if max_dim < 1e-6:  # Near-zero dimension
            logger.warning("Mesh has near-zero extents")
            return None
        mesh.vertices /= max_dim
        
        return mesh
    except Exception as e:
        logger.error(f"Normalization failed: {str(e)}")
        return None

def render_mesh(mesh_path):
    """Robust mesh rendering with multiple fallback strategies"""
    try:
        # Load mesh with error tolerance
        mesh = trimesh.load(mesh_path, process=False, maintain_order=True, force='mesh')
        
        # Skip if mesh is invalid
        if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
            logger.warning(f"Empty mesh: {mesh_path}")
            return None
            
        # Repair mesh if needed
        if not mesh.is_watertight or mesh.is_empty:
            logger.info(f"Repairing mesh: {mesh_path}")
            mesh = repair_mesh(mesh)
            
        # Normalize mesh
        mesh = normalize_mesh(mesh)
        if mesh is None:
            return None
            
        # Create scene with enhanced lighting
        scene = trimesh.Scene()
        scene.add_geometry(mesh)
        
        # Add directional lights from multiple angles
        directions = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        for direction in directions:
            scene.add_light(trimesh.scene.lighting.DirectionalLight(
                direction=direction,
                color=[1.0, 1.0, 1.0],
                intensity=0.5
            ))
        
        # Set camera to ensure object is visible
        scene.camera_transform = scene.camera.look_at(
            points=mesh.vertices,
            rotation=trimesh.transformations.euler_matrix(np.pi/4, np.pi/4, 0),
            distance=2.5
        )
        
        # Set resolution and FOV
        scene.camera.resolution = (1024, 768)
        scene.camera.fov = (60, 45)
        
        # Render with increased timeout
        try:
            png = scene.save_image(resolution=scene.camera.resolution, 
                                  visible=False, 
                                  timeout=60)
        except Exception as render_error:
            logger.warning(f"Standard render failed: {str(render_error)}")
            # Fallback to pyglet software renderer
            return render_with_pyglet(mesh)
        
        # Convert to OpenCV format
        img = Image.open(io.BytesIO(png))
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Check if image is mostly white
        if np.mean(img_cv) > 240:  # Almost white
            logger.warning(f"Rendered image is mostly white: {mesh_path}")
            # Try alternative renderer
            return render_with_pyglet(mesh)
        
        return img_cv
    except Exception as e:
        logger.error(f"Error rendering mesh {mesh_path}: {str(e)}")
        return None

def render_with_pyglet(mesh):
    """Fallback rendering using pyglet software renderer"""
    try:
        from pyglet import gl
        
        # Create a window with pyglet
        window = pyglet.window.Window(1024, 768, visible=False)
        window.set_visible(visible=False)
        
        # Set up projection
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(60, 1024/768, 0.1, 100)
        
        # Set up modelview
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.gluLookAt(0, 0, 3, 0, 0, 0, 0, 1, 0)
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Draw the mesh
        @window.event
        def on_draw():
            window.clear()
            gl.glColor3f(0.8, 0.8, 0.8)  # Default color
            mesh.show()
        
        # Capture the screen
        pyglet.image.get_buffer_manager().get_color_buffer().save('temp_pyglet.png')
        window.close()
        
        # Load and return image
        img = cv2.imread('temp_pyglet.png')
        os.remove('temp_pyglet.png')
        return img
        
    except Exception as e:
        logger.error(f"Pyglet render failed: {str(e)}")
        return None

def process_dataset():
    """Main rendering pipeline with comprehensive logging"""
    logger.info("Starting rendering pipeline...")
    
    # Render mesh files
    mesh_files = [f for f in os.listdir(MESH_DIR) if f.lower().endswith('.obj')]
    logger.info(f"Found {len(mesh_files)} mesh files")
    
    successful = 0
    for i, file in enumerate(mesh_files):
        mesh_path = os.path.join(MESH_DIR, file)
        logger.info(f"Rendering mesh {i+1}/{len(mesh_files)}: {file}")
        
        img = render_mesh(mesh_path)
        if img is not None:
            output_path = os.path.join(RENDER_DIR, f"{os.path.splitext(file)[0]}.png")
            cv2.imwrite(output_path, img)
            successful += 1
            logger.info(f"Saved render: {output_path}")
        else:
            logger.warning(f"Skipped render for: {file}")
    
    logger.info(f"Rendering completed! Success rate: {successful}/{len(mesh_files)}")
    logger.info(f"Check the 'renders' directory.")

if __name__ == "__main__":
    # Install mesh repair dependency if needed
    try:
        import pymeshfix
    except ImportError:
        logger.info("Installing pymeshfix...")
        import subprocess
        subprocess.run(["pip", "install", "pymeshfix"])
        import pymeshfix
        
    process_dataset()
