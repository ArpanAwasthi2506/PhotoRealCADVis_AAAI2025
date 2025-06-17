import cv2
import os
import random
import numpy as np
from pathlib import Path
import argparse
import json

def add_shadows(foreground, bg):
    # Extract alpha channel
    if foreground.shape[2] == 4:
        alpha = foreground[:, :, 3]
        fg_rgb = foreground[:, :, :3]
    else:
        fg_rgb = foreground
        gray = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    
    # Create shadow mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    shadow = cv2.morphologyEx(alpha, cv2.MORPH_ERODE, kernel)
    shadow = cv2.GaussianBlur(shadow, (51, 51), 0)
    shadow = shadow.astype(np.float32) / 255 * 0.6
    
    # Ensure proper dimensions
    if len(bg.shape) == 2:
        bg = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
    
    # Resize background to match foreground
    bg = cv2.resize(bg, (fg_rgb.shape[1], fg_rgb.shape[0]))
    
    # Convert to float for processing
    bg = bg.astype(np.float32) / 255
    fg_rgb = fg_rgb.astype(np.float32) / 255
    
    # Create shadow effect
    shadow_mask = np.stack([shadow] * 3, axis=-1)
    composite = bg * (1 - shadow_mask) + fg_rgb * shadow_mask
    
    # Combine foreground and background
    alpha_mask = alpha.astype(np.float32) / 255
    alpha_mask = np.stack([alpha_mask] * 3, axis=-1)
    result = composite * alpha_mask + bg * (1 - alpha_mask)
    
    return (result * 255).astype(np.uint8)

def composite_images(render_dir, bg_dir, output_dir):
    render_dir = Path(render_dir)
    bg_dir = Path(bg_dir)
    output_dir = Path(output_dir)
    
    # Find all background images
    bg_images = list(bg_dir.glob("*.*"))
    bg_images = [f for f in bg_images if f.suffix.lower() in ['.png', '.jpg', '.jpeg']]
    
    if not bg_images:
        print(f"❌ No background images found in: {bg_dir}")
        return
    
    # Find all rendered images
    render_images = list(render_dir.rglob("*.png"))
    
    if not render_images:
        print(f"❌ No rendered images found in: {render_dir}")
        return
    
    # Create composite for each render
    for render_path in render_images:
        try:
            # Preserve directory structure in output
            rel_path = render_path.relative_to(render_dir)
            out_path = output_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load rendered image
            fg = cv2.imread(str(render_path), cv2.IMREAD_UNCHANGED)
            if fg is None:
                print(f"⚠️ Could not read: {render_path}")
                continue
                
            # Select random background
            bg_path = random.choice(bg_images)
            bg = cv2.imread(str(bg_path))
            if bg is None:
                print(f"⚠️ Could not read background: {bg_path}")
                continue
            
            # Composite image
            composite = add_shadows(fg, bg)
            
            # Save result
            cv2.imwrite(str(out_path), composite)
            print(f"✅ Composited: {out_path}")
            
        except Exception as e:
            print(f"❌ Error processing {render_path}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--render_dir", required=True, help="Directory with rendered images")
    parser.add_argument("--bg_dir", required=True, help="Directory with background images")
    parser.add_argument("--output_dir", required=True, help="Output directory for composited images")
    args = parser.parse_args()
    
    composite_images(args.render_dir, args.bg_dir, args.output_dir)
