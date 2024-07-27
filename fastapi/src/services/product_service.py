from fastapi import HTTPException
import xmltodict
import requests
import os

eleven_api_key = os.getenv("ELEVEN_API_KEY")
eleven_url = os.getenv("ELEVEN_URL")

naver_client_id = os.getenv("NAVER_CLIENT_ID")
naver_secret = os.getenv("NAVER_SECRET")
naver_shopping_url = os.getenv("NAVER_SHOPPING_URL")

async def get_product_from_eleven(keyword: str, page_num: int, page_size: int):
    
    url = f"{eleven_url}?key={eleven_api_key}&apiCode=ProductSearch&keyword={keyword}&pageNum={page_num}&pageSize={page_size}"

    res = requests.get(url)

    if res.status_code == 200:
        product_search_response = xmltodict.parse(res.text)
        products = product_search_response["ProductSearchResponse"]["Products"]["Product"]
        return products
    
    raise HTTPException(status_code=400, detail="Something wrong")

async def get_product_from_naver_shopping(keyword: str, page_num: int, page_size: int):

    url = f"{naver_shopping_url}?query={keyword}&start={page_num}&display={page_size}&exclude=rental:cbshop"

    res = requests.get(url, headers={
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_secret
    })

    if res.status_code == 200:
        product_search_respnose = res.json()
        products = product_search_respnose["items"]
        # a = list(filter(lambda x: x["category3"] == "침대", products))
        # print(a)
        return products
    
    raise HTTPException(status_code=400, detail="Something wrong")

# category4 : 사무용의자, 
# category3 : 침대, 에어컨, 책상, 의자, 식탁/의자, 소파
# category2 : 원예/식물, 커튼/블라인드, 