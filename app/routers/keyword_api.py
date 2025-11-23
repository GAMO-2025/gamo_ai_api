import json
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
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
    
class KeywordProcessResponse(BaseModel):
    status: int
    videocallId: int


# --- API 엔드포인트 ---
@router.post("/keyword",
             summary="통화 내용에서 키워드 추출 및 저장",
             response_model=KeywordProcessResponse,
             status_code=status.HTTP_200_OK) # 성공 시 기본 상태 코드를 200으로 명시)
async def process_call_and_store_keywords(
    request: ProcessCallRequest,
    db: Session = Depends(get_db)
):
    model = genai.GenerativeModel('models/gemini-flash-latest')
    prompt = f"""
    당신은 대화의 문맥을 완벽하게 이해하고 핵심 요점을 정리하는 AI 분석가입니다.
    아래 [대화 내용]은 **STT(음성 인식)를 통해 텍스트로 변환된 결과물**입니다.
    따라서 발음이 비슷하지만 문맥상 어색한 오타(예: '저렴하다' -> '절연하다', '방학' -> '반학')가 포함되어 있을 수 있습니다.

    [규칙]
    1.  **[중요] STT 오류 보정:** 텍스트를 있는 그대로 해석하지 말고, **전체 대화 흐름과 문맥을 파악하여 오타를 원래 의도된 단어로 내부적으로 교정한 뒤** 주제를 추출하세요.
        - (예시: "갤럭시가 절연하잖아" -> "갤럭시가 저렴하잖아"로 해석하여 "갤럭시의 저렴한 가격"이라는 주제 추출)
    
    2.  **문맥 포함 요약:** 단일 키워드가 아닌, 문맥을 포함한 핵심 주제를 요약된 문장 형태로 추출하세요.
        - (좋은 예시): "할머니가 된장국을 끓여준다고 약속함"
        - (나쁜 예시): "된장국"

    3.  대화의 길이에 따라 주제의 개수를 2개에서 5개 사이로 조절하세요.
    4.  각 주제의 중요도를 대화의 핵심과 얼마나 관련이 깊은지에 따라 1(낮음)부터 5(매우 높음) 사이의 숫자로 평가하세요.
    5.  결과는 반드시 아래 [출력 형식]과 동일한 JSON 형식으로만 반환해야 합니다.

    [출력 형식]
    [
      {{"keyword": "보정된 내용을 바탕으로 추출된 주제 문장 1", "weight": 중요도_숫자}},
      {{"keyword": "보정된 내용을 바탕으로 추출된 주제 문장 2", "weight": 중요도_숫자}}
    ]

    [대화 내용]
    {request.text}
    """
    try:
        response = await model.generate_content_async(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        # keywords_data =[{'keyword': '시장 축제', 'weight': 5}, ...] 형태의 리스트
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

        db.commit() # 모든 키워드를 한 번에 DB에 최종 저장
        # 성공 시, status가 포함된 JSON 본문 반환
        return {
            "status": 200,
            "videocallId": request.call_id
        }
    except (json.JSONDecodeError, KeyError) as e:
        db.rollback()
        # 실패 시, status가 포함된 JSONResponse 반환
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "detail": f"Gemini 응답 처리 중 오류 발생 (잘못된 형식): {str(e)}"
            }
        )
    except Exception as e:
        db.rollback()
        # 실패 시, status가 포함된 JSONResponse 반환
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "detail": f"키워드 추출 또는 저장 중 오류 발생: {str(e)}"
            }
        )

