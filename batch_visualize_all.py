# batch_visualize_all.py

import os
from pathlib import Path
import subprocess

# File extensions to visualize
SUPPORTED_EXTENSIONS = ['.step', '.stp', '.ply', '.obj']

# Path to the CAD visualization script
VISUALIZER = 'visualize.py'

# Root directory containing CAD files
root_dir = Path(__file__).resolve().parent / "data_samples"

# Output folder for rendered images
output_dir = Path(__file__).resolve().parent / "batch_output"
output_dir.mkdir(parents=True, exist_ok=True)

def find_cad_files(root):
    return [f for f in root.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS]

def run_visualizer(file_path):
    output_image = output_dir / (file_path.stem + ".png")
    cmd = [
        "python", str(Path(__file__).resolve().parent / VISUALIZER),
        str(file_path),
        "--output", str(output_image),
        "--material", "plastic"
    ]
    print(f"[INFO] Visualizing: {file_path}")
    subprocess.run(cmd)

if __name__ == "__main__":
    all_files = find_cad_files(root_dir)
    print(f"Found {len(all_files)} files to visualize.")
    for file in all_files:
        run_visualizer(file)
