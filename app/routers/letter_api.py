# --- 라이브러리 임포트 ---
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import google.generativeai as genai

# --- 라우터 및 데이터 모델 정의 ---
router = APIRouter()

# API가 클라이언트로부터 받을 요청(Request)의 형식을 정의합니다.
class LetterRequest(BaseModel):
    text: str = Field(..., description="STT로 변환된, 다듬어지지 않은 원본 편지 텍스트")

# API가 클라이언트에게 보낼 응답(Response)의 형식을 정의합니다.
class LetterResponse(BaseModel):
    status: int
    corrected_text: str

# --- API 엔드포인트 구현 ---
# POST 방식으로 /correct-letter 주소로 요청이 들어왔을 때 아래 함수를 실행합니다.
@router.post("/letter",
             summary="음성 변환 텍스트를 자연스러운 편지글로 교정",
             response_model=LetterResponse,
             status_code=status.HTTP_200_OK)
async def correct_letter_text(request: LetterRequest):
    """
    STT로 변환된 원본 텍스트를 받아, Gemini를 이용해 자연스러운 편지글로 교정한 후,
    원본 letter_id와 함께 교정된 텍스트를 반환합니다.
    """
    # Gemini 모델을 선택합니다.
    model = genai.GenerativeModel('models/gemini-pro-latest')

    # Gemini에게 작업을 지시하는 프롬프트를 작성합니다. (가장 중요한 부분)
    prompt = f"""
    당신은 문장을 자연스럽게 다듬는 전문 교정가입니다.
    아래 [규칙]과 [완전한 작업 예시]를 참고하여, [실제 작업]의 [원본 텍스트]를 자연스러운 편지글로 다듬어 주세요.

    [규칙]
    1.  **내용을 절대 창작하거나 변경하지 말고**, 원래의 의미와 어조를 그대로 유지해야 합니다.
    2.  **원본 텍스트의 어조(예: 반말, 존댓말)를 절대 변경하지 말고 그대로 유지하세요.** 어색한 어미는 그 어조에 맞게 자연스럽게 다듬어 주세요.
    3.  "어...", "음...", "그..."와 같은 불필요한 추임새나 필러 단어는 자연스럽게 제거하세요.
    4.  띄어쓰기와 기본적인 맞춤법 오류를 교정하세요.
    5.  **의미의 흐름에 따라 적절하게 단락을 나누어(줄바꿈을 추가하여) 가독성을 높여주세요.**
    6.  만약 원본 텍스트가 이미 자연스럽고 수정할 내용이 거의 없다면, 원본 텍스트를 그대로 반환하세요.
    7.  교정된 최종 편지글 텍스트만 반환하고, 다른 설명은 절대 추가하지 마세요.

    ---
    [완전한 작업 예시]

    [원본 텍스트]
    "음… 우리 민지야 잘 지내지 그 할머니가 요즘에 좀 무릎이 아파서 많이 못 걸었어 그래도 어제는 동네 한 바퀴 돌았다 아… 날씨가 많이 추워져서 너는 감기 안 걸렸는지 모르겠네 밥은 잘 챙겨 먹고 있지 어… 그때 사진 보니까 머리도 자르고 예쁘더라 공부는 힘들지 그래도 너무 무리하지 말고 할머니는 니 생각 자주 해 그 뭐냐 다음 달에 아마 명절 되면 내려오지 그때 같이 시장도 가고 싶다 음… 할머니가 요즘은 혼자 있는 시간이 많아서 니 목소리 들으면 기분이 참 좋아 그… 아 참 네가 보내준 편지 잘 읽었다 거기 글씨체가 꼭 초등학교 때 썼던 거랑 비슷하더라 옛날 생각나더라 아무튼 건강 잘 챙기고 너무 늦게 자지 말고 사랑한다 우리 손녀"

    [교정된 텍스트]
    "민지야, 잘 지내지?

    할머니가 요즘 무릎이 좀 아파서 많이 걷진 못했단다. 그래도 어제는 동네 한 바퀴를 돌았어.

    날씨가 많이 추워졌는데, 너는 감기 안 걸렸는지 모르겠구나. 밥은 잘 챙겨 먹고 있지?

    사진 보니까 머리도 자르고 예쁘더라. 공부하느라 힘들겠지만 너무 무리하지는 말고.

    할머니는 네 생각 자주 한다. 다음 달 명절에 내려올 거라 했지? 그때 같이 시장도 가자.

    요즘은 혼자 있는 시간이 많아서 네 목소리 들으면 기분이 참 좋아.

    그리고 네가 보내준 편지 잘 읽었다. 글씨체가 초등학교 때 네가 쓰던 거랑 닮아서 참 반가웠어.

    아무튼 건강 잘 챙기고, 너무 늦게 자지 말고. 사랑한다, 우리 손녀."
    ---
    [실제 작업]

    [원본 텍스트]
    {request.text}

    [교정된 텍스트]
    """
    try:
        response = await model.generate_content_async(prompt)
        corrected_text = response.text.strip()

        # 성공 시, status가 포함된 JSON 본문을 반환합니다.
        return {
            "status": 200,
            "corrected_text": corrected_text
        }
    except Exception as e:
        # 실패 시, status가 포함된 JSON 본문을 직접 만들어 반환합니다.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "detail": f"편지 교정 중 오류 발생: {str(e)}"
            }
        )

    
