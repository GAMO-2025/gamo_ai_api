import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import google.generativeai as genai

# --- 내부 모듈 임포트 ---
from app.database import get_db
from app.database.models import Keyword
from app.utils.id_utils import generate_keyword_id
from pydantic import BaseModel, Field

# --- 라우터 및 요청 모델 정의 ---
router = APIRouter()

class ProcessCallRequest(BaseModel):
    call_id: int = Field(..., description="고유한 통화 ID")
    text: str = Field(..., description="STT 변환된 통화 내용 전체")

# --- API 엔드포인트 ---
@router.post("/process-call", summary="통화 내용에서 키워드 추출 및 저장")
async def process_call_and_store_keywords(
    request: ProcessCallRequest,
    db: Session = Depends(get_db)
):
    model = genai.GenerativeModel('models/gemini-pro-latest')
    prompt = f"""
    아래 [대화 내용]을 분석하여 핵심 키워드를 5개 추출하고, 결과를 반드시 JSON 배열(array)로만 반환해줘.
    [대화 내용]
    {request.text}
    """
    try:
        response = await model.generate_content_async(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        keywords = json.loads(cleaned)

        saved_keywords = []
        for kw in keywords:
            # keywordId 중복 방지
            while True:
                new_id = generate_keyword_id()
                if not db.query(Keyword).filter(Keyword.keywordId == new_id).first():
                    break
            
            # DB에 저장할 객체 생성
            entry = Keyword(
                keywordId=new_id,
                keyword=kw,
                videocallId=request.call_id
            )
            db.add(entry)
            saved_keywords.append(kw)

        db.commit() # 모든 키워드를 한 번에 DB에 최종 저장

        return {
            "message": f"'{request.call_id}'에 대한 키워드가 성공적으로 저장되었습니다.",
            "stored_keywords": saved_keywords
        }
    except ValueError:
        # call_id가 숫자로 변환되지 않을 때의 오류 처리
        raise HTTPException(status_code=422, detail="call_id는 반드시 숫자 형식의 문자열이어야 합니다.")
    except Exception as e:
        db.rollback() # 오류 발생 시 DB 변경사항을 원래대로 되돌림
        raise HTTPException(status_code=500, detail=f"키워드 추출 또는 저장 중 오류 발생: {str(e)}")