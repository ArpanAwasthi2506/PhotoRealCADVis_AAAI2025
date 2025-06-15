import os
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

if __name__ == "__main__":
    generate_backgrounds("dataset/backgrounds", num_backgrounds=10)
