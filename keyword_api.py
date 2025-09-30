import os
import json
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- 1. 초기 설정 ---

# .env 파일에서 환경 변수(API 키)를 불러옵니다.
load_dotenv()

# FastAPI 앱을 생성합니다.
app = FastAPI()

# Gemini API 키를 설정합니다.
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"API 키 설정에 실패했습니다: {e}")

# --- 2. 데이터 모델 정의 ---

class ConversationRequest(BaseModel):
    text: str

class KeywordResponse(BaseModel):
    keywords: List[str]

# --- 3. API 엔드포인트 생성 ---

@app.get("/")
def read_root():
    return {"message": "키워드 추출(Keyword) API 서버가 실행 중입니다. /docs 로 이동하여 테스트하세요."}


@app.post("/extract-keywords/", response_model=KeywordResponse)
async def extract_keywords_from_text(request: ConversationRequest):
    # 사용 가능한 정확한 모델 이름으로 설정합니다.
    model = genai.GenerativeModel('models/gemini-pro-latest')

    prompt = f"""
    당신은 텍스트를 분석하여 핵심 용어를 추출하는 AI입니다.
    아래 [대화 내용]을 분석하여 가장 중요한 키워드를 5개 추출해 주세요.
    결과는 반드시 JSON 형식의 배열(array)로만 반환해 주세요.

    예시: ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]

    [대화 내용]
    {request.text}
    """

    try:
        response = await model.generate_content_async(prompt)
        
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        keywords_list = json.loads(cleaned_response)

        return {"keywords": keywords_list}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Gemini가 반환한 키워드 형식이 올바르지 않습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API 호출 중 오류: {str(e)}")
