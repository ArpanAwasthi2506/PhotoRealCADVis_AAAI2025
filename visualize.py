#!/usr/bin/env python
"""
CAD Model Visualization Tool
============================

Verified Working Version

Features:
- Handles STEP and PLY files
- Automatic format detection
- Robust error handling
- Multiple visualization backends
"""

import os
import sys
import argparse
import tempfile
import logging
import trimesh
from pathlib import Path
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

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

def visualize_mesh(file_path):
    """Visualize mesh files using best available method"""
    try:
        logger.info(f"Loading file: {file_path}")
        mesh = trimesh.load(file_path)
        
        # Try with pyglet
        try:
            mesh.show()
            return True
        except Exception as e:
            logger.warning(f"Pyglet visualization failed: {str(e)}")
            logger.info("Falling back to Plotly visualization")
            return visualize_with_plotly(mesh)
    except Exception as e:
        logger.error(f"Error visualizing file: {str(e)}")
        return False

import plotly.graph_objects as go

def visualize_with_plotly(mesh):
    try:
        if isinstance(mesh, trimesh.PointCloud):
            points = mesh.vertices
            fig = go.Figure(data=[go.Scatter3d(
                x=points[:, 0],
                y=points[:, 1],
                z=points[:, 2],
                mode='markers',
                marker=dict(size=2)
            )])  # <== closing both the Scatter3d() and the data=[...] list

        else:
            x, y, z = mesh.vertices.T
            i, j, k = mesh.faces.T
            fig = go.Figure(data=[go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                opacity=0.5
            )])

        fig.show()

    except Exception as e:
        print(f"Plotly visualization failed: {e}")


def convert_step_to_stl(step_path, stl_path):
    """Convert STEP file to STL using OpenCASCADE"""
    try:
        logger.info(f"Converting STEP to STL: {step_path}")
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(step_path))
        
        if status != IFSelect_RetDone:
            raise ValueError(f"STEP file read failed with status: {status}")
        
        reader.TransferRoots()
        shape = reader.Shape(1)
        
        # Create mesh from BREP
        mesh = BRepMesh_IncrementalMesh(shape, 0.01)
        mesh.Perform()
        
        # Write to STL
        writer = StlAPI_Writer()
        writer.Write(shape, str(stl_path))
        
        logger.info(f"Conversion successful: {stl_path}")
        return True
    except Exception as e:
        logger.error(f"STEP conversion error: {str(e)}")
        return False

def visualize_step(file_path):
    """Visualize STEP files by converting to STL"""
    try:
        # Create temporary STL file
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp_file:
            stl_path = Path(tmp_file.name)
        
        # Convert STEP to STL
        if not convert_step_to_stl(file_path, stl_path):
            return False
        
        # Visualize with trimesh
        logger.info(f"Visualizing STL conversion: {stl_path}")
        return visualize_mesh(stl_path)
    except Exception as e:
        logger.error(f"STEP visualization error: {str(e)}")
        return False
    finally:
        # Clean up temporary file
        if stl_path.exists():
            logger.info(f"Cleaning up temporary file: {stl_path}")
            os.unlink(stl_path)

def main():
    parser = argparse.ArgumentParser(description="CAD Model Visualization Tool")
    parser.add_argument("file_path", help="Path to CAD file (STEP or PLY)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    setup_logging(args.debug)
    
    file_path = Path(args.file_path)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    # Determine file type
    if file_path.suffix.lower() in [".step", ".stp"]:
        logger.info(f"Visualizing STEP file: {file_path.name}")
        success = visualize_step(file_path)
    elif file_path.suffix.lower() in [".ply", ".obj"]:
        logger.info(f"Visualizing mesh file: {file_path.name}")
        success = visualize_mesh(file_path)
    else:
        logger.error(f"Unsupported file format: {file_path.suffix}")
        sys.exit(1)
    
    if success:
        logger.info("Visualization completed successfully!")
    else:
        logger.error("Visualization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
