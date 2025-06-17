from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-1", 
    torch_dtype=torch.float16
).to("cuda")

prompts = [
    "industrial workshop with tools",
    "engineer's desk with blueprints",
    "factory assembly line",
    "clean room laboratory"
]

for i, prompt in enumerate(prompts):
    image = pipe(prompt + ", photorealistic, 8k").images[0]
    image.save(f"dataset/backgrounds/bg_{i:04d}.png")
