from fastapi import FastAPI
from src.routers.index_router import index_router

app = FastAPI(docs_url="/api-docs", openapi_url="/open-api")

app.include_router(index_router, prefix="/api")