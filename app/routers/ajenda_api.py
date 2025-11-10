# --- 라이브러리 임포트 ---
import math
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import google.generativeai as genai

# --- 내부 모듈 임포트 ---
from app.database import get_db
from app.database.models import Keyword
from pydantic import BaseModel, Field

# --- 라우터 및 데이터 모델 정의 ---
router = APIRouter()

class RecommendRequest(BaseModel):
    videocall_ids: List[int] = Field(..., description="주제 추천의 기반이 될 과거 통화 ID 목록", example=[15352, 92737])

class RecommendResponse(BaseModel):
    status: int
    recommended_topic: str

# --- API 엔드포인트 구현 ---
@router.post("/ajenda",
             summary="키워드 우선순위 기반 통화 주제 추천",
             response_model=RecommendResponse,
             status_code=status.HTTP_200_OK)
async def recommend_topic(
    request: RecommendRequest,
    db: Session = Depends(get_db)
):
    """
    과거 통화 ID 목록을 받아, 저장된 키워드에 우선순위를 적용하여
    가장 관련성 높은 통화 주제 1개를 생성하여 반환합니다.
    """
    if not request.videocall_ids:
        raise HTTPException(status_code=400, detail="videocall_ids 목록이 비어있습니다.")

    all_keywords = db.query(Keyword).filter(
        Keyword.videocallId.in_(request.videocall_ids)
    ).all()

    if not all_keywords:
        raise HTTPException(status_code=404, detail="제공된 ID에 해당하는 키워드를 찾을 수 없습니다.")

    # --- 2. 우선순위 로직 적용 ---
    sorted_by_weight = sorted(all_keywords, key=lambda kw: kw.weight, reverse=True)
    n = len(sorted_by_weight)
    top_half_count = math.ceil(n / 2)
    top_half_keywords = sorted_by_weight[:top_half_count]
    sorted_by_date = sorted(top_half_keywords, key=lambda kw: kw.date, reverse=True)
    final_keywords = sorted_by_date[:3]
    topic_sentences = [kw.keyword for kw in final_keywords]

    # --- 3. Gemini를 이용한 최종 주제 문장 생성 ---
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = f"""
    당신은 따뜻한 대화를 이끌어내는 전문 상담가입니다.
    아래 [규칙]과 [완전한 작업 예시]를 참고하여, [핵심 주제 목록]을 자연스럽게 연결한 **단 한 개의 친근한 질문 문장**을 만들어 주세요.

    [규칙]
    1.  **출력은 반드시 최종 추천 문장 텍스트 한 줄이어야 합니다.**
    2.  **"그럼요..."와 같은 서론, 잡담, 설명, 마크다운(`**`, `##` 등)을 절대 포함하지 마세요.**
    3.  [핵심 주제 목록]의 주제들을 자연스럽게 엮어, 따뜻하고 친근한 **단 하나의 질문 문장**으로 만드세요.
    4.  [완전한 작업 예시]의 [추천 문장] 형식을 완벽하게 따르세요.

    ---
    [완전한 작업 예시 1 - 단일 주제]

    [핵심 주제 목록]
    - "기숙사 밥이 짜서 맛없다고 이야기함"

    [추천 문장]
    지난번에 기숙사 밥이 너무 짜다고 했는데, 요즘은 좀 입맛에 맞게 잘 나와요?
    ---
    [완전한 작업 예시 2 - 여러 주제]

    [핵심 주제 목록]
    - "할머니가 된장국을 끓여준다고 약속함"
    - "친구들과 찍은 사진에 대해 이야기함"
    - "과제를 끝내고 피곤해함"

    [추천 문장]
    그때 과제 끝내고 많이 피곤해 보였는데 컨디션은 좀 괜찮아졌어요? 친구분들이랑 찍은 사진도 잘 봤어요! 참, 할머니가 끓여주신다는 된장국은 맛있게 드셨어요?
    ---
    [실제 작업]

    [핵심 주제 목록]
    - {"\n- ".join(topic_sentences)}

    [추천 문장]
    """
    try:
        response = await model.generate_content_async(prompt)
        cleaned_text = response.text.strip().replace("**", "")
        
        return {
            "status": 200,
            "recommended_topic": cleaned_text
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_Error,
            content={
                "status": 500,
                "detail": f"주제 생성 중 오류 발생: {str(e)}"
            }
        )