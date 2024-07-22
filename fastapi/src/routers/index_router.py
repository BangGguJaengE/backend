from fastapi import APIRouter
from src.services.test import run_quickstart

index_router = router = APIRouter()    

@router.get("/test")
async def test():
    label = run_quickstart()

    return label
