import os
import cv2
import numpy as np
import random
import json
from plane_detection import PlaneDetector

# --- Configuration ---
RENDER_DIR = "renders"
BACKGROUND_DIR = "backgrounds"
COMPOSITE_DIR = "composites"
CONFIG_PATH = "compositing_config.json"
os.makedirs(COMPOSITE_DIR, exist_ok=True)

# Initialize plane detector
plane_detector = PlaneDetector()

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "object_scale": 0.7,
        "shadow_blur": 25,
        "output_size": (1024, 768)
    }

def photorealistic_composite(render_path, background_path, camera_metadata, config):
    render = cv2.imread(render_path, cv2.IMREAD_UNCHANGED)
    background = cv2.imread(background_path)

    if render is None or background is None:
        print(f"Error loading images: {render_path} or {background_path}")
        return None

    bg_height, bg_width = background.shape[:2]
    table_plane = plane_detector.detect_table_plane(background)
    lighting = plane_detector.estimate_lighting(background)

    render_height, render_width = render.shape[:2]
    focal_length = camera_metadata.get('camera_params', {}).get('focal_length', 35)
    sensor_width = camera_metadata.get('camera_params', {}).get('sensor_width', 32)
    distance_to_object = np.linalg.norm(camera_metadata.get('camera_params', {}).get('position', [0, 0, 2.5]))

    try:
        scale_factor = (focal_length * distance_to_object) / (sensor_width * render_width)
        scale = config.get('object_scale', 0.7) * scale_factor
        scale = max(0.1, min(scale, 3.0))
    except ZeroDivisionError:
        scale = config.get('object_scale', 0.7)

    table_center = table_plane.get('center', (bg_width // 2, bg_height // 2))
    pos_x = int(table_center[0] - (render_width * scale) // 2)
    pos_y = int(table_center[1] - (render_height * scale) // 2)
    pos_x = max(0, min(bg_width - 10, pos_x))
    pos_y = max(0, min(bg_height - 10, pos_y))

    try:
        render_transformed = apply_perspective(
            render,
            camera_metadata.get('camera_params', {}).get('rotation', [0, 0, 0]),
            scale
        )
    except Exception:
        new_size = (max(10, int(render_width * scale)), max(10, int(render_height * scale)))
        render_transformed = cv2.resize(render, new_size)

    render_lit = apply_lighting(render_transformed, lighting)

    # Resize render to match background if dimensions mismatch
    if render_lit.shape[0] != background.shape[0] or render_lit.shape[1] != background.shape[1]:
        render_lit = cv2.resize(render_lit, (background.shape[1], background.shape[0]))

    try:
        shadow = generate_physics_shadow(render_lit, table_plane, lighting)
    except:
        shadow = None

    composite = background.copy()
    if shadow is not None:
        composite = blend_shadow(composite, shadow)
    composite = blend_object(composite, render_lit, (pos_x, pos_y))

    return composite

def apply_perspective(render, rotation, scale):
    height, width = render.shape[:2]
    new_w = max(10, int(width * scale))
    new_h = max(10, int(height * scale))
    render = cv2.resize(render, (new_w, new_h))

    src_pts = np.array([
        [0, 0], [new_w, 0], [new_w, new_h], [0, new_h]
    ], dtype=np.float32)

    rx, ry, rz = np.radians(rotation)
    dst_pts = np.array([
        [np.clip(new_w * 0.1 * rx, 0, new_w), np.clip(new_h * 0.1 * ry, 0, new_h)],
        [np.clip(new_w - new_w * 0.1 * rz, 0, new_w), np.clip(new_h * 0.05 * ry, 0, new_h)],
        [np.clip(new_w - new_w * 0.05 * rx, 0, new_w), np.clip(new_h - new_h * 0.1 * ry, 0, new_h)],
        [np.clip(new_w * 0.1 * rz, 0, new_w), np.clip(new_h - new_h * 0.05 * ry, 0, new_h)]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    return cv2.warpPerspective(render, M, (new_w, new_h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

def apply_lighting(render, lighting_info):
    bgr = render[:, :, :3]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = np.clip(v * lighting_info.get('intensity', 1.0), 0, 255).astype(np.uint8)
    s = np.clip(s * 0.9, 0, 255).astype(np.uint8)
    adjusted = cv2.merge([h, s, v])
    bgr_adjusted = cv2.cvtColor(adjusted, cv2.COLOR_HSV2BGR)
    if render.shape[2] == 4:
        return np.dstack((bgr_adjusted, render[:, :, 3]))
    return bgr_adjusted

def generate_physics_shadow(render, plane_info, lighting_info):
    alpha = render[:, :, 3] if render.shape[2] == 4 else None
    if alpha is None:
        return None
    light_dir = np.array(lighting_info.get('direction', [1, -1, 0]))
    shadow_dir = -light_dir[:2] * 20
    M = np.array([[1, 0, shadow_dir[0]], [0, 1, shadow_dir[1]]], dtype=float)
    shadow = cv2.warpAffine(alpha, M, (render.shape[1], render.shape[0]))
    shadow = cv2.GaussianBlur(shadow, (25, 25), 0)
    return shadow * lighting_info.get('intensity', 1.0) * 0.7

def blend_shadow(background, shadow):
    shadow_3ch = np.stack([shadow] * 3, axis=-1) / 255.0
    return (background.astype(np.float32) * (1.0 - shadow_3ch * 0.5)).astype(np.uint8)

def blend_object(background, render, position):
    """Blend object onto background with proper alpha handling"""
    x, y = position
    h, w = render.shape[:2]
    H, W = background.shape[:2]

    # Create a blank canvas for full-sized render
    if render.shape[2] == 4:
        render_fullsize = np.zeros((H, W, 4), dtype=np.uint8)
    else:
        render_fullsize = np.zeros((H, W, 3), dtype=np.uint8)

    y_end = min(H, y + h)
    x_end = min(W, x + w)

    if y_end > y and x_end > x:
        render_y = min(h, H - y)
        render_x = min(w, W - x)
        render_fullsize[y:y_end, x:x_end] = render[:render_y, :render_x]
    else:
        x = max(0, (W - w) // 2)
        y = max(0, (H - h) // 2)
        y_end = min(H, y + h)
        x_end = min(W, x + w)
        render_y = min(h, H - y)
        render_x = min(w, W - x)
        render_fullsize[y:y_end, x:x_end] = render[:render_y, :render_x]

    if render_fullsize.shape[2] == 4:
        obj_rgb = render_fullsize[:, :, :3]
        alpha = render_fullsize[:, :, 3:] / 255.0
    else:
        obj_rgb = render_fullsize
        alpha = np.ones(obj_rgb.shape[:2] + (1,), dtype=np.float32)

    blended = (obj_rgb * alpha) + (background * (1 - alpha))
    return blended.astype(np.uint8)

def main():
    config = load_config()
    renders = [os.path.join(RENDER_DIR, f) for f in os.listdir(RENDER_DIR)
               if f.endswith('.png') and '_metadata' not in f]

    metadata = {}
    for render in renders:
        base_name = os.path.splitext(os.path.basename(render))[0]
        meta_path = os.path.join(RENDER_DIR, f"{base_name}_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                metadata[base_name] = json.load(f)

    backgrounds = [os.path.join(BACKGROUND_DIR, f) for f in os.listdir(BACKGROUND_DIR)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    composite_info = []
    for i, render in enumerate(renders):
        base_name = os.path.splitext(os.path.basename(render))[0]
        bg = random.choice(backgrounds)
        cam_meta = metadata.get(base_name, [{}])[0]
        composite = photorealistic_composite(render, bg, cam_meta, config)
        if composite is None:
            continue

        output_name = f"composite_{i:04d}.jpg"
        output_path = os.path.join(COMPOSITE_DIR, output_name)
        cv2.imwrite(output_path, composite)
        composite_info.append({
            "composite": output_name,
            "render": os.path.basename(render),
            "background": os.path.basename(bg),
            "camera_metadata": cam_meta,
            "composite_path": output_path
        })

    with open(os.path.join(COMPOSITE_DIR, "composite_metadata.json"), "w") as f:
        json.dump(composite_info, f, indent=2)

    print(f"✅ Created {len(composite_info)} photorealistic composites")

if __name__ == "__main__":
    main()
