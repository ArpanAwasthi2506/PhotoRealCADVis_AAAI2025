import os
import json
import numpy as np
import trimesh  # ✅ Required for mesh operations

MATERIAL_DIR = "materials"
os.makedirs(MATERIAL_DIR, exist_ok=True)

# Updated materials with additional options
DEFAULT_MATERIALS = {
    "metal": {
        "type": "phong",
        "diffuse": [0.6, 0.6, 0.6],
        "specular": [0.8, 0.8, 0.8],
        "shininess": 100,
        "texture": "metal_brushed.jpg"
    },
    "plastic": {
        "type": "lambert",
        "diffuse": [0.8, 0.8, 0.8],
        "specular": [0.1, 0.1, 0.1],
        "shininess": 20
    },
    "rubber": {
        "type": "lambert",
        "diffuse": [0.1, 0.1, 0.1],
        "roughness": 0.9
    },
    "brushed_metal": {
        "type": "phong",
        "diffuse": [0.55, 0.55, 0.55],
        "specular": [0.8, 0.8, 0.8],
        "shininess": 120,
        "texture": "brushed_metal.jpg"
    },
    "matte_plastic": {
        "type": "lambert",
        "diffuse": [0.85, 0.85, 0.85],
        "specular": [0.1, 0.1, 0.1],
        "shininess": 30
    }
}

def save_materials(materials):
    """Save materials to JSON file"""
    with open(os.path.join(MATERIAL_DIR, "materials.json"), "w") as f:
        json.dump(materials, f, indent=2)

def load_materials():
    """Load materials from file or create default"""
    path = os.path.join(MATERIAL_DIR, "materials.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    save_materials(DEFAULT_MATERIALS)
    return DEFAULT_MATERIALS

def apply_material(mesh, material_name):
    """Apply simple visual color to a trimesh object"""
    materials = load_materials()
    material = materials.get(material_name, materials["metal"])
    diffuse = material.get("diffuse", [1, 1, 1])
    
    # Apply vertex color uniformly
    color_array = np.tile((np.array(diffuse) * 255).astype(np.uint8), (len(mesh.vertices), 1))
    mesh.visual.vertex_colors = color_array

    return mesh
