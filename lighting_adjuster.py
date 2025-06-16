import cv2
import numpy as np

def match_lighting(foreground, background, mask):
    """Adjust foreground lighting to match background"""
    # Convert to LAB color space for lighting adjustment
    fg_lab = cv2.cvtColor(foreground, cv2.COLOR_BGR2LAB)
    bg_lab = cv2.cvtColor(background, cv2.COLOR_BGR2LAB)
    
    # Calculate mean and std for background
    bg_mean, bg_std = cv2.meanStdDev(bg_lab, mask=mask)
    
    # Calculate mean and std for foreground
    fg_mean, fg_std = cv2.meanStdDev(fg_lab, mask=mask)
    
    # Normalize foreground to match background statistics
    fg_lab = fg_lab.astype(np.float32)
    fg_lab[:,:,0] = (fg_lab[:,:,0] - fg_mean[0]) * (bg_std[0] / fg_std[0]) + bg_mean[0]
    fg_lab[:,:,1] = (fg_lab[:,:,1] - fg_mean[1]) * (bg_std[1] / fg_std[1]) + bg_mean[1]
    fg_lab[:,:,2] = (fg_lab[:,:,2] - fg_mean[2]) * (bg_std[2] / fg_std[2]) + bg_mean[2]
    
    # Clip values to valid range
    fg_lab = np.clip(fg_lab, 0, 255).astype(np.uint8)
    
    # Convert back to BGR
    return cv2.cvtColor(fg_lab, cv2.COLOR_LAB2BGR)

# Usage in compositor.py (add before color adjustment):
# rgb = match_lighting(rgb, background_region, alpha_mask)
