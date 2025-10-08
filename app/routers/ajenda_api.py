# --- 라이브러리 임포트 ---
import os                                    # 운영체제와 상호작용하기 위한 라이브러리
import json                                  # JSON 형식 데이터를 다루기 위한 라이브러리
from typing import List, Dict                  # 타입 힌팅을 위한 라이브러리
from dotenv import load_dotenv               # .env 파일에서 환경 변수를 불러오기 위한 라이브러리
import google.generativeai as genai          # Gemini API를 사용하기 위한 구글 라이브러리
from fastapi import FastAPI, HTTPException   # API 서버를 만들기 위한 FastAPI 라이브러리
from pydantic import BaseModel, Field        # 데이터 유효성 검사를 위한 Pydantic 라이브러리

# --- 초기 설정 ---
load_dotenv()                                # .env 파일의 내용을 환경 변수로 로드합니다.
app = FastAPI()                              # FastAPI 애플리케이션 인스턴스를 생성합니다.
DB_FILE = "keyword_db.json"                  # 키워드를 조회할 JSON 파일의 이름을 정의합니다.

# Gemini API 키 설정
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"API 키 설정에 실패했습니다: {e}")

# --- 데이터 모델 정의 ---
# API가 요청(Request)으로 받을 데이터의 형식을 정의합니다.
class RecommendTopicRequest(BaseModel):
    call_ids: List[str] = Field(..., description="주제 추천의 기반이 될 과거 통화 ID 목록")

# API가 응답(Response)으로 보낼 데이터의 형식을 정의합니다.
class TopicResponse(BaseModel):
    recommended_topic: str

# --- 데이터베이스 헬퍼 함수 ---
# JSON 파일을 읽어 데이터를 반환하는 함수입니다.
def read_db() -> Dict[str, List[str]]:
    if not os.path.exists(DB_FILE):          # 만약 DB 파일이 존재하지 않으면,
        return {}                            # 비어있는 딕셔너리를 반환합니다.
    with open(DB_FILE, "r", encoding="utf-8") as f: # DB 파일을 읽기 모드로 엽니다.
        return json.load(f)                  # 파일의 JSON 내용을 파이썬 딕셔너리로 변환하여 반환합니다.

# --- API 엔드포인트 구현 ---
# POST 방식으로 /recommend-topic 주소로 요청이 들어왔을 때 아래 함수를 실행합니다.
@app.post("/recommend-topic", summary="키워드 기반 통화 주제 추천", response_model=TopicResponse)
async def recommend_topic_based_on_keywords(request: RecommendTopicRequest):
    # DB 파일을 읽어 현재 저장된 모든 키워드 데이터를 가져옵니다.
    db_data = read_db()
    # 추천의 기반이 될 모든 키워드를 담을 빈 리스트를 생성합니다.
    all_keywords = []

    # 클라이언트가 요청한 모든 통화 ID에 대해 반복합니다.
    for call_id in request.call_ids:
        # 만약 현재 통화 ID가 DB 데이터에 존재하면,
        if call_id in db_data:
            # 해당 ID의 키워드 리스트를 전체 키워드 리스트에 추가합니다.
            all_keywords.extend(db_data[call_id])

    # 만약 관련된 키워드가 하나도 없으면,
    if not all_keywords:
        # 404 상태 코드와 함께 오류 메시지를 반환합니다.
        raise HTTPException(status_code=404, detail="관련된 키워드를 찾을 수 없습니다.")

    # 전체 키워드 리스트에서 중복된 항목을 제거하여 더 명확한 프롬프트를 만듭니다.
    unique_keywords = list(set(all_keywords))

    # Gemini 모델을 선택합니다.
    model = genai.GenerativeModel('models/gemini-pro-latest')
    # 키워드를 기반으로 추천 주제 문장을 생성하도록 요청하는 프롬프트를 작성합니다.
    prompt = f"""
    아래 [핵심 키워드 목록]은 한 사람과 나누었던 과거 대화들의 주제입니다.
    이 키워드들을 자연스럽게 엮어서, 대화를 시작할 수 있는 친근한 추천 문장 하나만 만들어줘.
    [핵심 키워드 목록]
    {', '.join(unique_keywords)}
    """
    try:
        # Gemini API를 호출하여 응답을 받습니다.
        response = await model.generate_content_async(prompt)
        # 생성된 추천 주제를 클라이언트에게 반환합니다.
        return {"recommended_topic": response.text.strip()}
    except Exception as e:
        # 오류 발생 시 500 상태 코드와 함께 오류 메시지를 반환합니다.
        raise HTTPException(status_code=500, detail=f"주제 생성 중 오류 발생: {str(e)}")
