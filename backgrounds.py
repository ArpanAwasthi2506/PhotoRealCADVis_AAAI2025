import os
import cv2
import numpy as np
import random
from diffusers import StableDiffusionPipeline
import torch

def generate_backgrounds(output_dir, num_backgrounds=10):
    """Generate diverse backgrounds using Stable Diffusion on GPU"""
    os.makedirs(output_dir, exist_ok=True)

    # Load GPU-accelerated pipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-2-1",
        torch_dtype=torch.float16
    ).to("cuda")

    prompts = [
        "industrial workshop with tools",
        "engineer's desk with blueprints",
        "factory assembly line",
        "clean room laboratory",
        "technical drawing background",
        "modern machine shop",
        "concrete floor and tool shelf",
        "metal fabrication background",
        "manufacturing unit with robots",
        "precision engineering lab"
    ]

    for i in range(num_backgrounds):
        prompt = prompts[i % len(prompts)]
        print(f"Generating background {i+1}/{num_backgrounds}: {prompt}")
        image = pipe(prompt + ", photorealistic, 8k").images[0]
        output_path = os.path.join(output_dir, f"bg_{i:04d}.png")
        image.save(output_path)

    print(f"Generated {num_backgrounds} backgrounds in {output_dir}")


def composite_object(foreground, background_path=None):
    """Composite rendered object onto background"""
    if background_path is None or not os.path.exists(background_path):
        height, width = foreground.shape[:2]
        bg = np.zeros((height, width, 3), dtype=np.uint8)

        top_color = (
            random.randint(180, 220),
            random.randint(200, 230),
            random.randint(220, 255)
        )
        bottom_color = (
            random.randint(150, 190),
            random.randint(170, 210),
            random.randint(200, 230)
        )

        for i in range(height):
            alpha = i / height
            color = [
                int(top_color[0] * (1 - alpha) + bottom_color[0] * alpha),
                int(top_color[1] * (1 - alpha) + bottom_color[1] * alpha),
                int(top_color[2] * (1 - alpha) + bottom_color[2] * alpha)
            ]
            bg[i, :] = color
    else:
        bg = cv2.imread(background_path)
        if bg is None:
            return composite_object(foreground)
        bg = cv2.resize(bg, (foreground.shape[1], foreground.shape[0]))

    gray = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    fg_object = cv2.bitwise_and(foreground, foreground, mask=mask)
    mask_inv = cv2.bitwise_not(mask)
    bg_area = cv2.bitwise_and(bg, bg, mask=mask_inv)

    composite = cv2.add(fg_object, bg_area)
    return composite


if __name__ == "__main__":
    generate_backgrounds("dataset/backgrounds", num_backgrounds=10)
