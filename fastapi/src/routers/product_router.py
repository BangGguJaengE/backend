from fastapi import APIRouter
from src.services.product_service import *

product_router = router = APIRouter()

@router.get("/eleven")
async def get_furniture_from_eleven(keyword: str, page_num: int, page_size: int):
    res = await get_product_from_eleven(keyword, page_num, page_size)

    return res

@router.get("/naver")
async def get_furniture_from_naver(keyword: str, page_num: int, page_size: int):
    res = await get_product_from_naver_shopping(keyword, page_num, page_size)

    return res