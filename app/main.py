import requests
from PIL import Image, ImageFile
from starlette.datastructures import UploadFile as StarletteUploadFile
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

# Imgur 클라이언트 ID 설정 (Imgur API에서 발급받은 클라이언트 ID)
IMGUR_CLIENT_ID = ""


def resize_image(file: UploadFile) -> UploadFile:
    ImageFile.LOAD_TRUNCATED_IMAGES = True  # Load truncated images if needed
    image = Image.open(file.file)
    new_size = (512,512)
    resized_image = image.resize(new_size, Image.Resampling.LANCZOS)  # Updated to LANCZOS

    byte_arr = io.BytesIO()
    resized_image.save(byte_arr, format='PNG')
    byte_arr.seek(0)

    return StarletteUploadFile(file=byte_arr, filename=file.filename)

def upload_to_imgur(file: UploadFile) -> str:
    headers = {
        'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'
    }
    files = {
        'image': (file.filename, file.file, file.content_type)
    }
    response = requests.post("https://api.imgur.com/3/upload", headers=headers, files=files)
    data = response.json()
    if response.status_code == 200:
        return data['data']['link']
    else:
        return None

def process_image(file: UploadFile, style_prompt: str) -> dict:
    try:
        resized_file = resize_image(file)
        file_url = upload_to_imgur(resized_file)
        print(file_url)
        if not file_url:
            return {"error": "Failed to upload to Imgur"}

        url = "https://modelslab.com/api/v5/interior"
        payload = {
            "key": "",  # Insert your API key here
            "init_image": file_url,
            "prompt": style_prompt,
            "num_inference_steps": 21,
            "base64": "no",
            "guidance_scale": 7
        }
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to transform the image", "status_code": response.status_code}
    
    except Exception as e:
        return {"error": str(e)}

# FastAPI 애플리케이션 정의
app = FastAPI()

@app.post("/transform-room")
async def transform_room(file: UploadFile, style_prompt: str):
    result = process_image(file, style_prompt)
    return JSONResponse(content=result)

if __name__ == "__main__":
    # import uvicorn
    from pathlib import Path

    # # FastAPI 서버 실행
    # uvicorn.run(app, host="0.0.0.0", port=8000)

    # 기능 테스트
    test_image_path = "/Users/timdalxx/2024/zerodeling/backend/app/stabledesign/data/general_room/test_room.jpg"
    if Path(test_image_path).is_file():
        with open(test_image_path, "rb") as image_file:
            upload_file = UploadFile(filename=test_image_path, file=image_file)
            result = process_image(upload_file, "A modern room, photorealistic, 4k")
            print("Result:", result)
    else:
        print(f"Image file not found: {test_image_path}")
