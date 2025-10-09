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
    당신은 대화의 핵심 요점을 정리하는 AI 분석가입니다.
    아래 [대화 내용]을 분석하여, 다음 규칙에 따라 핵심 주제들을 **요약된 문장 형태**로 추출해 주세요.

    [규칙]
    1.  **단일 키워드가 아닌, 문맥을 포함한 핵심 주제를 요약된 문장으로 추출해야 합니다.**
        -   (좋은 예시): "할머니가 된장국을 끓여준다고 약속함"
        -   (좋은 예시): "기숙사 밥이 짜서 맛없다고 이야기함"
        -   (나쁜 예시): "된장국"
        -   (나쁜 예시): "기숙사 밥"
    2.  대화의 길이에 따라 주제의 개수를 2개에서 5개 사이로 조절하세요.
    3.  각 주제의 중요도를 대화의 핵심과 얼마나 관련이 깊은지에 따라 1(낮음)부터 5(매우 높음) 사이의 숫자로 평가하세요.
    4.  결과는 반드시 아래 [출력 형식]과 동일한 JSON 형식으로만 반환해야 합니다. 다른 설명은 절대 추가하지 마세요.

    [출력 형식]
    [
      {{"keyword": "추출된 주제 요약 문장 1", "weight": 중요도_숫자}},
      {{"keyword": "추출된 주제 요약 문장 2", "weight": 중요도_숫자}}
    ]

    [대화 내용]
    {request.text}
    """
    try:
        response = await model.generate_content_async(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        # [{'keyword': '시장 축제', 'weight': 5}, ...] 형태의 리스트
        keywords_data = json.loads(cleaned)

        stored_items = []
        for item in keywords_data:
            # keywordId 중복 방지
            while True:
                new_id = generate_keyword_id()
                if not db.query(Keyword).filter(Keyword.keywordId == new_id).first():
                    break
            
            entry = Keyword(
                keywordId=new_id,
                keyword=item["keyword"],
                weight=item["weight"],
                videocallId=request.call_id
            )
            db.add(entry)
            stored_items.append({"keyword": item["keyword"], "weight": item["weight"]})

        db.commit()

        return {
            "message": f"'{request.call_id}'에 대한 키워드와 가중치가 성공적으로 저장되었습니다.",
            "stored_items": stored_items
        }
    except (json.JSONDecodeError, KeyError) as e:
        # Gemini가 약속된 JSON 형식으로 응답하지 않았을 경우의 오류 처리
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gemini 응답 처리 중 오류 발생 (잘못된 형식): {str(e)}")
    except Exception as e:
        # 그 외 모든 예외에 대한 처리
        db.rollback() # 오류 발생 시 DB 변경사항을 원래대로 되돌림
        raise HTTPException(status_code=500, detail=f"키워드 추출 또는 저장 중 오류 발생: {str(e)}")

