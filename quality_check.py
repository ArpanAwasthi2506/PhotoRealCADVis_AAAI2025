import cv2
import os
import json
import numpy as np

def check_composite_quality(composite_path):
    """Check composite image quality metrics"""
    img = cv2.imread(composite_path)
    if img is None:
        return False, "Failed to load image"

    # Convert to grayscale for analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)

    # Exposure check
    if mean_val > 240:
        return False, "Overexposed (mostly white background)"
    if mean_val < 15:
        return False, "Underexposed (mostly black background)"

    # Contrast check
    min_val = np.min(gray)
    max_val = np.max(gray)
    contrast = (max_val - min_val) / (max_val + min_val + 1e-5)
    if contrast < 0.2:
        return False, f"Low contrast: {contrast:.2f}"

    # Object visibility using edge density (Canny edge detection)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges) / (edges.size * 255)
    if edge_density < 0.01:
        return False, f"Low object visibility: {edge_density:.4f}"

    return True, "Quality OK"

def main():
    metadata_path = "composites/composite_metadata.json"
    if not os.path.exists(metadata_path):
        print(f"Metadata file not found: {metadata_path}")
        return

    with open(metadata_path) as f:
        metadata = json.load(f)

    results = []
    for item in metadata:
        composite_path = item.get("composite_path") or item.get("composite")
        valid, message = check_composite_quality(composite_path)
        results.append({
            "file": composite_path,
            "valid": valid,
            "message": message
        })
        status = "PASS" if valid else "FAIL"
        print(f"{status}: {composite_path} - {message}")

    # Save quality report
    with open("quality_report.json", "w") as f:
        json.dump(results, f, indent=2)

    # Count passing composites
    valid_count = sum(1 for r in results if r["valid"])
    print(f"\nQuality check complete! {valid_count}/{len(results)} composites passed")

if __name__ == "__main__":
    main()
