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
    videocallId: str


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
    당신은 대화의 핵심 요점을 정리하는 AI 분석가입니다.
    아래 [규칙]과 [완전한 작업 예시]를 참고하여, [대화 내용]에서 핵심 주제들을 **요약된 문장 형태**로 추출해 주세요.

    [규칙]
    1.  **단일 키워드가 아닌, 문맥을 포함한 핵심 주제를 요약된 문장으로 추출해야 합니다.**
    2.  대화의 길이에 따라 주제의 개수를 2개에서 5개 사이로 조절하세요.
    3.  각 주제의 중요도를 1(낮음)부터 5(매우 높음) 사이의 숫자로 평가하세요.
    4.  결과는 반드시 [출력 형식]과 동일한 JSON 형식으로만 반환해야 합니다. 다른 설명은 절대 추가하지 마세요.

    ---
    [완전한 작업 예시 1 - 짧은 대화]

    [대화 내용]
    "아, 맞다. 나 설탕 떨어져서 호떡 못 해먹었네. 내가 사갈까? 됐다. 니가 뭘 또 사오노. 그냥 오면 되지."

    [출력 형식]
    [
      {{"keyword": "호떡 재료(설탕) 구매 관련 대화", "weight": 5}},
      {{"keyword": "방문 시 빈손으로 와도 된다고 함", "weight": 3}}
    ]
    ---
    [완전한 작업 예시 2 - 긴 대화]

    [대화 내용]
    "여보세요 어, 할머니 나야 그래, 우리 손녀구나. 뭐 하노 지금 그냥 과제 끝내고 누워 있었어. 너무 피곤해 밤새웠지 또? 아니, 그냥 좀 늦게 잤어. ... (중략) ... 나 요즘 밥 잘 먹어요. 근데 기숙사 밥이 너무 짜요 짜면 물 많이 마셔야지. ... (중략) ... 나중에 내려오면 내가 된장국 끓여줄게 진짜요? 근데 할머니 된장 다 떨어졌다 하지 않았어요 아, 옆집에서 좀 나눠줬다. ... (중략) ... 사진 봤어요. 친구분들이랑 찍은 거 그거? 네 이모가 보내줬다고 하더라. ... (중략) ... 모자도 잘 어울렸어요"

    [출력 형식]
    [
      {{"keyword": "할머니가 된장국을 끓여준다고 약속함", "weight": 5}},
      {{"keyword": "친구들과 찍은 사진에 대해 이야기함", "weight": 4}},
      {{"keyword": "기숙사 밥이 짜서 맛없다고 이야기함", "weight": 3}},
      {{"keyword": "과제를 끝내고 피곤해함", "weight": 2}}
    ]
    ---
    [실제 작업]

    [대화 내용]
    {request.text}

    [출력 형식]
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

