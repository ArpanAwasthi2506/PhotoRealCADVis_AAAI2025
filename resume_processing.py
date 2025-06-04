import os
import logging
from batch_visualize import find_cad_files, process_file, setup_logging

def main():
    setup_logging()
    logger = logging.getLogger('ResumeProcessor')
    
    # Find all CAD files
    all_files = find_cad_files("data_samples")
    
    # Get already processed files
    processed_files = set()
    if os.path.exists("file_lists/processed.txt"):
        with open("file_lists/processed.txt") as f:
            processed_files = set(f.read().splitlines())
    
    # Get failed files to retry
    files_to_process = [f for f in all_files if f not in processed_files]
    
    if not files_to_process:
        logger.info("No files to process - all files already completed")
        return
    
    logger.info(f"Resuming processing for {len(files_to_process)} files")
    
    success_count = 0
    failed_files = []
    
    for i, file_path in enumerate(files_to_process, 1):
        logger.info(f"Processing file {i}/{len(files_to_process)}: {file_path}")
        success, error = process_file(file_path)
        
        if success:
            success_count += 1
            logger.info("✅ Visualization successful")
            # Append to processed list
            with open("file_lists/processed.txt", "a") as f:
                f.write(file_path + "\n")
        else:
            failed_files.append(file_path)
            logger.error(f"❌ Visualization failed: {error}")
    
    # Generate report
    logger.info("\n" + "="*50)
    logger.info("RESUME PROCESSING SUMMARY")
    logger.info("="*50)
    logger.info(f"Files processed: {len(files_to_process)}")
    logger.info(f"New successes: {success_count}")
    logger.info(f"New failures: {len(failed_files)}")
    
    if failed_files:
        with open("file_lists/failed_files.txt", "a") as f:
            f.write("\n".join(failed_files) + "\n")
    
    logger.info("Resume processing completed!")

if __name__ == "__main__":
    main()
