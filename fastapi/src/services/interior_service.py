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
from src.google.object_detection import ObjectDetection

from src.mock.object_detection import mock_object_detection
from src.services.product_service import get_product_from_naver_shopping

load_dotenv()

credentials = load_credentials_from_file("bbangguzipggu-430108-8fb65a8f56a8.json")
credential = credentials[0]
project_id = credentials[1]

interior_url = os.getenv("INTERIOR_URL")
interior_api_key = os.getenv("INTERIOR_API_KEY")

open_ai_key = os.getenv("OPENAI_KEY")

async def detect_obj_and_search(image_url):
    print("image url")
    print(image_url)

    
    dic_list = ObjectDetection.detect_objects(image_url)

    print("dic list")
    print(dic_list)


    # dic_list = mock_object_detection()

    # Object Detection 된 이미지를 gcp에 업로드
    for dic in dic_list:
        file_stream = io.BytesIO()
        dic["image"].save(file_stream, format="PNG")
        file_stream.seek(0)
    
        object_url = (await upload_byte_image_to_gcs(file_stream, dic["label"]))["url"]
        dic["image_url"] = object_url

    # object url을 이용하여 탐지된 object에서 특징 추출(캡셔닝) 후, 특징 기반으로 검색
    for dic in dic_list:
        object_url = dic["image_url"]
        interior_dict_str=generate_interior_class(object_url)
        
        try:
            interior_dict = ast.literal_eval(interior_dict_str)
        except Exception as e:
            interior_dict_str=generate_interior_class(object_url)
            interior_dict = ast.literal_eval(interior_dict_str)

        size = "" if interior_dict["size"] == "None" else interior_dict["size"]

        shape = "" if interior_dict["shape"] == "None" else f" {interior_dict["shape"]}"

        keyword = f"{size}{shape} {interior_dict["color"]} {interior_dict["material"]} {interior_dict["class"]}"

        print(f"search keyword : {keyword}")
        print(f"class : {interior_dict["class"]}")

        products_dict_list = await get_product_from_naver_shopping(keyword, 1, 10, interior_dict["class"])

        # 검색 후, 이미지 유사도 검색 (일단 보류)
        
        items = list(map(lambda x: { "title":x["title"], "productUrl": x["link"], "price": x["lprice"], "imageUrl": x["image"] } ,products_dict_list))

        dic["label"] = interior_dict["class"]
        dic["items"] = items
        del dic["image"]
        del dic["bounding_box"]
        
    for i in dic_list:
        print()
        print("dict list")
        print(i)

    return dic_list

async def upload_byte_image_to_gcs(image: io.BytesIO, label: str):

    content_type = "image/png"

    client = storage.Client(credentials=credential)

    bucket_name = os.getenv("GCS_BUCKET_NAME")

    bucket = client.get_bucket(bucket_name)

    date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")

    filename = f"detected_object/{date}{label}"

    blob = bucket.blob(filename)

    try:
        blob.upload_from_file(image, content_type=content_type)

        blob.make_public()

        gs_url = f"gs://{bucket_name}/detected_object/{filename}"

        return {"url": blob.public_url, "gs_url": gs_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
    

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

    try:
        styled_prompt = ast.literal_eval(style_dict)["style_prompt"]
    except Exception as e:
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
    - 가구의 class는 "침대, 책상, 의자, 소파, 커튼, 서랍장, 식물, 조명, 베개" 중 하나 입니다.
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


# 1. 생성된 이미지의 url을 이용해서 Object Detection을 한다. (중심좌표, 이미지, label)

# 2. Detection된 Object들을 dictionary 형태로 중심 좌표값과 함께 이미지 데이터(아마 nparray 형식)를 보낸다.
# 3. detection된 이미지 데이터를 gcp에 업로드한다.
# 4. 업로드된 이미지 url을 이용해 이미지 캡셔닝을 진행한다.
# 5. 이미지 캡셔닝을 통해 나온 결과 값으로 naver 쇼핑 api에 검색을 진행한다. (이때, 카테고리로 필터링 진행)
# 6. 검색 결과를 바탕으로 이미지 유사도 검사를 진행하여 유사도가 제일 높은 top 10개의 상품을 보여준다.

# 7. 2~6의 과정을 Object Detection된 객체의 수만큼 반복한다.
# 8. 결과 값 : { generated_image_url, items:[{ 중심좌표, 유사한 상품 목록(imageUrl, 상품url, price, title)}]} 를 프론트로 넘겨준다.

# 고려사항 : 중심좌표가 겹치는 경우는? -> 프론트에서 처리해야할듯