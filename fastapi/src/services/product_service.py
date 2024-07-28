from fastapi import HTTPException
import xmltodict
import requests
import os
from dotenv import load_dotenv

load_dotenv()

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

async def get_product_from_naver_shopping(keyword: str, page_num: int, page_size: int, category: str = None):

    url = f"{naver_shopping_url}?query={keyword}&start={page_num}&display={page_size}&exclude=rental:cbshop"

    res = requests.get(url, headers={
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_secret
    })

    if res.status_code == 200:
        product_search_respnose = res.json()
        products = product_search_respnose["items"]
        
        if category == None:
            return products

        filtered_products = get_filtered_products(products, category)

        return filtered_products
    
    raise HTTPException(status_code=400, detail="Something wrong")

# category4 : 사무용의자, 
# category3 : 침대, 책상, 의자, 식탁/의자, 소파, 서랍장, 조명
# category2 : 원예/식물, 커튼/블라인드, 베개

def get_filtered_products(products: list, category: str):
    if category == "침대":
        return list(filter(lambda x: x["category3"] == "침대", products))
    
    if category == "책상":
        return list(filter(lambda x: x["category3"] == "책상", products))

    if category == "의자":
        return list(filter(lambda x: x["category3"] == "의자" or x["category4"] == "사무용의자" or x["category3"] == "식탁/의자", products))
    
    if category == "소파":
        return list(filter(lambda x: x["category3"] == "소파", products))
    
    if category == "커튼":
        return list(filter(lambda x: x["category2"] == "커튼/블라인드", products))
    
    if category == "서랍장":
        return list(filter(lambda x: x["category3"] == "서랍장", products))

    if category == "식물":
        return list(filter(lambda x: x["category2"] == "원예/식물", products))

    if category == "조명":
        return list(filter(lambda x: x["category3"] == "조명", products))
    
    if category == "베개":
        return list(filter(lambda x: x["category2"] == "베개", products))

    return products
