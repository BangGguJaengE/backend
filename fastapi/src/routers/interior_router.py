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

    gen_image_url = await generate_interior_image(url, prompt.prompt)

    await upload_url_image_to_gcs(gen_image_url)

    res = await detect_obj_and_search(gen_image_url)

    return {"generatedImageUrl": gen_image_url, "result": res}

@router.post("/gcp")
async def upload_image(file: UploadFile = File(...)):
    url = await upload_image_to_gcs(file)

    return url["url"]

@router.get("/gen_image")
async def upload_image_url(image_url: str):
    res = await upload_url_image_to_gcs(image_url)
    
    return res

@router.post("/test")
async def test(body: str = Form(...), file: UploadFile = File(...)):

    prompt = Prompt(**json.loads(body))

    return {
  "generatedImageUrl": "https://d9jy2smsrdjcq.cloudfront.net/generations/0-fcda6dff-a894-4b09-8283-940498d40bcd.png",
  "result": [
    {
      "label": "침대",
      "coordinate": [
        332,
        382
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-07-28T13-16-30-527753Couch",
      "items": [
        {
          "title": "슬립퍼 티라 <b>침대</b>프레임 슈퍼싱글 <b>퀸</b> 킹 라지킹 저상형 호텔 호텔형 <b>패브릭 침대</b>",
          "productUrl": "https://smartstore.naver.com/main/products/7761682726",
          "price": "387000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8530618/85306183048.4.jpg"
        },
        {
          "title": "퍼니코 빈 아쿠아텍스 <b>패브릭</b> 평상형 호텔 <b>침대</b> 프레임 슈퍼싱글 <b>퀸</b> 킹 라지킹 캘리포니아킹",
          "productUrl": "https://smartstore.naver.com/main/products/8536994771",
          "price": "249000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8608149/86081495094.7.jpg"
        },
        {
          "title": "퍼니코 샤르망 앤틱 매립형 벨벳 <b>패브릭 침대</b> 슈퍼싱글 <b>퀸</b> 킹",
          "productUrl": "https://smartstore.naver.com/main/products/4596292335",
          "price": "259000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8214081/82140812552.7.jpg"
        },
        {
          "title": "잉글랜더 마요 조야원단 <b>패브릭 침대</b>프레임 Q",
          "productUrl": "https://search.shopping.naver.com/catalog/34722132619",
          "price": "298000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_3472213/34722132619.20240426102205.jpg"
        },
        {
          "title": "철제<b>침대</b> 이케아 <b>침대</b> 저상형 슈퍼 싱글 <b>침대</b>프레임 <b>퀸</b> 킹 매트리스 깔판 받<b>침대</b> 마켓비",
          "productUrl": "https://smartstore.naver.com/main/products/5593366519",
          "price": "129000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8313786/83137862840.3.jpg"
        },
        {
          "title": "썸앤데코 데이지2 <b>패브릭 침대</b>프레임 Q/K 겸용",
          "productUrl": "https://search.shopping.naver.com/catalog/48003271618",
          "price": "1090000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4800327/48003271618.20240527172424.jpg"
        },
        {
          "title": "에덴느 호텔<b>침대</b>프레임 라지킹 이스턴킹 더블 <b>퀸</b> 트윈베드 신혼부부",
          "productUrl": "https://smartstore.naver.com/main/products/6742357888",
          "price": "489000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8428685/84286858210.4.jpg"
        },
        {
          "title": "2165 모던 스퀘어 도브<b>그레이 패브릭 침대</b> 퀸사이즈 / 킹사이즈",
          "productUrl": "https://smartstore.naver.com/main/products/7793768852",
          "price": "990000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8533826/85338269174.jpg"
        },
        {
          "title": "평상형 <b>침대</b>프레임 파운데이션 슈퍼싱글 <b>퀸</b> 킹 라지킹 저상형 무헤드 <b>침대</b> 깔판",
          "productUrl": "https://smartstore.naver.com/main/products/5048517273",
          "price": "262000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8259303/82593038357.11.jpg"
        },
        {
          "title": "밀레 호텔<b>침대</b> 프레임 <b>패브릭</b> 호텔식 라지킹 <b>퀸</b> 킹 트윈<b>침대</b> 평상형 led",
          "productUrl": "https://smartstore.naver.com/main/products/10353988847",
          "price": "589000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8789849/87898493320.1.jpg"
        }
      ]
    }
  ]
}

# @router.get("/test")
# async def test():
#     return await detect_obj_and_search()