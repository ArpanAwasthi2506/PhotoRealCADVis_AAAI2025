import os
import sys
import subprocess
import logging
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
    cad_extensions = ['.obj', '.step', '.stp', '.ply']
    return [str(p) for p in Path(dataset_path).rglob('*') 
            if p.suffix.lower() in cad_extensions]

def process_file(file_path):
    """Visualize a single CAD file"""
    try:
        result = subprocess.run(
            ["python", "visualize.py", file_path],
            capture_output=True,
            text=True,
            timeout=60  # 60-second timeout per file
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    setup_logging()
    logger = logging.getLogger('BatchProcessor')
    
    dataset_path = "data_samples"
    if not Path(dataset_path).exists():
        logger.error(f"Dataset directory not found: {dataset_path}")
        sys.exit(1)
    
    # Get list of CAD files
    cad_files = find_cad_files(dataset_path)
    if not cad_files:
        logger.error("No CAD files found in dataset")
        sys.exit(1)
        
    logger.info(f"Found {len(cad_files)} CAD files for processing")
    
    # Create file lists
    Path("file_lists").mkdir(exist_ok=True)
    with open("file_lists/all_files.txt", "w") as f:
        f.write("\n".join(cad_files))
    
    # Process files
    success_count = 0
    failed_files = []
    
    for i, file_path in enumerate(cad_files, 1):
        logger.info(f"Processing file {i}/{len(cad_files)}: {file_path}")
        success, error = process_file(file_path)
        
        if success:
            success_count += 1
            logger.info("✅ Visualization successful")
        else:
            failed_files.append(file_path)
            logger.error(f"❌ Visualization failed: {error}")
        
        # Save progress every 10 files
        if i % 10 == 0:
            with open("file_lists/processed.txt", "a") as f:
                f.write("\n".join(cad_files[i-10:i]) + "\n")
    
    # Generate report
    logger.info("\n" + "="*50)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("="*50)
    logger.info(f"Total files processed: {len(cad_files)}")
    logger.info(f"Successfully visualized: {success_count}")
    logger.info(f"Failed: {len(failed_files)}")
    
    if failed_files:
        with open("file_lists/failed_files.txt", "w") as f:
            f.write("\n".join(failed_files))
        logger.info("Failed files saved to: file_lists/failed_files.txt")
    
    logger.info("Batch processing completed!")

if __name__ == "__main__":
    main()
