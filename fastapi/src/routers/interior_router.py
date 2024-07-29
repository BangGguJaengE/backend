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
  "generatedImageUrl": "https://d9jy2smsrdjcq.cloudfront.net/generations/0-ebb56320-eba3-4dae-b03e-8bc32971e19a.png",
  "result": [
    {
      "label": "소파",
      "coordinate": [
        359.50000128,
        391
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-07-29T19-54-06-147726Couch",
      "items": [
        {
          "title": "에보니아 루비 2인 <b>패브릭소파</b>",
          "productUrl": "https://search.shopping.naver.com/catalog/8014189833",
          "price": "105600",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8014189/8014189833.20240503101626.jpg"
        },
        {
          "title": "장인가구 콤마 기능성 아쿠아 2인 <b>패브릭 소파</b>",
          "productUrl": "https://search.shopping.naver.com/catalog/45834458620",
          "price": "152640",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4583445/45834458620.20240215154030.jpg"
        },
        {
          "title": "에보니아 뮤즈 2인 <b>패브릭 소파</b> 스툴포함",
          "productUrl": "https://search.shopping.naver.com/catalog/17309714958",
          "price": "136400",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_1730971/17309714958.20221018114919.jpg"
        },
        {
          "title": "에보니아 라떼 2인 <b>패브릭소파</b>",
          "productUrl": "https://search.shopping.naver.com/catalog/8764943398",
          "price": "99810",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8764943/8764943398.20240503101453.jpg"
        },
        {
          "title": "<b>패브릭</b>쇼파 2인 <b>소파</b> 미니 1인 <b>소파</b> 마켓비 다이닝 이케아 쇼파 3인용 4인",
          "productUrl": "https://smartstore.naver.com/main/products/5078401500",
          "price": "119000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8262292/82622923198.6.jpg"
        },
        {
          "title": "장인가구 콤마 기능성 아쿠아 2인 <b>패브릭 소파</b> 스툴포함",
          "productUrl": "https://smartstore.naver.com/main/products/9179178763",
          "price": "209000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8672367/86723679086.1.jpg"
        },
        {
          "title": "카페쇼파 데니쉬 2인 <b>브라운 패브릭소파</b> 부클레 의자 프랜차이즈",
          "productUrl": "http://chairhd.kr/?ca=product&page=view&auto_id=16302&c_id=240&cm_id=4916302_3618_20240412_YSJ_UH&nt_source=naver.ads&nt_medium=naver.shopping",
          "price": "825000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4706831/47068318084.jpg"
        },
        {
          "title": "에보니아 브릿지 라텍스폼 2인 <b>패브릭</b> 카우치 <b>소파</b>",
          "productUrl": "https://search.shopping.naver.com/catalog/26159679522",
          "price": "149490",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_2615967/26159679522.20210226140019.jpg"
        },
        {
          "title": "슬로 원목 기능성 아쿠아스웨이드 <b>패브릭</b> 1인/2인/3인 <b>소파</b>",
          "productUrl": "https://smartstore.naver.com/main/products/6926460037",
          "price": "116900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8447096/84470960359.2.jpg"
        },
        {
          "title": "데니쉬 2인 <b>브라운 패브릭</b> 부클레 <b>소파</b>페브릭 학원 의자",
          "productUrl": "http://chairhd.kr/?ca=product&page=view&auto_id=16302&c_id=240&cm_id=10016302_8474_20240710_YSJ_UH&nt_source=naver.ads&nt_medium=naver.shopping",
          "price": "825000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4906708/49067082381.jpg"
        }
      ]
    },
    {
      "label": "의자",
      "coordinate": [
        117.18750131200001,
        348.50000128
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-07-29T19-54-07-713751Chair",
      "items": [
        {
          "title": "몽키<b>우드</b> 리베르체어 월넛 식탁<b>의자</b> <b>베이지</b>",
          "productUrl": "https://www.leweekend.co.kr/goods/goods_view.php?goodsNo=75377&inflow=naver",
          "price": "450000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4761419/47614196218.jpg"
        },
        {
          "title": "한성 IM 로이스<b>우드의자</b> 그레이 <b>베이지</b>",
          "productUrl": "https://hansunggagu.com/product/detail.html?product_no=14394&cate_no=204&display_group=1&cafe_mkt=naver_ks&mkt_in=Y&ghost_mall_id=naver&ref=naver_open",
          "price": "140800",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4640576/46405763144.jpg"
        },
        {
          "title": "데온 고무나무 원목 패브릭 <b>의자</b> 체어 <b>우드</b> 까페 카페 현관 가구 크림<b>베이지</b>",
          "productUrl": "https://search.shopping.naver.com/catalog/48626313646",
          "price": "163760",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4862631/48626313646.20240622200352.jpg"
        },
        {
          "title": "독특한 회전 <b>의자</b> 예쁜 원목 식탁<b>의자</b> 고급스러운 <b>우드</b> 체어 월넛 <b>베이지</b>",
          "productUrl": "https://smartstore.naver.com/main/products/5838469711",
          "price": "129800",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8338296/83382969125.jpg"
        },
        {
          "title": "파스텔<b>우드</b> 세스카 라탄 카페 철재 식탁<b>의자</b>  <b>베이지</b>",
          "productUrl": "https://link.coupang.com/re/PCSNAVERPCSDP?pageKey=7358095616&ctag=7358095616&lptag=P7358095616&itemId=18950901863&vendorItemId=86077157444&spec=10305199",
          "price": "99000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4023035/40230350013.1.jpg"
        },
        {
          "title": "파스텔<b>우드</b> 그린빈 1인소파 원목 카페<b>의자</b>  <b>베이지</b>",
          "productUrl": "https://link.coupang.com/re/PCSNAVERPCSDP?pageKey=7563963326&ctag=7563963326&lptag=I19933762322&itemId=19933762322&vendorItemId=87033243194&spec=10305199",
          "price": "133000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4295815/42958159147.jpg"
        },
        {
          "title": "데온 고무나무 원목 패브릭 <b>의자</b> 체어 <b>우드</b> 예쁜 까페 카페 현관 가구(크림<b>베이지</b>)",
          "productUrl": "https://smartstore.naver.com/main/products/10404299183",
          "price": "152000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8794880/87948804076.jpg"
        },
        {
          "title": "카페<b>의자</b> 2P 가죽 철제 <b>우드</b>래핑 더블린체어  <b>베이지</b> 1+1",
          "productUrl": "https://link.coupang.com/re/PCSNAVERPCSDP?pageKey=7565813680&ctag=7565813680&lptag=I19942528326&itemId=19942528326&vendorItemId=87041753002&spec=10305199",
          "price": "151100",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4308276/43082768016.jpg"
        },
        {
          "title": "퀴니 <b>우드</b> 체어 - 내추럴 + <b>베이지</b> PU",
          "productUrl": "https://casadi.co.kr/product/detail.html?product_no=2168&cate_no=57&display_group=1&cafe_mkt=naver_ks&mkt_in=Y&ghost_mall_id=naver&ref=naver_open",
          "price": "60040",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4561244/45612449860.jpg"
        },
        {
          "title": "퀴니 <b>우드</b> 체어 - 월넛 + <b>베이지</b> PU",
          "productUrl": "https://casadi.co.kr/product/detail.html?product_no=2170&cate_no=57&display_group=1&cafe_mkt=naver_ks&mkt_in=Y&ghost_mall_id=naver&ref=naver_open",
          "price": "60040",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4561253/45612537134.jpg"
        }
      ]
    },
    {
      "label": "조명",
      "coordinate": [
        278,
        47.8173834496
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-07-29T19-54-09-227020Lighting",
      "items": [
        {
          "title": "프랜디 <b>원형</b><b>조명</b> 둥근 아크릴볼 유리볼 <b>조명</b> 식탁등 동그란 펜던트 레일등",
          "productUrl": "https://smartstore.naver.com/main/products/4560831405",
          "price": "23000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8210535/82105351405.3.jpg"
        },
        {
          "title": "밀키1등 유리볼 식탁<b>조명</b> <b>원형</b> 펜던트 레일<b>조명</b> 간접 포인트등",
          "productUrl": "https://smartstore.naver.com/main/products/8861637440",
          "price": "26000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8640613/86406137763.jpg"
        },
        {
          "title": "LED 촛불 초 <b>원형</b> 티라이트 이벤트 양초 미니 전기초 전자초 캔들",
          "productUrl": "https://smartstore.naver.com/main/products/5308300090",
          "price": "200",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8285279/82852792537.1.jpg"
        },
        {
          "title": "휴슬립 햇빛 <b>원형</b>발광 <b>조명</b> 라이트테라피 생체시계 관리 광테라피 세로토닌 취침등 수면증",
          "productUrl": "https://smartstore.naver.com/main/products/10236464925",
          "price": "69000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8778096/87780968494.jpg"
        },
        {
          "title": "LED모듈 삼성 기판 리폼 거실등 주방 <b>원형</b> 욕실 <b>조명</b> 자석 교체 안정기 세트",
          "productUrl": "https://smartstore.naver.com/main/products/2138652510",
          "price": "10900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_1211621/12116210380.115.jpg"
        },
        {
          "title": "전등갓 아크릴 <b>원형</b> 커버 <b>조명</b> 케이스 방등커버 안방 침실등 작은 방등 플라스틱 실내",
          "productUrl": "https://smartstore.naver.com/main/products/5387523055",
          "price": "23000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8293201/82932016338.jpg"
        },
        {
          "title": "비상 소형 <b>원형</b> <b>조명</b> 무선 충전식 캠핑 램프 전구 무드등 파티라이트",
          "productUrl": "https://smartstore.naver.com/main/products/8606581942",
          "price": "14900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8615108/86151082265.jpg"
        },
        {
          "title": "페블 1등 <b>원형</b><b>조명</b> 포인트 유리 펜던트 카페 <b>조명</b>",
          "productUrl": "https://smartstore.naver.com/main/products/6728470362",
          "price": "48000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8427297/84272970684.jpg"
        },
        {
          "title": "이케아 파도 <b>원형</b><b>조명</b> 유리볼 인스타 감성<b>조명</b> 달 <b>조명</b> 인테리어 테이블 탁상스탠드 침실용 무드등",
          "productUrl": "https://smartstore.naver.com/main/products/4985916931",
          "price": "26900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8253043/82530437525.jpg"
        },
        {
          "title": "휴슬립 <b>원형</b>발광<b>조명</b> 햇빛 <b>조명</b> 라이트테라피 생체시계 관리 광테라피 세로토닌 생체리듬",
          "productUrl": "https://husleep.com/product/detail.html?product_no=12&cate_no=43&display_group=1&cafe_mkt=naver_ks&mkt_in=Y&ghost_mall_id=naver&ref=naver_open",
          "price": "69000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4851141/48511410439.jpg"
        }
      ]
    },
    {
      "label": "조명",
      "coordinate": [
        278,
        47.8173834496
      ],
      "image_url": "https://storage.googleapis.com/bbangggujipggu/detected_object/2024-07-29T19-54-10-605495Light%20fixture",
      "items": [
        {
          "title": "나무 <b>우드 조명</b> 후렌치 원목 1등 2등 3등 일자 <b>원형</b>",
          "productUrl": "https://smartstore.naver.com/main/products/5254607029",
          "price": "7000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8279912/82799129507.3.jpg"
        },
        {
          "title": "뉴트럴감성 <b>베이지우드</b> 펜던트<b>조명</b> 서재 포인트 호텔",
          "productUrl": "https://smartstore.naver.com/main/products/10502680384",
          "price": "112000",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8804718/88047185736.jpg"
        },
        {
          "title": "JIYU 아크릴 <b>조명</b> 나무 받침대 <b>원형</b> LED <b>우드</b> 무드등 부자재 교보재 교재 재료",
          "productUrl": "https://smartstore.naver.com/main/products/8237422366",
          "price": "2900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8578192/85781922689.jpg"
        },
        {
          "title": "라탄 1등 식탁등 <b>원형</b> 펜던트 LED <b>우드</b> 갓등 인테리어 홈 카페<b>조명</b>",
          "productUrl": "https://smartstore.naver.com/main/products/5397676621",
          "price": "26500",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8294217/82942170147.4.jpg"
        },
        {
          "title": "공간LED 브리앙 <b>원형</b> <b>우드</b> 레일<b>조명</b> BL2colors",
          "productUrl": "https://link.auction.co.kr/gate/pcs?item-no=E603669246&sub-id=1&service-code=10000003",
          "price": "41670",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4929995/49299959112.jpg"
        },
        {
          "title": "공간LED 브리앙 <b>원형</b> <b>우드</b> 레일<b>조명</b> BL2colors",
          "productUrl": "https://smartstore.naver.com/main/products/9967164959",
          "price": "42400",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8751166/87511667232.1.jpg"
        },
        {
          "title": "무드등 아크릴 LED 교재 <b>원형</b> 나무 <b>우드 조명</b> 교보재 재료 받침대 부자재",
          "productUrl": "http://shop.interpark.com/gate/ippgw.jsp?goods_no=15642541307&biz_cd=P01397",
          "price": "4720",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4867997/48679972976.jpg"
        },
        {
          "title": "카페 라인<b>조명</b> <b>우드</b> <b>원형</b> 스포트 레일등 스팟 <b>조명</b>",
          "productUrl": "https://link.gmarket.co.kr/gate/pcs?item-no=3509530578&sub-id=1003&service-code=10000003",
          "price": "42660",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_4941121/49411216212.jpg"
        },
        {
          "title": "붙이는 <b>우드조명</b> 실내 부착식 벽등 벽<b>조명</b> 거실 <b>원형</b>",
          "productUrl": "https://smartstore.naver.com/main/products/9106898943",
          "price": "33900",
          "imageUrl": "https://shopping-phinf.pstatic.net/main_8665139/86651399265.jpg"
        }
      ]
    }
  ]
}

# @router.get("/test")
# async def test():
#     return await detect_obj_and_search()