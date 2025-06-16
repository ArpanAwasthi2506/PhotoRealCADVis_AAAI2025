import os
import cv2
import io
import random
import numpy as np
import trimesh
from PIL import Image

from render_robust import render_mesh
from backgrounds import generate_backgrounds, composite_object
from materials import apply_material, load_materials
from camera import CameraSystem
from dataset_manager import DatasetManager
import git_manager

def main():
    # --- Configuration ---
    MESH_DIR = "mesh_data"
    BACKGROUND_DIR = "backgrounds"
    RENDER_DIR = "renders"
    DATASET_DIR = "dataset"

    os.makedirs(RENDER_DIR, exist_ok=True)
    os.makedirs(BACKGROUND_DIR, exist_ok=True)

    # Initialize dataset manager
    dm = DatasetManager(DATASET_DIR)

    # Generate backgrounds if not present
    if not os.listdir(BACKGROUND_DIR):
        print("No backgrounds found. Generating new backgrounds...")
        generate_backgrounds(BACKGROUND_DIR, num_backgrounds=10)

    # Load material names
    materials = list(load_materials().keys())

    # Initialize camera system
    camera = CameraSystem()

    # Collect all mesh files
    mesh_files = [f for f in os.listdir(MESH_DIR) if f.lower().endswith(".obj")]
    print(f"Found {len(mesh_files)} mesh files")

    for i, file in enumerate(mesh_files):
        mesh_path = os.path.join(MESH_DIR, file)
        print(f"Processing {i+1}/{len(mesh_files)}: {file}")

        # Load and apply material
        material_name = random.choice(materials)
        try:
            mesh = trimesh.load(mesh_path)
            mesh = apply_material(mesh, material_name)
        except Exception as e:
            print(f"Failed to load/apply material to {file}: {e}")
            continue

        # Render from multiple camera views
        for view_idx in range(len(camera.positions)):
            try:
                # Create scene and render image
                scene = trimesh.Scene()
                scene.add_geometry(mesh)
                scene.camera_transform = camera.get_view_matrix(view_idx)
                scene.camera.resolution = camera.resolution

                png = scene.save_image(visible=False)
                img = np.array(Image.open(io.BytesIO(png)))
                render = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                # Select random background
                bg_files = os.listdir(BACKGROUND_DIR)
                bg_path = os.path.join(BACKGROUND_DIR, random.choice(bg_files)) if bg_files else None

                # Composite
                composite = composite_object(render, bg_path)

                # Save render to disk
                render_filename = f"{os.path.splitext(file)[0]}_v{view_idx:02d}.png"
                render_path = os.path.join(RENDER_DIR, render_filename)
                cv2.imwrite(render_path, composite)

                # Add to dataset
                dm.add_rendering(
                    composite,
                    mesh_path,
                    "mesh",
                    material=material_name,
                    background=bg_path,
                    view=view_idx
                )

            except Exception as e:
                print(f"View {view_idx} failed for {file}: {e}")
                continue

    # Save annotations
    dm.save_annotations()
    print(f"Dataset created with {dm.counter} images")

    # Commit and push to GitHub
    print("Updating GitHub repository...")
    git_manager.git_setup("git@github.com:saali14/PhotoRealCADVis_AAAI2025.git")
    git_manager.git_commit("Complete pipeline with dataset")
    git_manager.git_push()

if __name__ == "__main__":
    main()
