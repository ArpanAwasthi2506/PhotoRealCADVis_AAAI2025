import os
import json
import numpy as np

MATERIAL_DIR = "materials"
os.makedirs(MATERIAL_DIR, exist_ok=True)

# Define base materials
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
    """Apply material properties to a trimesh object"""
    materials = load_materials()
    material = materials.get(material_name, materials["metal"])
    
    # Create visual properties
    mesh.visual = trimesh.visual.material.PBRMaterial(
        baseColorFactor=material.get("diffuse", [1, 1, 1]),
        metallicFactor=0.8 if "metal" in material_name else 0.1,
        roughnessFactor=material.get("roughness", 0.3),
        emissiveFactor=material.get("emissive", [0, 0, 0])
    )
    return mesh
