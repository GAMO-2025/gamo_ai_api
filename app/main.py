from fastapi import FastAPI
import google.generativeai as genai

# 내부 모듈
from app.core.config import settings
from app.database import Base, engine
from app.routers import keyword_api, letter_api, ajenda_api

# Gemini API 키 설정
genai.configure(api_key=settings.GEMINI_API_KEY)

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 인스턴스
app = FastAPI(title="GAMO AI Keyword API")

# 라우터 등록
app.include_router(keyword_api.router, prefix="/api", tags=["Keywords"])
app.include_router(letter_api.router, prefix="/api", tags=["Letters"])
app.include_router(ajenda_api.router, prefix="/api", tags=["Agendas"])

@app.get("/")
def root():
    return {"message": "GAMO AI API is running"}
