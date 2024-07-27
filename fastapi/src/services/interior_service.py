import json
from google.cloud import storage
from google.auth import load_credentials_from_file
from openai import OpenAI
from PIL import Image, ImageFile
from dotenv import load_dotenv
import datetime
import io
import os
import ast

from fastapi import HTTPException, UploadFile
import requests

load_dotenv()

credentials = load_credentials_from_file("bbangguzipggu-430108-8fb65a8f56a8.json")
credential = credentials[0]
project_id = credentials[1]

interior_url = os.getenv("INTERIOR_URL")
interior_api_key = os.getenv("INTERIOR_API_KEY")

open_ai_key = os.getenv("OPENAI_KEY")

async def upload_image_to_gcs(file: UploadFile):
    global credential, project_id

    # image resize
    ImageFile.LOAD_TRUNCATED_IMAGES = True  # Load truncated images if needed
    image = Image.open(file.file)
    new_size = (512,512)
    resized_image = image.resize(new_size, Image.Resampling.LANCZOS)  # Updated to LANCZOS

    byte_arr = io.BytesIO()
    resized_image.save(byte_arr, format='PNG')
    byte_arr.seek(0)


    client = storage.Client(credentials=credential)

    bucket_name = os.getenv("GCS_BUCKET_NAME")

    bucket = client.get_bucket(bucket_name)

    date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")

    filename = f"user_interior/{date}{file.filename}"

    blob = bucket.blob(filename)

    try:
        blob.upload_from_file(byte_arr, content_type=file.content_type)

        blob.make_public()

        gs_url = f"gs://{bucket_name}/user_interior/{filename}"

        return {"url": blob.public_url, "gs_url": gs_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
    
async def generate_interior_image(url: str, prompt: str):
    style_dict = generate_style_prompt(prompt)

    styled_prompt = ast.literal_eval(style_dict)["style_prompt"]

    payload = json.dumps({
        "key": interior_api_key,
        "init_image" : url,
        "prompt" : styled_prompt,
        "num_inference_steps" : 21,
        "base64" : "no",
        "guidance_scale" : 7,
    })

    headers = {
        'Content-Type': 'application/json'
    }

    res = requests.post(interior_url, headers=headers, data=payload)

    if res.status_code == 200:
        return (res.json())["output"][0]
    
    raise HTTPException(status_code=400, detail="Something Wrong")
    

def generate_style_prompt(user_prompt: str):
    client = OpenAI(api_key=open_ai_key)

    style_prompt_generator = """
    
    ### Role
    - 당신은 stable diffusion prompt engineer 입니다. 고품질의 이미지 결과를 위한 프롬프트 작성법을 잘 알고 있습니다.

    ### Objective
    - user 의 입력을 바탕으로, room style generation을 위한 style prompt 를 작성해주세요.

    ### Example
    user_input : 요즘따라 너무 우울한데, 기분전환하고 싶어. 나는 cozy 한 스타일을 원해.
    output : {"style_prompt" : "A cozy bright room, shiny, yellow mood, 4k, photorealistic", "reason" : "우울할 때는 밝은 방에서 따사로운 햇살을 받으며 기분전환을 하면 도움이 됩니다. 활기찬 노란색 가구를 구매해보시면 어떨까요?"}

    usesr_input : 멋진 방. 나는 modern 한 스타일을 원해.
    output: {"style_prompt": "A modern room, black mood, 4k, photorealistic", "reason" : "모던함과 멋짐이라는 단어에는 검정색이 잘 어울려요. 깊이있는 방의 분위기를 만들어보세요!"}

        
    """
    
    try:
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": style_prompt_generator},
            {"role": "user", "content": user_prompt}
        ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"
    
def generate_interior_class(interior_img_url : str):
    client = OpenAI(api_key=open_ai_key)
    
    interior_class_generator = """
    ### Role
    - 당신은 가구 전문 이미지 라벨러 입니다. 

    ### Objective
    - 가구 이미지를 보고 라벨을 Example 과 같은 형식으로 반환해주세요. 

    ### Example
    output : {"class" : "소파", "color" : "블랙", "material" : "우드", "size" : "None", "shape" :"원형"}

    ### Information
    - 가구의 class는 "침대, 책상, 의자, 소파, 커튼, 서랍장, 식물" 중 하나 입니다.
    - 가구가 침대인 경우 size 는 "싱글, 퀸, 킹" 중 하나입니다.
    - 가구가 서랍장인 경우 size는 "1단, 2단, 3단" 중 하나입니다.
    - 가구가 소파인 경우 size는 "1인용, 2인용, 패밀리" 중 하나입니다.
    - size와 shape는 식별하기 어려운 경우 "None" 으로 작성하세요.
    """
    
    try : 
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                "role": "user",
                "content": [
                    {"type": "text", "text": interior_class_generator},
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": interior_img_url
                    },
                    },
                ],
                }
            ],
            max_tokens=300,
        )

        return response.choices[0].message.content
    
    except Exception as e:
        return f"An error occurred: {e}"