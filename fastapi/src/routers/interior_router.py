from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel
from src.services.interior_service import *

interior_router = router = APIRouter()

class Prompt(BaseModel):
    prompt: str


@router.post("/generate")
async def generate_interior(body: str = Form(...), file: UploadFile = File(...)):
    url_dict = await upload_image_to_gcs(file)
    url = url_dict["url"]
    
    prompt = Prompt(**json.loads(body))

    print(url)

    print(prompt.prompt)

    res = await generate_interior_image(url, prompt.prompt)

    return res

@router.post("/gcp")
async def upload_image(file: UploadFile = File(...)):
    url = await upload_image_to_gcs(file)

    return url["url"]