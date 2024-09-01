from fastapi import FastAPI
from src.routers.index_router import index_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(docs_url="/api-docs", openapi_url="/open-api")

# 모든 도메인에 대해 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.include_router(index_router, prefix="/api")

