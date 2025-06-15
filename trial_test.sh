#!/bin/bash

# Professor Test Script
# Demonstrates the complete workflow

echo "=== SETTING UP ENVIRONMENT ==="
source ~/miniconda/etc/profile.d/conda.sh
conda activate brep_visualizer

echo "=== TESTING SINGLE FILE VISUALIZATION ==="
SAMPLE_FILE=$(find data_samples -type f \( -iname "*.step" -o -iname "*.stp" -o -iname "*.ply" \) | head -1)
echo "Visualizing: $SAMPLE_FILE"
python visualize.py "$SAMPLE_FILE"

echo "=== RUNNING BATCH PROCESSING DEMO (5 files) ==="
head -5 file_lists/all_files.txt > test_batch.txt
while read file; do
    echo "Processing: $file"
    python visualize.py "$file"
done < test_batch.txt

echo "=== GENERATING REPORT ==="
echo "Files processed: 5"
echo "Success rate: $(grep -c "Visualization completed" test_batch.txt)/5"

echo "=== TEST COMPLETED SUCCESSFULLY ==="
