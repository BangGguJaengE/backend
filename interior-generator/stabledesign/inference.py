from typing import Tuple, Union, List
import numpy as np
from PIL import Image
import torch
from diffusers import ControlNetModel, StableDiffusionControlNetInpaintPipeline, UniPCMultistepScheduler, StableDiffusionXLPipeline
from transformers import AutoImageProcessor, UperNetForSemanticSegmentation, AutoModelForDepthEstimation
import gc
from colors import ade_palette
from utils import map_colors_rgb


# Device and precision settings
device = "cuda"
dtype = torch.float16

# Helper functions for garbage collection and device memory management
def flush():
    gc.collect()
    torch.cuda.empty_cache()

# Function to filter out specific items based on their color
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

# Image segmentation setup and processing
def get_segmentation_pipeline() -> Tuple[AutoImageProcessor, UperNetForSemanticSegmentation]:
    image_processor = AutoImageProcessor.from_pretrained("openmmlab/upernet-convnext-small")
    image_segmentor = UperNetForSemanticSegmentation.from_pretrained("openmmlab/upernet-convnext-small").to(device).to(dtype)
    return image_processor, image_segmentor

@torch.inference_mode()
def segment_image(image: Image, image_processor: AutoImageProcessor, image_segmentor: UperNetForSemanticSegmentation) -> Image:
    pixel_values = image_processor(image, return_tensors="pt").pixel_values.to(device).to(dtype)
    outputs = image_segmentor(pixel_values)
    seg = image_processor.post_process_semantic_segmentation(outputs, target_sizes=[image.size[::-1]])[0]
    seg = seg.cpu().numpy()
    color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)
    palette = np.array(ade_palette())
    for label, color in enumerate(palette):
        color_seg[seg == label, :] = color
    color_seg = color_seg.astype(np.uint8)
    seg_image = Image.fromarray(color_seg).convert('RGB')
    return seg_image

# Depth estimation setup and processing
def get_depth_pipeline():
    feature_extractor = AutoImageProcessor.from_pretrained("LiheYoung/depth-anything-large-hf", torch_dtype=dtype)
    depth_estimator = AutoModelForDepthEstimation.from_pretrained("LiheYoung/depth-anything-large-hf", torch_dtype=dtype).to(device)
    return feature_extractor, depth_estimator

@torch.inference_mode()
def get_depth_image(image: Image, feature_extractor: AutoImageProcessor, depth_estimator: AutoModelForDepthEstimation) -> Image:
    image_to_depth = feature_extractor(images=image, return_tensors="pt").to(device).to(dtype)
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

# Utility function for resizing image dimensions while maintaining aspect ratio
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

# Main class for generating room designs using control networks
class ControlNetDepthDesignModelMulti:
    def __init__(self):
        self.seed = 323 * 111
        self.neg_prompt = "window, door, low resolution, banner, logo, watermark, text, deformed, blurry, out of focus, surreal, ugly, beginner"
        self.control_items = ["windowpane;window", "door;double;door"]
        self.additional_quality_suffix = "interior design, 4K, high resolution, photorealistic"
        self._initialize_models()
        
    def _initialize_models(self):
        # Initialize and set up models
        self.controlnet_depth = ControlNetModel.from_pretrained("controlnet_depth", torch_dtype=dtype, use_safetensors=True)
        self.controlnet_seg = ControlNetModel.from_pretrained("controlnet", torch_dtype=dtype, use_safetensors=True)

        self.pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
            "SG161222/Realistic_Vision_V5.1_noVAE",
            controlnet=[self.controlnet_depth, self.controlnet_seg],
            safety_checker=None,
            torch_dtype=dtype
        )

        self.pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")
        self.pipe.set_ip_adapter_scale(0.4)
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.pipe = self.pipe.to(device)
        self.guide_pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=dtype, use_safetensors=True, variant="fp16")
        self.guide_pipe = self.guide_pipe.to(device)

        self.seg_image_processor, self.image_segmentor = get_segmentation_pipeline()

        self.depth_feature_extractor, self.depth_estimator = get_depth_pipeline()
        
    def generate_design(self, empty_room_image: Image, prompt: str, guidance_scale: int = 10, num_steps: int = 50, strength: float = 0.9, img_size: int = 640) -> Image:
        flush()
        self.generator = torch.Generator(device=device).manual_seed(self.seed)

        pos_prompt = prompt + f', {self.additional_quality_suffix}'

        orig_w, orig_h = empty_room_image.size
        new_width, new_height = resize_dimensions(empty_room_image.size, img_size)
        input_image = empty_room_image.resize((new_width, new_height))
        real_seg = np.array(segment_image(input_image, self.seg_image_processor, self.image_segmentor))
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

        image_depth = get_depth_image(image, self.depth_feature_extractor, self.depth_estimator)

        flush()
        new_width_ip = int(new_width / 8) * 8
        new_height_ip = int(new_height / 8) * 8
        ip_image = self.guide_pipe(pos_prompt,
                                   num_inference_steps=num_steps,
                                   negative_prompt=self.neg_prompt,
                                   height=new_height_ip,
                                   width=new_width_ip,
                                   generator=[self.generator]).images[0]

        flush()
        generated_image = self.pipe(
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

# Main execution
if __name__ == "__main__":
    # Define input image path and prompt
    empty_room_image_path = "/Users/timdalxx/2024/zerodeling/backend/app/stabledesign/data/general_room/test_room.jpg"
    prompt = "A stylish modern living room, warm color palette, 4K resolution"
    
    # Load the image
    empty_room_image = Image.open(empty_room_image_path)

    # Initialize the model and generate design
    model = ControlNetDepthDesignModelMulti()
    design_image = model.generate_design(empty_room_image, prompt)
    
    # Save the generated image
    design_image_path = "/Users/timdalxx/2024/zerodeling/backend/app/stabledesign/data/general_room/generated_design_image.png"
    design_image.save(design_image_path)
    print(f"Generated design image saved as '{design_image_path}'")
