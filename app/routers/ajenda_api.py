# --- 라이브러리 임포트 ---
import math
import json
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
    # 가중치(weight) 내림차순 정렬
    sorted_by_weight = sorted(all_keywords, key=lambda kw: kw.weight, reverse=True)
    
    # 상위 절반 필터링 (소수점 올림)
    n = len(sorted_by_weight)
    top_half_count = math.ceil(n / 2)
    top_half_keywords = sorted_by_weight[:top_half_count]

    # 생성일시(date) 최신순 정렬 후 상위 3개 선택
    sorted_by_date = sorted(top_half_keywords, key=lambda kw: kw.date, reverse=True)
    final_keywords = sorted_by_date[:3]
    
    # 최종 키워드 문장 리스트
    topic_sentences = [kw.keyword for kw in final_keywords]

    # 4. Gemini 호출 설정
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = f"""
    [임무]
    당신은 입력된 [핵심 주제 목록]에 있는 각각의 사실들을 문맥 왜곡 없이 연결하여, **대화 주제를 제안하는 하나의 문장**을 만드는 '문장 결합기'입니다.

    [규칙]
    1.  각 주제는 서로 독립적인 사건일 수 있습니다. 억지로 인과관계를 만들지 말고, 접속사(~고, ~며, ~했는데 등)를 사용하여 자연스럽게 나열하세요.
    2.  문장의 끝은 질문이 아니라 **"~에 대해 이야기해 보세요."** 또는 **"~어땠는지 물어보세요."**와 같은 권유형 평서문으로 끝나야 합니다.
    3.  감정적인 표현이나 안부 인사를 덧붙이지 말고, **주제 내용만 명확하게 전달**하세요.
    4.  결과는 반드시 유효한 JSON 포맷이어야 합니다.
    5.  JSON 데이터 외에 "네, 알겠습니다"와 같은 서론이나 설명은 절대 포함하지 마세요.

    ---
    [작업 예시]

    [핵심 주제 목록]
    - "친구들과 축구를 하러 간다고 이야기 했음"
    - "동생이랑 싸웠는데 화해하기가 힘들다고 했음"

    [출력 형식]
    {{
      "recommended_topic": "친구들과의 축구는 어땠는지, 동생이랑은 화해하였는지 이야기해 보세요."
    }}
    
    ---
    [실제 작업]

    [핵심 주제 목록]
    - {"\n- ".join(topic_sentences)}

    [출력 형식]
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        # --- 응답 처리 로직 (JSON 파싱 및 서론 제거) ---
        content = response.text.strip()
        
        # 마크다운 코드 블록 제거
        if '```' in content:
            parts = content.split('```')
            for part in parts:
                if part.strip().startswith('json'):
                    content = part.strip()[4:]
                    break
                elif part.strip().startswith('{'):
                    content = part.strip()
                    break

        # JSON 추출
        start_index = content.find('{')
        end_index = content.rfind('}')
        
        if start_index != -1 and end_index != -1:
            json_str = content[start_index : end_index + 1]
            data = json.loads(json_str)
            final_topic = data.get('recommended_topic', '')
        else:
            # JSON 구조가 깨졌을 경우, 전체 텍스트를 반환하되 깔끔하게 정리
            final_topic = content.replace('"', '').replace('{', '').replace('}', '').replace('recommended_topic:', '').strip()

        return {
            "status": 200,
            "recommended_topic": final_topic
        }

    except (json.JSONDecodeError, KeyError) as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "detail": f"Gemini 응답 파싱 중 오류: {str(e)} - 원본: {response.text}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "detail": f"주제 생성 중 오류 발생: {str(e)}"
            }
        )