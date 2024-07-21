import spaces
from typing import Tuple, Union, List
import os

import numpy as np
from PIL import Image

import torch
from diffusers.pipelines.controlnet import StableDiffusionControlNetInpaintPipeline
from diffusers import ControlNetModel, UniPCMultistepScheduler, AutoPipelineForText2Image
from transformers import AutoImageProcessor, UperNetForSemanticSegmentation, AutoModelForDepthEstimation
from colors import ade_palette
from utils import map_colors_rgb
from diffusers import StableDiffusionXLPipeline
import gradio as gr
import gc

device = "cuda"
dtype = torch.float16

        
css = """
#img-display-container {
    max-height: 50vh;
    }
#img-display-input {
    max-height: 40vh;
    }
#img-display-output {
    max-height: 40vh;
    }

"""


def filter_items(
    colors_list: Union[List, np.ndarray],
    items_list: Union[List, np.ndarray],
    items_to_remove: Union[List, np.ndarray]
) -> Tuple[Union[List, np.ndarray], Union[List, np.ndarray]]:
    """
    Filters items and their corresponding colors from given lists, excluding
    specified items.

    Args:
        colors_list: A list or numpy array of colors corresponding to items.
        items_list: A list or numpy array of items.
        items_to_remove: A list or numpy array of items to be removed.

    Returns:
        A tuple of two lists or numpy arrays: filtered colors and filtered
        items.
    """
    filtered_colors = []
    filtered_items = []
    for color, item in zip(colors_list, items_list):
        if item not in items_to_remove:
            filtered_colors.append(color)
            filtered_items.append(item)
    return filtered_colors, filtered_items

def get_segmentation_pipeline(
) -> Tuple[AutoImageProcessor, UperNetForSemanticSegmentation]:
    """Method to load the segmentation pipeline
    Returns:
        Tuple[AutoImageProcessor, UperNetForSemanticSegmentation]: segmentation pipeline
    """
    image_processor = AutoImageProcessor.from_pretrained(
        "openmmlab/upernet-convnext-small"
    )
    image_segmentor = UperNetForSemanticSegmentation.from_pretrained(
        "openmmlab/upernet-convnext-small"
    )
    return image_processor, image_segmentor


@torch.inference_mode()
@spaces.GPU
def segment_image(
        image: Image,
        image_processor: AutoImageProcessor,
        image_segmentor: UperNetForSemanticSegmentation
) -> Image:
    """
    Segments an image using a semantic segmentation model.

    Args:
        image (Image): The input image to be segmented.
        image_processor (AutoImageProcessor): The processor to prepare the
            image for segmentation.
        image_segmentor (UperNetForSemanticSegmentation): The semantic
            segmentation model used to identify different segments in the image.

    Returns:
        Image: The segmented image with each segment colored differently based
            on its identified class.
    """
    # image_processor, image_segmentor = get_segmentation_pipeline()
    pixel_values = image_processor(image, return_tensors="pt").pixel_values
    with torch.no_grad():
        outputs = image_segmentor(pixel_values)

    seg = image_processor.post_process_semantic_segmentation(
        outputs, target_sizes=[image.size[::-1]])[0]
    color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)
    palette = np.array(ade_palette())
    for label, color in enumerate(palette):
        color_seg[seg == label, :] = color
    color_seg = color_seg.astype(np.uint8)
    seg_image = Image.fromarray(color_seg).convert('RGB')
    return seg_image


def get_depth_pipeline():
    feature_extractor = AutoImageProcessor.from_pretrained("LiheYoung/depth-anything-large-hf",
                                                           torch_dtype=dtype)
    depth_estimator = AutoModelForDepthEstimation.from_pretrained("LiheYoung/depth-anything-large-hf",
                                                                  torch_dtype=dtype)
    return feature_extractor, depth_estimator


@torch.inference_mode()
@spaces.GPU
def get_depth_image(
        image: Image,
        feature_extractor: AutoImageProcessor,
        depth_estimator: AutoModelForDepthEstimation
) -> Image:
    image_to_depth = feature_extractor(images=image, return_tensors="pt").to(device)
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
    """ 
    Resize PIL to target size while maintaining aspect ratio 
    If smaller than target size leave it as is
    """
    width, height = dimensions

    # Check if both dimensions are smaller than the target size
    if width < target_size and height < target_size:
        return dimensions

    # Determine the larger side
    if width > height:
        # Calculate the aspect ratio
        aspect_ratio = height / width
        # Resize dimensions
        return (target_size, int(target_size * aspect_ratio))
    else:
        # Calculate the aspect ratio
        aspect_ratio = width / height
        # Resize dimensions
        return (int(target_size * aspect_ratio), target_size)


def flush():
    gc.collect()
    torch.cuda.empty_cache()
    
    
class ControlNetDepthDesignModelMulti:
    """ Produces random noise images """
    
    def __init__(self):
        """ Initialize your model(s) here """
        #os.environ['HF_HUB_OFFLINE'] = "True"
        
        self.seed = 323*111
        self.neg_prompt = "window, door, low resolution, banner, logo, watermark, text, deformed, blurry, out of focus, surreal, ugly, beginner"
        self.control_items = ["windowpane;window", "door;double;door"]
        self.additional_quality_suffix = "interior design, 4K, high resolution, photorealistic"
        
    @spaces.GPU
    def generate_design(self, empty_room_image: Image, prompt: str, guidance_scale: int = 10, num_steps: int = 50, strength: float =0.9, img_size: int = 640) -> Image:
        """
        Given an image of an empty room and a prompt
        generate the designed room according to the prompt
        Inputs - 
            empty_room_image - An RGB PIL Image of the empty room
            prompt - Text describing the target design elements of the room
        Returns - 
            design_image - PIL Image of the same size as the empty room image
                           If the size is not the same the submission will fail.
        """
        print(prompt)
        flush()
        self.generator = torch.Generator(device=device).manual_seed(self.seed)

        pos_prompt = prompt + f', {self.additional_quality_suffix}'

        orig_w, orig_h = empty_room_image.size
        new_width, new_height = resize_dimensions(empty_room_image.size, img_size)
        input_image = empty_room_image.resize((new_width, new_height))
        real_seg = np.array(segment_image(input_image,
                                          seg_image_processor,
                                          image_segmentor))
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

        # generate image that would be used as IP-adapter
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


def create_demo(model):
    gr.Markdown("### Stable Design demo")
    with gr.Row():
        with gr.Column():
            input_image = gr.Image(label="Input Image", type='pil', elem_id='img-display-input')
            input_text = gr.Textbox(label='Prompt', placeholder='Please upload your image first', lines=2)
            with gr.Accordion('Advanced options', open=False):
                num_steps = gr.Slider(label='Steps',
                                      minimum=1,
                                      maximum=50,
                                      value=50,
                                      step=1)
                img_size = gr.Slider(label='Image size',
                                      minimum=256,
                                      maximum=768,
                                      value=768,
                                      step=64)
                guidance_scale = gr.Slider(label='Guidance Scale',
                                           minimum=0.1,
                                           maximum=30.0,
                                           value=10.0,
                                           step=0.1)
                seed = gr.Slider(label='Seed',
                                 minimum=-1,
                                 maximum=2147483647,
                                 value=323*111,
                                 step=1,
                                 randomize=True)
                strength = gr.Slider(label='Strength',
                                           minimum=0.1,
                                           maximum=1.0,
                                           value=0.9,
                                           step=0.1)
                a_prompt = gr.Textbox(
                    label='Added Prompt',
                    value="interior design, 4K, high resolution, photorealistic")
                n_prompt = gr.Textbox(
                    label='Negative Prompt',
                    value="window, door, low resolution, banner, logo, watermark, text, deformed, blurry, out of focus, surreal, ugly, beginner")
            submit = gr.Button("Submit")
        
        with gr.Column():
            design_image = gr.Image(label="Output Mask", elem_id='img-display-output')
    
    
    def on_submit(image, text, num_steps, guidance_scale, seed, strength, a_prompt, n_prompt, img_size):
        model.seed = seed
        model.neg_prompt = n_prompt
        model.additional_quality_suffix = a_prompt
        
        with torch.no_grad():
            out_img = model.generate_design(image, text, guidance_scale=guidance_scale, num_steps=num_steps, strength=strength, img_size=img_size)

        return out_img

    submit.click(on_submit, inputs=[input_image, input_text, num_steps, guidance_scale, seed, strength, a_prompt, n_prompt, img_size], outputs=design_image)
    examples = gr.Examples(examples=[["imgs/bedroom_1.jpg", "An elegantly appointed bedroom in the Art Deco style, featuring a grand king-size bed with geometric bedding, a luxurious velvet armchair, and a mirrored nightstand that reflects the room's opulence. Art Deco-inspired artwork adds a touch of glamour"], ["imgs/bedroom_2.jpg", "A bedroom that exudes French country charm with a soft upholstered bed, walls adorned with floral wallpaper, and a vintage wooden wardrobe. A crystal chandelier casts a warm, inviting glow over the space"], ["imgs/dinning_room_1.jpg", "A cozy dining room that captures the essence of rustic charm with a solid wooden farmhouse table at its core, surrounded by an eclectic mix of mismatched chairs. An antique sideboard serves as a statement piece, and the ambiance is warmly lit by a series of quaint Edison bulbs dangling from the ceiling"], ["imgs/dinning_room_3.jpg", "A dining room that epitomizes contemporary elegance, anchored by a sleek, minimalist dining table paired with stylish modern chairs. Artistic lighting fixtures create a focal point above, while the surrounding minimalist decor ensures the space feels open, airy, and utterly modern"], ["imgs/image_1.jpg", "A glamorous master bedroom in Hollywood Regency style, boasting a plush tufted headboard, mirrored furniture reflecting elegance, luxurious fabrics in rich textures, and opulent gold accents for a touch of luxury."], ["imgs/image_2.jpg", "A vibrant living room with a tropical theme, complete with comfortable rattan furniture, large leafy plants bringing the outdoors in, bright cushions adding pops of color, and bamboo blinds for natural light control."], ["imgs/living_room_1.jpg", "A stylish living room embracing mid-century modern aesthetics, featuring a vintage teak coffee table at its center, complemented by a classic sunburst clock on the wall and a cozy shag rug underfoot, creating a warm and inviting atmosphere"]],
                           inputs=[input_image, input_text], cache_examples=False)


controlnet_depth= ControlNetModel.from_pretrained(
    "controlnet_depth", torch_dtype=dtype, use_safetensors=True)
controlnet_seg = ControlNetModel.from_pretrained(
    "own_controlnet", torch_dtype=dtype, use_safetensors=True)

pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
    "SG161222/Realistic_Vision_V5.1_noVAE",
    #"models/runwayml--stable-diffusion-inpainting",
    controlnet=[controlnet_depth, controlnet_seg],
    safety_checker=None,
    torch_dtype=dtype
)

pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models",
                     weight_name="ip-adapter_sd15.bin")
pipe.set_ip_adapter_scale(0.4)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to(device)
guide_pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B",
                                                       torch_dtype=dtype, use_safetensors=True, variant="fp16")
guide_pipe = guide_pipe.to(device)
   
seg_image_processor, image_segmentor = get_segmentation_pipeline()
depth_feature_extractor, depth_estimator = get_depth_pipeline()
depth_estimator = depth_estimator.to(device)


def main():
    model = ControlNetDepthDesignModelMulti()
    print('Models uploaded successfully')
    
    title = "# StableDesign"
    description = """
    <p style='font-size: 14px; margin-bottom: 10px;'><a href='https://www.linkedin.com/in/mykola-lavreniuk/'>Mykola Lavreniuk</a>, <a href='https://www.linkedin.com/in/bartosz-ludwiczuk-a677a760/'>Bartosz Ludwiczuk</a></p>
    <p style='font-size: 16px; margin-bottom: 0px; margin-top=0px;'>Official demo for <strong>StableDesign:</strong> 2nd place solution for the Generative Interior Design 2024 <a href='https://www.aicrowd.com/challenges/generative-interior-design-challenge-2024/leaderboards?challenge_round_id=1314'>competition</a>. StableDesign is a deep learning model designed to harness the power of AI, providing innovative and creative tools for designers. Using our algorithms, images of empty rooms can be transformed into fully furnished spaces based on text descriptions. Please refer to our <a href='https://github.com/Lavreniuk/generative-interior-design'>GitHub</a> for more details.</p>
    """
    with gr.Blocks() as demo:
        gr.Markdown(title)
        gr.Markdown(description)
        
        create_demo(model)
        gr.HTML('''<br><br><br><center>You can duplicate this Space to skip the queue:<a href="https://huggingface.co/spaces/MykolaL/StableDesign?duplicate=true"><img src="https://bit.ly/3gLdBN6" alt="Duplicate Space"></a><br>
                <p><img src="https://visitor-badge.glitch.me/badge?page_id=MykolaL/StableDesign" alt="visitors"></p></center>''')

    demo.queue().launch(share=False)


if __name__ == '__main__':
    main()
