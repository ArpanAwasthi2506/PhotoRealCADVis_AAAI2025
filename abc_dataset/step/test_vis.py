from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Display.SimpleGui import init_display

# Initialize the 3D viewer
display, start_display, add_menu, add_function_to_menu = init_display()

# Load STEP file from nested folder
step_reader = STEPControl_Reader()
file_path = "abc_dataset/step/abc_0000_step_v00/abc_0000.step"
status = step_reader.ReadFile(file_path)

if status == 1:  # Check if file was read successfully
    step_reader.TransferRoots()
    shape = step_reader.OneShape()

    # Display the shape
    display.DisplayShape(shape, update=True)
    start_display()
else:
    print(f"Error: Could not read STEP file from {file_path}")
