import os
import cv2
import numpy as np
import random
from PIL import Image
import json

# Configuration
RENDER_DIR = "renders"
BACKGROUND_DIR = "backgrounds"
COMPOSITE_DIR = "composites"
MATERIAL_DIR = "materials"
CONFIG_PATH = "compositing_config.json"
os.makedirs(COMPOSITE_DIR, exist_ok=True)

def load_config():
    """Load compositing configuration"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "shadow_intensity": 0.6,
        "shadow_blur": 25,
        "min_scale": 0.5,
        "max_scale": 0.9,
        "light_direction": (0.7, -0.3),  # (x, y) normalized
        "color_adjustment": 0.95,
        "output_size": (1024, 768)
    }

def composite_object(render_path, background_path, config):
    """Composite CAD render onto background with realistic effects"""
    # Load images
    render = cv2.imread(render_path, cv2.IMREAD_UNCHANGED)
    background = cv2.imread(background_path)

    if render is None or background is None:
        print(f"Skipping due to load failure: {render_path} or {background_path}")
        return None

    # Resize background to output size
    background = cv2.resize(background, config["output_size"])

    # Extract alpha channel from render
    if render.shape[2] == 4:
        alpha = render[:, :, 3] / 255.0
        rgb = render[:, :, :3]
    else:
        # Create alpha from non-black pixels
        gray = cv2.cvtColor(render, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        alpha = alpha.astype(float) / 255
        rgb = render

    # Apply color adjustment to match background lighting
    rgb = (rgb * config["color_adjustment"]).astype(np.uint8)

    # Random scaling and positioning
    scale = random.uniform(config["min_scale"], config["max_scale"])
    new_h = int(rgb.shape[0] * scale)
    new_w = int(rgb.shape[1] * scale)

    margin_x = int(config["output_size"][0] * 0.1)
    margin_y = int(config["output_size"][1] * 0.1)

    # Check if object fits
    if new_w + 2 * margin_x > config["output_size"][0] or new_h + 2 * margin_y > config["output_size"][1]:
        print(f"Skipping {render_path} due to size {new_w}x{new_h} larger than output size with margin")
        return None

    resized_rgb = cv2.resize(rgb, (new_w, new_h))
    resized_alpha = cv2.resize(alpha, (new_w, new_h))

    pos_x = random.randint(margin_x, config["output_size"][0] - new_w - margin_x)
    pos_y = random.randint(margin_y, config["output_size"][1] - new_h - margin_y)

    # Create shadow
    shadow = np.zeros((config["output_size"][1], config["output_size"][0]), dtype=float)
    shadow_mask = resized_alpha.copy()

    # Apply light direction offset
    offset_x = int(config["light_direction"][0] * 30)
    offset_y = int(config["light_direction"][1] * 30)
    shadow_mask = cv2.warpAffine(
        shadow_mask,
        np.float32([[1, 0, offset_x], [0, 1, offset_y]]),
        (shadow_mask.shape[1], shadow_mask.shape[0])
    )

    # Add shadow to background
    shadow[
        pos_y + offset_y:pos_y + offset_y + new_h,
        pos_x + offset_x:pos_x + offset_x + new_w
    ] = shadow_mask * config["shadow_intensity"]

    shadow = cv2.GaussianBlur(shadow, (config["shadow_blur"], config["shadow_blur"]), 0)
    shadow = np.clip(shadow, 0, 0.7)[:, :, np.newaxis]

    # Apply shadow to background
    background = (background * (1 - shadow)).astype(np.uint8)

    # Composite object
    for c in range(3):
        region = background[
            pos_y:pos_y + new_h,
            pos_x:pos_x + new_w,
            c
        ]
        region[:] = (
            resized_rgb[:, :, c].astype(float) * resized_alpha +
            region.astype(float) * (1 - resized_alpha)
        )

    return background

def main():
    config = load_config()

    renders = [os.path.join(RENDER_DIR, f) for f in os.listdir(RENDER_DIR)
               if f.endswith('.png')]
    backgrounds = [os.path.join(BACKGROUND_DIR, f) for f in os.listdir(BACKGROUND_DIR)
                   if f.endswith(('.png', '.jpg'))]

    print(f"Found {len(renders)} renders and {len(backgrounds)} backgrounds")

    composite_info = []
    for i, render in enumerate(renders):
        bg = random.choice(backgrounds)
        composite = composite_object(render, bg, config)

        if composite is None:
            continue

        output_name = f"composite_{i:04d}.jpg"
        output_path = os.path.join(COMPOSITE_DIR, output_name)
        cv2.imwrite(output_path, composite)

        composite_info.append({
            "composite": output_name,
            "render": os.path.basename(render),
            "background": os.path.basename(bg),
            "composite_path": output_path
        })
        print(f"Created composite {i+1}/{len(renders)}: {output_name}")

    with open(os.path.join(COMPOSITE_DIR, "composite_metadata.json"), "w") as f:
        json.dump(composite_info, f, indent=2)

    print(f"Compositing complete! Created {len(composite_info)} composites in {COMPOSITE_DIR}")

if __name__ == "__main__":
    main()
