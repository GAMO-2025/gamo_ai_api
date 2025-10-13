# --- 라이브러리 임포트 ---
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import google.generativeai as genai

# --- 라우터 및 데이터 모델 정의 ---
router = APIRouter()

# API가 클라이언트로부터 받을 요청(Request)의 형식을 정의합니다.
class LetterRequest(BaseModel):
    text: str = Field(..., description="STT로 변환된, 다듬어지지 않은 원본 편지 텍스트")

# API가 클라이언트에게 보낼 응답(Response)의 형식을 정의합니다.
class LetterResponse(BaseModel):
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
    아래 [원본 텍스트]는 음성을 텍스트로 변환한 초안입니다. 이 텍스트를 자연스러운 편지글로 다듬어 주세요.

    [규칙]
    1.  **내용을 절대 창작하거나 변경하지 말고**, 원래의 의미를 그대로 유지해야 합니다.
    2.  **원본 텍스트의 어조(예: 반말, 존댓말)를 절대 변경하지 말고 그대로 유지하세요.** 어색한 어미는 그 어조에 맞게 자연스럽게 다듬어 주세요.
    3.  "어...", "음..."과 같은 불필요한 추임새나 필러 단어는 자연스럽게 제거하세요.
    4.  띄어쓰기와 기본적인 맞춤법 오류를 교정하세요.
    5.  **의미의 흐름에 따라 적절하게 단락을 나누어(줄바꿈을 추가하여) 가독성을 높여주세요.**
    6.  만약 원본 텍스트가 이미 자연스럽고 수정할 내용이 거의 없다면, 원본 텍스트를 그대로 반환하세요.
    7.  교정된 최종 편지글 텍스트만 반환하고, 다른 설명은 절대 추가하지 마세요.

    [원본 텍스트]
    {request.text}
    """
    try:
        # Gemini API를 호출하여 응답을 받습니다.
        response = await model.generate_content_async(prompt)

        # Gemini가 교정한 텍스트를 변수에 저장합니다.
        corrected_text = response.text.strip()

        # 클라이언트에게 원본 letter_id와 교정된 텍스트를 함께 반환합니다.
        return {
            "corrected_text": corrected_text
        }
    except Exception as e:
        # 오류 발생 시 500 상태 코드와 함께 오류 메시지를 반환합니다.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"편지 교정 중 오류 발생: {str(e)}"
        )
    
