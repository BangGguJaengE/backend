import requests
import json
from openai import OpenAI
from openai_key import OPENAI_KEY
from interior_key import INTERIOR_KEY
import ast


def generate_interior_image(url: str, prompt: str):
    payload = json.dumps({
        "key": INTERIOR_KEY,
        "init_image" : url,
        "prompt" : prompt,
        "num_inference_steps" : 31,
        "base64" : "no",
        "guidance_scale" : 7,
    })

    headers = {
        'Content-Type': 'application/json'
    }

    res = requests.post(interior_url, headers=headers, data=payload)
    print(res.json())
    
    if res.status_code == 200:
        return (res.json())["output"][0]
    
def generate_interior_class(interior_img_url : str):
    client = OpenAI(api_key=OPENAI_KEY)
    
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
    
def generate_style_prompt(user_prompt: str):
    client = OpenAI(api_key=OPENAI_KEY)

    style_prompt_generator = """
    ### Role
    - 당신은 stable diffusion prompt engineer 입니다. 고품질의 이미지 결과를 위한 프롬프트 작성법을 잘 알고 있습니다.

    ### Objective
    - user 의 입력을 바탕으로, room style generation을 위한 style prompt 를 작성해주세요.

    ### Example
    user_input : 요즘따라 너무 우울한데, 기분전환하고 싶어. 나는 cozy 한 스타일을 원해.
    output : {"style_prompt" : "A cozy bright room, shiny, yellow mood, 4k, photorealistic, masterpiece, super realistic, best quality, raw photo", "reason" : "우울할 때는 밝은 방에서 따사로운 햇살을 받으며 기분전환을 하면 도움이 됩니다. 활기찬 노란색 가구를 구매해보시면 어떨까요?"}

    usesr_input : 멋진 방. 나는 modern 한 스타일을 원해.
    output: {"style_prompt": "A modern room, black mood, 4k, photorealistic, masterpiece, super realistic, best quality, raw photo", "reason" : "모던함과 멋짐이라는 단어에는 검정색이 잘 어울려요. 깊이있는 방의 분위기를 만들어보세요!"}

    ### Information
    - 창문에 관련된 내용은 넣지 마세요. 그 밖에도 현실적인 스타일 프롬프트를 작성하세요.
    - 사용자의 입력 중 우울함, 슬픔, 스트레스 중 하나로 보이는 경우, 이를 완화할 수 있도록 아래 매핑 정보를 활용하세요.
        - 우울감 : combination of warm white light with blue–yellow or green–yellow light
        - 슬픔 : warm white light
        - 스트레스 : cool white light and blue-green light
    - colorful 스타일을 원하는 경우, colorful 라는 단어는 절대 넣지 말고, green sofa 혹은 pink chair 같이 특정 가구나 소품에만 색깔 포인트를 넣어주세요.
    - planterior 스타일을 원하는 경우, planterior 라는 단어는 절대 넣지 말고, with 1 minimal plants 만 추가해주세요.
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
    
    
    
if __name__ == "__main__":
    
    # style prompt generation
    interior_url = "https://modelslab.com/api/v5/interior"
    # image_url = "https://raw.githubusercontent.com/BangGguJaengE/backend/main/interior-generator/stabledesign/data/general_room/test_room_resize.jpg"
    image_url = "https://storage.googleapis.com/bbangggujipggu/friends_room/a.jpeg"
    user_prompt = "기분이 좀 안좋아서 기분전환 하고 싶어.. 나는 핑쿠 좋아해. 나는 colorful 한 스타일을 원해."
    style_dict = generate_style_prompt(user_prompt)
    print(style_dict)
    style_prompt = ast.literal_eval(style_dict)["style_prompt"]
    print(style_prompt)
    
    # image generation
    output_url = generate_interior_image(image_url, style_prompt)
    print(output_url)
    
    # style class generation
    # object_url = "https://raw.githubusercontent.com/BangGguJaengE/backend/main/interior-generator/data/bed.png"
    # interior_dict_str = generate_interior_class(object_url)
    # interior_dict = ast.literal_eval(interior_dict_str)
    # print(interior_dict)
