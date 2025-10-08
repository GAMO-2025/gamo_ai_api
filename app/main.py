from fastapi import FastAPI
import google.generativeai as genai

# 내부 모듈
from app.core.config import settings
from app.database import Base, engine
from app.routers import keyword_api

# Gemini API 키 설정
genai.configure(api_key=settings.GEMINI_API_KEY)

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 인스턴스
app = FastAPI(title="GAMO AI Keyword API")

# 라우터 등록
app.include_router(keyword_api.router, prefix="/api", tags=["Keywords"])

@app.get("/")
def root():
    return {"message": "GAMO AI API is running"}
