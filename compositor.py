import os
import cv2
import numpy as np
import random
from PIL import Image
import json

# --- Configuration ---
RENDER_DIR = "renders"
BACKGROUND_DIR = "backgrounds"
COMPOSITE_DIR = "composites"
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
    render = cv2.imread(render_path, cv2.IMREAD_UNCHANGED)
    background = cv2.imread(background_path)

    if render is None or background is None:
        print(f"Skipping due to load failure: {render_path} or {background_path}")
        return None

    # Ensure 4-channel render
    if render.shape[2] == 3:
        render = cv2.cvtColor(render, cv2.COLOR_BGR2BGRA)

    # Resize background
    background = cv2.resize(background, config["output_size"])

    alpha = render[:, :, 3] / 255.0
    rgb = render[:, :, :3]
    rgb = (rgb * config["color_adjustment"]).astype(np.uint8)

    margin_x = int(config["output_size"][0] * 0.1)
    margin_y = int(config["output_size"][1] * 0.1)

    # --- Fix: Scale bounding box to fit ---
    max_allowed_width = config["output_size"][0] - 2 * margin_x
    max_allowed_height = config["output_size"][1] - 2 * margin_y
    width_scale = max_allowed_width / rgb.shape[1]
    height_scale = max_allowed_height / rgb.shape[0]
    max_scale = min(width_scale, height_scale, config["max_scale"])

    if max_scale < config["min_scale"]:
        scale = config["min_scale"]
        print(f"Warning: Object too large. Using min scale {scale}")
    else:
        scale = random.uniform(config["min_scale"], max_scale)

    new_h = int(rgb.shape[0] * scale)
    new_w = int(rgb.shape[1] * scale)

    resized_rgb = cv2.resize(rgb, (new_w, new_h))
    resized_alpha = cv2.resize(alpha, (new_w, new_h))

    pos_x = random.randint(margin_x, config["output_size"][0] - new_w - margin_x)
    pos_y = random.randint(margin_y, config["output_size"][1] - new_h - margin_y)

    # --- Shadow creation with fixed perspective ---
    shadow = np.zeros((config["output_size"][1], config["output_size"][0]), dtype=float)
    offset_x = int(config["light_direction"][0] * 30)
    offset_y = int(config["light_direction"][1] * 30)

    shadow_pts = np.array([
        [0, 0],
        [new_w, 0],
        [new_w, new_h],
        [0, new_h]
    ], dtype=np.float32)

    shadow_dst = shadow_pts + np.array([offset_x, offset_y], dtype=np.float32)

    if shadow_pts.shape == (4, 2) and shadow_dst.shape == (4, 2):
        M = cv2.getPerspectiveTransform(shadow_pts, shadow_dst)
        shadow_mask = cv2.warpPerspective(
            resized_alpha,
            M,
            (config["output_size"][0], config["output_size"][1])
        )
    else:
        # Fallback to translation if transform fails
        shadow_mask = np.zeros((config["output_size"][1], config["output_size"][0]))
        y1 = max(0, pos_y + offset_y)
        y2 = min(config["output_size"][1], pos_y + offset_y + new_h)
        x1 = max(0, pos_x + offset_x)
        x2 = min(config["output_size"][0], pos_x + offset_x + new_w)
        if y1 < y2 and x1 < x2:
            shadow_mask[y1:y2, x1:x2] = resized_alpha[:y2-y1, :x2-x1]

    # --- Apply shadow ---
    shadow[pos_y:pos_y+new_h, pos_x:pos_x+new_w] = shadow_mask[pos_y:pos_y+new_h, pos_x:pos_x+new_w] * config["shadow_intensity"]
    shadow = cv2.GaussianBlur(shadow, (config["shadow_blur"], config["shadow_blur"]), 0)
    shadow = np.clip(shadow, 0, 0.7)[:, :, np.newaxis]
    background = (background * (1 - shadow)).astype(np.uint8)

    # --- Composite with alpha ---
    for c in range(3):
        region = background[pos_y:pos_y + new_h, pos_x:pos_x + new_w, c]
        region[:] = (
            resized_rgb[:, :, c].astype(float) * resized_alpha +
            region.astype(float) * (1 - resized_alpha)
        )

    return background

def main():
    config = load_config()

    renders = [os.path.join(RENDER_DIR, f) for f in os.listdir(RENDER_DIR) if f.endswith('.png')]
    backgrounds = [os.path.join(BACKGROUND_DIR, f) for f in os.listdir(BACKGROUND_DIR) if f.lower().endswith(('.png', '.jpg'))]

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

    print(f"\nCompositing complete! {len(composite_info)} images saved in {COMPOSITE_DIR}")

if __name__ == "__main__":
    main()
