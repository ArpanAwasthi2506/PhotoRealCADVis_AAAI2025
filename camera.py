import numpy as np
import trimesh

class CameraSystem:
    def __init__(self, resolution=(1024, 768)):
        self.resolution = resolution
        self.positions = [
            (0, 0, 2.5),     # Front
            (2.0, 0, 1.5),    # Front-right
            (0, 2.0, 1.5),    # Front-top
            (-2.0, 0, 1.5),   # Front-left
            (0, -2.0, 1.5),   # Front-bottom
            (0, 0, -2.5)      # Back
        ]
        self.angles = [
            (0, 0, 0),        # Front
            (0, 30, 0),       # Front-right
            (-30, 0, 0),      # Front-top
            (0, -30, 0),      # Front-left
            (30, 0, 0),       # Front-bottom
            (0, 180, 0)       # Back
        ]
    
    def get_view_matrix(self, index):
        """Get camera view matrix for a viewpoint"""
        eye = np.array(self.positions[index])
        target = np.array([0, 0, 0])
        up = np.array([0, 1, 0])
        
        # Calculate view matrix
        f = (target - eye) / np.linalg.norm(target - eye)
        s = np.cross(f, up)
        s /= np.linalg.norm(s)
        u = np.cross(s, f)
        
        return np.array([
            [s[0], u[0], -f[0], 0],
            [s[1], u[1], -f[1], 0],
            [s[2], u[2], -f[2], 0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1]
        ])
    
    def render_multiview(self, mesh, output_dir, base_name):
        """Render object from multiple viewpoints"""
        scene = trimesh.Scene()
        scene.add_geometry(mesh)
        scene.camera.resolution = self.resolution
        
        for i in range(len(self.positions)):
            # Set camera transform
            scene.camera_transform = self.get_view_matrix(i)
            
            # Render
            png = scene.save_image(visible=False)
            img = Image.open(io.BytesIO(png))
            output_path = os.path.join(output_dir, f"{base_name}_view{i}.png")
            img.save(output_path)
