from fastapi import APIRouter, File, UploadFile
from src.routers.interior_router import interior_router

index_router = router = APIRouter()    

index_router.include_router(interior_router, prefix="/interior")