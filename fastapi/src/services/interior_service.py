import json
from google.cloud import storage
from google.auth import load_credentials_from_file
from PIL import Image, ImageFile
from dotenv import load_dotenv
import datetime
import io
import os

from fastapi import HTTPException, UploadFile
import requests

load_dotenv()

credentials = load_credentials_from_file("bbangguzipggu-430108-8fb65a8f56a8.json")
credential = credentials[0]
project_id = credentials[1]

interior_url = os.getenv("INTERIOR_URL")
interior_api_key = os.getenv("INTERIOR_API_KEY")

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
    payload = json.dumps({
        "key": interior_api_key,
        "init_image" : url,
        "prompt" : prompt,
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
    

