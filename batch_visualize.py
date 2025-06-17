#!/usr/bin/env python
"""
Batch Visualization Processor
=============================

Automates rendering of CAD files with:
- Random materials
- Procedural backgrounds
- Camera variations
"""

import os
import sys
import subprocess
import logging
import random
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("batch_visualization.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def find_cad_files(dataset_path):
    """Find all CAD files in the dataset directory"""
    cad_extensions = ['.step', '.stp', '.ply', '.obj']
    return [str(p) for p in Path(dataset_path).rglob('*') if p.suffix.lower() in cad_extensions]

def process_file(file_path, output_dir, material, dataset_path):
    """Process a single CAD file with visualization script"""
    try:
        # Create output file path
        rel_path = Path(file_path).relative_to(dataset_path)
        output_path = Path(output_dir) / rel_path.with_suffix('.png')
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build the visualize.py command
        cmd = [
            "python", "visualize.py", str(file_path),
            "--output", str(output_path),
            "--material", material
        ]

        # Run subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # up to 5 minutes per file
        )

        if result.returncode == 0 and output_path.exists():
            return True, ""
        else:
            return False, f"Return code: {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    except Exception as e:
        return False, str(e)

def main():
    setup_logging()
    logger = logging.getLogger('BatchProcessor')

    # Configuration
    dataset_path = Path("data_samples").resolve()
    output_dir = Path("rendered_results").resolve()
    materials = ['metal', 'plastic', 'ceramic']

    if not dataset_path.exists():
        logger.error(f"Dataset directory not found: {dataset_path}")
        sys.exit(1)

    output_dir.mkdir(exist_ok=True)

    cad_files = find_cad_files(dataset_path)
    if not cad_files:
        logger.error("No CAD files found in dataset")
        sys.exit(1)

    logger.info(f"Found {len(cad_files)} CAD files for processing")

    Path("file_lists").mkdir(exist_ok=True)
    with open("file_lists/all_files.txt", "w") as f:
        f.write("\n".join(cad_files))

    success_count = 0
    failed_files = []

    for i, file_path in enumerate(cad_files, 1):
        material = random.choice(materials)
        logger.info(f"\n[{i}/{len(cad_files)}] Processing: {file_path}")
        logger.info(f"→ Material used: {material}")

        success, error = process_file(file_path, output_dir, material, dataset_path)

        if success:
            success_count += 1
            logger.info("✅ Success")
        else:
            failed_files.append(file_path)
            logger.error("❌ Failed")
            logger.error(error)

        # Periodic progress save
        if i % 5 == 0:
            with open("file_lists/processed.txt", "a") as f:
                f.write("\n".join(cad_files[i-5:i]) + "\n")

    # Final report
    logger.info("\n" + "="*50)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("="*50)
    logger.info(f"Total files:        {len(cad_files)}")
    logger.info(f"Successfully done:  {success_count}")
    logger.info(f"Failures:           {len(failed_files)}")

    if failed_files:
        with open("file_lists/failed_files.txt", "w") as f:
            f.write("\n".join(failed_files))
        logger.info("⚠️  Failed files written to: file_lists/failed_files.txt")

    logger.info(f"\n🖼️  All renders saved to: {output_dir}")
    logger.info("🎉 Batch processing complete.")

if __name__ == "__main__":
    main()
