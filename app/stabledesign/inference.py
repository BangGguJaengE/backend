# export PYTORCH_ENABLE_MPS_FALLBACK=1
import os
from typing import Tuple, Union, List
import numpy as np
from PIL import Image
import torch
from diffusers import ControlNetModel, StableDiffusionControlNetInpaintPipeline, UniPCMultistepScheduler, StableDiffusionXLPipeline
from transformers import AutoImageProcessor, UperNetForSemanticSegmentation, AutoModelForDepthEstimation
from colors import ade_palette
from utils import map_colors_rgb
import gc

device = "cuda"
dtype = torch.float16

def filter_items(
    colors_list: Union[List, np.ndarray],
    items_list: Union[List, np.ndarray],
    items_to_remove: Union[List, np.ndarray]
) -> Tuple[Union[List, np.ndarray], Union[List, np.ndarray]]:
    filtered_colors = []
    filtered_items = []
    for color, item in zip(colors_list, items_list):
        if item not in items_to_remove:
            filtered_colors.append(color)
            filtered_items.append(item)
    return filtered_colors, filtered_items

def get_segmentation_pipeline() -> Tuple[AutoImageProcessor, UperNetForSemanticSegmentation]:
    image_processor = AutoImageProcessor.from_pretrained("openmmlab/upernet-convnext-small")
    image_segmentor = UperNetForSemanticSegmentation.from_pretrained("openmmlab/upernet-convnext-small").to(device).to(dtype)
    return image_processor, image_segmentor

@torch.inference_mode()
def segment_image(image: Image, image_processor: AutoImageProcessor, image_segmentor: UperNetForSemanticSegmentation) -> Image:
    pixel_values = image_processor(image, return_tensors="pt").pixel_values.to(device).to(dtype)
    with torch.no_grad():
        outputs = image_segmentor(pixel_values)

    seg = image_processor.post_process_semantic_segmentation(outputs, target_sizes=[image.size[::-1]])[0]
    seg = seg.cpu().numpy()  # CPU로 이동하여 NumPy 배열로 변환
    color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)
    palette = np.array(ade_palette())
    for label, color in enumerate(palette):
        color_seg[seg == label, :] = color
    color_seg = color_seg.astype(np.uint8)
    seg_image = Image.fromarray(color_seg).convert('RGB')
    return seg_image

def get_depth_pipeline():
    feature_extractor = AutoImageProcessor.from_pretrained("LiheYoung/depth-anything-large-hf", torch_dtype=dtype)
    depth_estimator = AutoModelForDepthEstimation.from_pretrained("LiheYoung/depth-anything-large-hf", torch_dtype=dtype).to(device)
    return feature_extractor, depth_estimator

@torch.inference_mode()
def get_depth_image(image: Image, feature_extractor: AutoImageProcessor, depth_estimator: AutoModelForDepthEstimation) -> Image:
    image_to_depth = feature_extractor(images=image, return_tensors="pt").to(device).to(dtype)
    with torch.no_grad():
        depth_map = depth_estimator(**image_to_depth).predicted_depth

    width, height = image.size
    depth_map = torch.nn.functional.interpolate(
        depth_map.unsqueeze(1).float(),
        size=(height, width),
        mode="bicubic",
        align_corners=False,
    )
    depth_min = torch.amin(depth_map, dim=[1, 2, 3], keepdim=True)
    depth_max = torch.amax(depth_map, dim=[1, 2, 3], keepdim=True)
    depth_map = (depth_map - depth_min) / (depth_max - depth_min)
    image = torch.cat([depth_map] * 3, dim=1)

    image = image.permute(0, 2, 3, 1).cpu().numpy()[0]
    image = Image.fromarray((image * 255.0).clip(0, 255).astype(np.uint8))
    return image

def resize_dimensions(dimensions, target_size):
    width, height = dimensions
    if width < target_size and height < target_size:
        return dimensions
    if width > height:
        aspect_ratio = height / width
        return (target_size, int(target_size * aspect_ratio))
    else:
        aspect_ratio = width / height
        return (int(target_size * aspect_ratio), target_size)

def flush():
    gc.collect()
    torch.cuda.empty_cache()

class ControlNetDepthDesignModelMulti:
    def __init__(self):
        self.seed = 323 * 111
        self.neg_prompt = "window, door, low resolution, banner, logo, watermark, text, deformed, blurry, out of focus, surreal, ugly, beginner"
        self.control_items = ["windowpane;window", "door;double;door"]
        self.additional_quality_suffix = "interior design, 4K, high resolution, photorealistic"
        
    def generate_design(self, empty_room_image: Image, prompt: str, guidance_scale: int = 10, num_steps: int = 50, strength: float = 0.9, img_size: int = 640) -> Image:
        print(prompt)
        flush()
        self.generator = torch.Generator(device=device).manual_seed(self.seed)

        pos_prompt = prompt + f', {self.additional_quality_suffix}'

        orig_w, orig_h = empty_room_image.size
        new_width, new_height = resize_dimensions(empty_room_image.size, img_size)
        input_image = empty_room_image.resize((new_width, new_height))
        real_seg = np.array(segment_image(input_image, seg_image_processor, image_segmentor))
        unique_colors = np.unique(real_seg.reshape(-1, real_seg.shape[2]), axis=0)
        unique_colors = [tuple(color) for color in unique_colors]
        segment_items = [map_colors_rgb(i) for i in unique_colors]
        chosen_colors, segment_items = filter_items(
            colors_list=unique_colors,
            items_list=segment_items,
            items_to_remove=self.control_items
        )
        mask = np.zeros_like(real_seg)
        for color in chosen_colors:
            color_matches = (real_seg == color).all(axis=2)
            mask[color_matches] = 1

        image_np = np.array(input_image)
        image = Image.fromarray(image_np).convert("RGB")
        mask_image = Image.fromarray((mask * 255).astype(np.uint8)).convert("RGB")
        segmentation_cond_image = Image.fromarray(real_seg).convert("RGB")

        image_depth = get_depth_image(image, depth_feature_extractor, depth_estimator)

        flush()
        new_width_ip = int(new_width / 8) * 8
        new_height_ip = int(new_height / 8) * 8
        ip_image = guide_pipe(pos_prompt,
                                   num_inference_steps=num_steps,
                                   negative_prompt=self.neg_prompt,
                                   height=new_height_ip,
                                   width=new_width_ip,
                                   generator=[self.generator]).images[0]

        flush()
        generated_image = pipe(
            prompt=pos_prompt,
            negative_prompt=self.neg_prompt,
            num_inference_steps=num_steps,
            strength=strength,
            guidance_scale=guidance_scale,
            generator=[self.generator],
            image=image,
            mask_image=mask_image,
            ip_adapter_image=ip_image,
            control_image=[image_depth, segmentation_cond_image],
            controlnet_conditioning_scale=[0.5, 0.5]
        ).images[0]
        
        flush()
        design_image = generated_image.resize(
            (orig_w, orig_h), Image.Resampling.LANCZOS
        )
        
        return design_image

def main():
    model = ControlNetDepthDesignModelMulti()
    print('Models uploaded successfully')
    
    # Load local images
    empty_room_image_path = "/Users/timdalxx/2024/zerodeling/backend/app/stabledesign/data/general_room/test_room.jpg"
    empty_room_image = Image.open(empty_room_image_path)

    # Example prompt
    prompt = "A stylish modern living room, warm color palette, 8K"
    prompt = "A simple and clean room, 8k, photorealistic"
    prompt = "A cozy and calming bedroom with soft blue and green colors, natural light, and comfortable furniture."
    prompt = "A bright and cheerful living room with yellow and orange accents, vibrant plants, and lots of natural light."
    prompt = "A bedroom with baby pink and white mood, and natural sunlight through large windows."
    # prompt =  "A warm and comforting bedroom with beige and cream tones, soft lighting, and personal memorabilia."

    # prompt = "cool mood"

    # Generate design
    design_image = model.generate_design(empty_room_image, prompt)
    
    # Save the generated image
    design_image_path = "generated_design_image_yh.png"
    design_image.save(design_image_path)
    print(f"Generated design image saved as '{design_image_path}'")

# Setup models
controlnet_depth = ControlNetModel.from_pretrained("controlnet_depth", torch_dtype=dtype, use_safetensors=True)
controlnet_seg = ControlNetModel.from_pretrained("own_controlnet", torch_dtype=dtype, use_safetensors=True)

pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
    "SG161222/Realistic_Vision_V5.1_noVAE",
    controlnet=[controlnet_depth, controlnet_seg],
    safety_checker=None,
    torch_dtype=dtype
)

pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")
pipe.set_ip_adapter_scale(0.4)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to(device)
guide_pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=dtype, use_safetensors=True, variant="fp16")
guide_pipe = guide_pipe.to(device)

seg_image_processor, image_segmentor = get_segmentation_pipeline()

depth_feature_extractor, depth_estimator = get_depth_pipeline()

if __name__ == '__main__':
    main()
