import bpy
import os
import sys
import argparse
import random
import json
from pathlib import Path

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", help="Root directory of ABC dataset")
    parser.add_argument("--output_dir", required=True, help="Directory to save rendered images")
    parser.add_argument("--mode", choices=["mesh", "brep"], required=True)
    # Add input_file argument for single file rendering
    parser.add_argument("--input_file", help="Process a single file (for testing)")
    return parser.parse_args(argv)

def setup_scene(hdri_path):  
    # ... [keep existing setup_scene function unchanged] ...

def import_model(filepath, mode):
    # ... [keep existing import_model function unchanged] ...

def apply_pbr_material(obj, material_type):
    # ... [keep existing apply_pbr_material function unchanged] ...

def render_model(filepath, output_path, mode, hdri_dir):
    # ... [keep existing render_model function unchanged] ...

def find_cad_files(root_dir, mode):
    # ... [keep existing find_cad_files function unchanged] ...

def render_batch(root_dir, output_dir, mode, hdri_dir="hdri"):
    
    if input_file:
        # Single file mode
        cad_files = [input_file]
        print(f"Processing single file: {input_file}")
    else:
        # Batch mode
        cad_files = find_cad_files(root_dir, mode)
    
    total = len(cad_files)
    log_data = []
    
    print(f"Found {total} {mode} files to render")
    
    for i, filepath in enumerate(cad_files):
        print(f"Processing {i+1}/{total}: {filepath}")
        
        # Create output path
        if input_file:
            # Simple filename for single file mode
            output_path = os.path.join(output_dir, os.path.basename(filepath).split('.')[0] + '.png')
        else:
            # Preserve directory structure for batch mode
            rel_path = Path(filepath).relative_to(root_dir)
            output_path = Path(output_dir) / rel_path.with_suffix('.png')
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Render the model
        result = render_model(
            filepath, 
            str(output_path),
            mode,
            hdri_dir
        )
        
        if result:
            log_data.append(result)
        
        # Cleanup after each render
        bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Save metadata log
    if log_data:
        log_file = Path(output_dir) / "render_metadata.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        print(f"Rendering complete. Metadata saved to {log_file}")
    else:
        print("No files were successfully rendered")

if __name__ == "__main__":
    args = parse_args()
    
    # Handle GVFS warning suppression
    if 'BLENDER_SYSTEM_SKIP_GVFS_CHECK' not in os.environ:
        os.environ['BLENDER_SYSTEM_SKIP_GVFS_CHECK'] = '1'
        print("Setting BLENDER_SYSTEM_SKIP_GVFS_CHECK=1 to suppress warnings")
    
    render_batch(
        args.root_dir, 
        args.output_dir, 
        args.mode,
        input_file=args.input_file
    )
