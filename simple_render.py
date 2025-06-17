import bpy
import os
import sys
import argparse

# Suppress GVFS warning
os.environ['BLENDER_SYSTEM_SKIP_GVFS_CHECK'] = '1'

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True, help="Input file to render")
    parser.add_argument("--output_file", required=True, help="Output PNG file")
    return parser.parse_args(argv)

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Add a camera
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.location = (3, -3, 2)
    camera.data.lens = 35
    
    # Set this camera as the active camera for the scene
    bpy.context.scene.camera = camera
    
    # Point camera to origin
    bpy.ops.object.empty_add(location=(0, 0, 0))
    focus = bpy.context.active_object
    camera.constraints.new(type='TRACK_TO')
    camera.constraints['Track To'].target = focus
    
    return camera

def import_model(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".obj":
        bpy.ops.import_scene.obj(filepath=filepath)
    elif ext in [".step", ".stp"]:
        bpy.ops.import_scene.step(filepath=filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    return bpy.context.selected_objects[0]

def main():
    args = parse_args()
    
    # Setup scene
    camera = setup_scene()
    
    # Import model
    obj = import_model(args.input_file)
    
    # Position object at origin
    obj.location = (0, 0, 0)
    
    # Set render settings
    bpy.context.scene.render.filepath = args.output_file
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.image_settings.file_format = "PNG"
    
    # Render
    bpy.ops.render.render(write_still=True)
    print(f"✅ Rendered {args.input_file} to {args.output_file}")

if __name__ == "__main__":
    main()
