from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel
from src.services.interior_service import *

interior_router = router = APIRouter()

class Prompt(BaseModel):
    prompt: str
    img_url: str

@router.post("/upload")
async def upload_img(file: UploadFile = File(...)):
    url_dict = await upload_image_to_gcs(file)

    return url_dict


@router.post("/generate")
async def generate_interior(body: Prompt):
    # url_dict = await upload_image_to_gcs(file)
    # url = url_dict["url"]
    
    url = body.img_url

    # prompt = Prompt(**json.loads(body))

    prompt = body.prompt

    print(url)

    print(prompt)

    gen_image_url = await generate_interior_image(url, prompt)

    gen_image_gcs_url = await upload_url_image_to_gcs(gen_image_url)

    res = await detect_obj_and_search(gen_image_url)

    return {"generatedImageUrl": gen_image_gcs_url, "result": res}

@router.post("/gcp")
async def upload_image(file: UploadFile = File(...)):
    url = await upload_image_to_gcs(file)

    return url["url"]

@router.get("/gen_image")
async def upload_image_url(image_url: str):
    res = await upload_url_image_to_gcs(image_url)
    
    return res

@router.post("/test")
async def test(body: Prompt):

    prompt = body.prompt

    return {
  "generatedImageUrl": {
    "url": "https://storage.googleapis.com/bbangggujipggu/generated_image/2024-09-03T14-47-28-469882",
    "gs_url": "gs://bbangggujipggu/generated_image/2024-09-03T14-47-28-469882"
  },
  "result": [
    {
      "label": "침대",
      "coordinate": [
        387,
        373.50000128
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-09-03T14-47-32-768131Bed",
      "items": [
        {
          "title": "소나무 원목 투톤 퀸<b>침대</b>",
          "productUrl": "https://shopping.naver.com/outlink/itemdetail/3471767422",
          "price": "860000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8101628/81016284559.jpg"
        },
        {
          "title": "콜로르 원목 투톤 퀸<b>침대</b>",
          "productUrl": "https://smartstore.naver.com/main/products/3471767421",
          "price": "860000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8101628/81016284558.jpg"
        },
        {
          "title": "[<b>침대</b>전문점] 까사나인 국내제작 클라우드 아쿠아스웨이드 킹 <b>퀸</b> 슈퍼싱글 <b>침대</b> 프레임",
          "productUrl": "https://shopping.naver.com/outlink/itemdetail/5188674563",
          "price": "580000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8273319/82733195895.2.jpg"
        },
        {
          "title": "[<b>침대</b>전문점] 까사나인 국내제작 클라우드 아쿠아스웨이드 킹 <b>퀸</b> 슈퍼싱글 <b>침대</b> 프레임",
          "productUrl": "https://smartstore.naver.com/main/products/5188674562",
          "price": "580000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8273319/82733195894.2.jpg"
        },
        {
          "title": "국내제작 샤벨 나비쿠션 신소재 페브릭 <b>침대</b>프레임 SS 맞춤제작",
          "productUrl": "https://smartstore.naver.com/main/products/3573084257",
          "price": "450000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8111760/81117601608.4.jpg"
        },
        {
          "title": "끌레오 피에르 패브릭 황토볼 흙<b>침대</b> 온열 황토<b>침대</b> Q CL463",
          "productUrl": "https://search.shopping.naver.com/catalog/41552665618",
          "price": "1869000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4155266/41552665618.20230801141153.jpg"
        }
      ]
    },
    {
      "label": "식물",
      "coordinate": [
        178,
        278.50000128
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-09-03T14-47-34-069852Houseplant",
      "items": [
        {
          "title": "알로카시아 무늬 프라이덱 <b>그린</b>벨벳 희귀<b>식물</b> 플랜테리어 공기정화<b>식물</b>",
          "productUrl": "https://smartstore.naver.com/main/products/9218188378",
          "price": "6800",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8676268/86762688701.jpg"
        },
        {
          "title": "알로카시아 프라이덱 <b>그린</b>벨벳 공기정화<b>식물</b> / OneGreenDay / 원<b>그린</b>데이",
          "productUrl": "https://smartstore.naver.com/main/products/5467770787",
          "price": "6900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8301226/83012265274.jpg"
        },
        {
          "title": "갑조네 알로카시아 <b>그린</b>벨벳 소품 프라이덱 희귀<b>식물</b> 실내공기정화<b>식물</b> 인테리어",
          "productUrl": "https://smartstore.naver.com/main/products/5739031836",
          "price": "5900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8328353/83283530784.jpg"
        },
        {
          "title": "필로덴드론 플로리다 뷰티<b>그린</b> 수입<b>식물</b> 희귀<b>식물</b> 유칼립투스 몬스테라 공기정화<b>식물</b> 279S",
          "productUrl": "https://smartstore.naver.com/main/products/4823053330",
          "price": "14890",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8236757/82367576182.jpg"
        },
        {
          "title": "호야콤팩트 바리에가타 마우나로 중투 희귀<b>식물</b> <b>그린</b>뜨락",
          "productUrl": "https://smartstore.naver.com/main/products/10362557502",
          "price": "48000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8790706/87907062163.jpg"
        },
        {
          "title": "<b>그린식물</b>팜 피닉스야자 대품 반려식물 야자 플랜테리어 60-80cm  1개",
          "productUrl": "https://link.coupang.com/re/PCSNAVERPCSDP?pageKey=8229154928&ctag=8229154928&lptag=I23677602498&itemId=23677602498&vendorItemId=90702810879&spec=10305199",
          "price": "19900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4942383/49423834653.jpg"
        },
        {
          "title": "나무플랜테리어 <b>그린 식물</b> 키큰",
          "productUrl": "https://link.gmarket.co.kr/gate/pcs?item-no=3978349129&sub-id=1003&service-code=10000003",
          "price": "42800",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4904416/49044164432.jpg"
        },
        {
          "title": "<b>그린식물</b>팜 립살리스 팝아이 뽀빠이 산호 공중식물 행이식물 50-70CM  1개",
          "productUrl": "https://link.coupang.com/re/PCSNAVERPCSDP?pageKey=8205441203&ctag=8205441203&lptag=I23534188219&itemId=23534188219&vendorItemId=90560452627&spec=10305199",
          "price": "15900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4926497/49264978198.jpg"
        },
        {
          "title": "<b>그린식물</b>팜 에피프레넘 바리에가타 에피프리넘 소품 무늬종  1개",
          "productUrl": "https://link.coupang.com/re/PCSNAVERPCSDP?pageKey=7703960505&ctag=7703960505&lptag=I20633884979&itemId=20633884979&vendorItemId=87707832637&spec=10305199",
          "price": "5900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4409363/44093638849.jpg"
        },
        {
          "title": "[플랫츠] 플랫츠 차리다에디션, <b>그린 식물</b>세트",
          "productUrl": "https://www.dplot.co.kr/shop/detail/0000010205",
          "price": "82000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4663552/46635523760.1.jpg"
        }
      ]
    }
  ]
}

# @router.get("/test")
# async def test():
#     return await detect_obj_and_search()