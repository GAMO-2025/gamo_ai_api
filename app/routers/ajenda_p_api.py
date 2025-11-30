# --- 라이브러리 임포트 ---
import math
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
# import google.generativeai as genai # ✨ Gemini 라이브러리 제거

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
    # ✨ Gemini가 만든 문장(str) 대신, 키워드 리스트(List[str])를 반환하도록 변경
    recommended_keywords: List[str]

# --- API 엔드포인트 구현 ---
@router.post("/ajenda",
             summary="키워드 우선순위 기반 추천 키워드 리스트 반환",
             response_model=RecommendResponse,
             status_code=status.HTTP_200_OK)
async def recommend_topic(
    request: RecommendRequest,
    db: Session = Depends(get_db)
):
    """
    과거 통화 ID 목록을 받아, 우선순위 로직(가중치 -> 최신순)에 따라
    상위 3개의 핵심 키워드를 리스트 형태로 반환합니다.
    (Gemini 생성 없이 순수 키워드만 반환)
    """
    # 1. 요청 검증
    if not request.videocall_ids:
        raise HTTPException(status_code=400, detail="videocall_ids 목록이 비어있습니다.")

    # 2. DB에서 키워드 조회
    all_keywords = db.query(Keyword).filter(
        Keyword.videocallId.in_(request.videocall_ids)
    ).all()

    if not all_keywords:
        raise HTTPException(status_code=404, detail="제공된 ID에 해당하는 키워드를 찾을 수 없습니다.")

    # 3. 우선순위 로직 적용
    # 3-1. 가중치(weight) 내림차순 정렬
    sorted_by_weight = sorted(all_keywords, key=lambda kw: kw.weight, reverse=True)
    
    # 3-2. 상위 절반 필터링 (소수점 올림)
    n = len(sorted_by_weight)
    top_half_count = math.ceil(n / 2)
    top_half_keywords = sorted_by_weight[:top_half_count]

    # 3-3. 생성일시(date) 최신순 정렬
    sorted_by_date = sorted(top_half_keywords, key=lambda kw: kw.date, reverse=True)
    
    # 3-4. 최종적으로 최신 키워드 3개 선택
    final_keywords = sorted_by_date[:3]
    
    # 4. 키워드 문자열만 추출하여 리스트 생성
    keyword_list = [kw.keyword for kw in final_keywords]

    # 5. 결과 반환 (Gemini 호출 없음)
    return {
        "status": 200,
        "recommended_keywords": keyword_list
    }