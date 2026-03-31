from openai import AsyncOpenAI

from app.core.config import settings


client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_text(prompt: str) -> str:
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty response.")

    return content.strip()
