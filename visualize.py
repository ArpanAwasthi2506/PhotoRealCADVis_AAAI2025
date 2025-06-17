#!/usr/bin/env python
"""
CAD Visualization & Rendering Tool
=================================

Features:
- STEP/PLY visualization
- Photorealistic rendering with materials
- Procedural backgrounds
- Camera parameter control
- Image saving capability
"""

import os
import sys
import argparse
import tempfile
import logging
import numpy as np
import trimesh
from pathlib import Path
from PIL import Image
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
import random

# Configure logging
logger = logging.getLogger('CAD Visualizer')

def setup_logging(debug=False):
    """Configure logging level"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

class Renderer:
    """Photorealistic rendering system with material support"""
    def __init__(self):
        self.materials = {
            'metal': {
                'ambient': 0.2,
                'diffuse': 0.7,
                'specular': 1.0,
                'roughness': 0.3,
                'metallic': 1.0,
                'baseColorFactor': [0.8, 0.8, 0.8, 1.0]
            },
            'plastic': {
                'ambient': 0.3,
                'diffuse': 0.9,
                'specular': 0.5,
                'roughness': 0.4,
                'metallic': 0.0,
                'baseColorFactor': [0.9, 0.1, 0.1, 1.0]
            },
            'ceramic': {
                'ambient': 0.4,
                'diffuse': 0.6,
                'specular': 0.8,
                'roughness': 0.2,
                'metallic': 0.1,
                'baseColorFactor': [0.95, 0.95, 0.95, 1.0]
            }
        }
        self.default_material = 'plastic'
        self.camera_presets = [
            {'position': [0, -2, 1], 'target': [0, 0, 0]},
            {'position': [-2, 0, 1], 'target': [0, 0, 0]},
            {'position': [0, 0, 2], 'target': [0, 0, 0]},
            {'position': [-1, -1, 1], 'target': [0, 0, 0]},
        ]

    def create_gradient_background(self, top_color, bottom_color, resolution=(1920, 1080)):
        img = Image.new('RGB', resolution)
        pixels = img.load()
        for y in range(resolution[1]):
            ratio = y / resolution[1]
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            for x in range(resolution[0]):
                pixels[x, y] = (r, g, b)
        return img

    def get_random_background(self, resolution=(1920, 1080)):
        gradients = [
            ((70, 130, 180), (135, 206, 250)),
            ((50, 50, 50), (100, 100, 100)),
            ((255, 100, 0), (255, 200, 50)),
            ((30, 60, 30), (100, 150, 100))
        ]
        top, bottom = random.choice(gradients)
        return self.create_gradient_background(top, bottom, resolution)

    def apply_material(self, mesh, material_name=None):
        material = self.materials.get(material_name or self.default_material, self.materials[self.default_material])
        if not hasattr(mesh.visual, 'material'):
            mesh.visual.material = trimesh.visual.material.PBRMaterial()
        for prop, value in material.items():
            if hasattr(mesh.visual.material, prop):
                setattr(mesh.visual.material, prop, value)

    def get_random_camera(self):
        return random.choice(self.camera_presets)

    def render_scene(self, mesh, resolution=(1920, 1080)):
        try:
            scene = trimesh.Scene()
            scene.add_geometry(mesh)
            camera = self.get_random_camera()
            scene.camera_transform = scene.camera.look_at(
                points=camera['target'],
                eye=camera['position']
            )
            scene.background = self.get_random_background(resolution)
            image = scene.save_image(resolution=resolution)
            return Image.frombytes('RGB', resolution, image)
        except Exception as e:
            logger.error(f"Rendering failed: {str(e)}")
            return None

def visualize_with_plotly(mesh):
    try:
        if isinstance(mesh, trimesh.PointCloud):
            points = mesh.vertices
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Scatter3d(
                x=points[:, 0], y=points[:, 1], z=points[:, 2],
                mode='markers', marker=dict(size=2)
            )])
        else:
            x, y, z = mesh.vertices.T
            i, j, k = mesh.faces.T
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                opacity=0.5
            )])
        fig.show()
        return True
    except Exception as e:
        logger.error(f"Plotly visualization failed: {e}")
        return False

def convert_step_to_stl(step_path, stl_path):
    try:
        logger.info(f"Converting STEP to STL: {step_path}")
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(step_path))
        if status != IFSelect_RetDone:
            raise ValueError(f"STEP file read failed with status: {status}")
        reader.TransferRoots()
        shape = reader.Shape(1)
        mesh = BRepMesh_IncrementalMesh(shape, 0.01)
        mesh.Perform()
        writer = StlAPI_Writer()
        writer.Write(shape, str(stl_path))
        logger.info(f"Conversion successful: {stl_path}")
        return True
    except Exception as e:
        logger.error(f"STEP conversion error: {str(e)}")
        return False

def visualize_step(file_path, renderer=None, output_image=None, material=None):
    try:
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp_file:
            stl_path = Path(tmp_file.name)
        if not convert_step_to_stl(file_path, stl_path):
            return False
        mesh = trimesh.load(stl_path)
        if renderer and material:
            renderer.apply_material(mesh, material)
        if output_image and renderer:
            logger.info(f"Rendering image: {output_image}")
            img = renderer.render_scene(mesh)
            if img:
                img.save(output_image)
                logger.info(f"Saved rendered image to: {output_image}")
                return True
            return False
        # ✅ Use Plotly instead of Pyglet
        return visualize_with_plotly(mesh)
    except Exception as e:
        logger.error(f"STEP visualization error: {str(e)}")
        return False
    finally:
        if stl_path.exists():
            logger.info(f"Cleaning up temporary file: {stl_path}")
            os.unlink(stl_path)

def visualize_mesh(file_path, renderer=None, output_image=None, material=None):
    try:
        logger.info(f"Loading file: {file_path}")
        mesh = trimesh.load(file_path)
        if renderer and material:
            renderer.apply_material(mesh, material)
        if output_image and renderer:
            logger.info(f"Rendering image: {output_image}")
            img = renderer.render_scene(mesh)
            if img:
                img.save(output_image)
                logger.info(f"Saved rendered image to: {output_image}")
                return True
            return False
        # ✅ Use Plotly instead of Pyglet
        return visualize_with_plotly(mesh)
    except Exception as e:
        logger.error(f"Error visualizing file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="CAD Visualization & Rendering Tool")
    parser.add_argument("file_path", help="Path to CAD file (STEP or PLY)")
    parser.add_argument("--output", "-o", help="Path to save rendered image")
    parser.add_argument("--material", choices=['metal', 'plastic', 'ceramic'], default='plastic', help="Material for rendering")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    renderer = Renderer() if args.output else None
    if file_path.suffix.lower() in [".step", ".stp"]:
        logger.info(f"Processing STEP file: {file_path.name}")
        success = visualize_step(file_path, renderer=renderer, output_image=args.output, material=args.material)
    elif file_path.suffix.lower() in [".ply", ".obj"]:
        logger.info(f"Processing mesh file: {file_path.name}")
        success = visualize_mesh(file_path, renderer=renderer, output_image=args.output, material=args.material)
    else:
        logger.error(f"Unsupported file format: {file_path.suffix}")
        sys.exit(1)

    if success:
        logger.info("Operation completed successfully!")
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
