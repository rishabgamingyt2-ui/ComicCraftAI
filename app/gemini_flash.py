from google import genai

from app.config import settings
from app.schemas import OutlineResponse, PromptRequest


def generate_outline(request: PromptRequest) -> OutlineResponse:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your Gemini API key to the .env file."
        )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""
You are the story-outline generator for ComicCraft.

Create a personalized comic based on the user's request.

User story:
{request.prompt}

Character name:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Requirements:
- Create exactly 5 panels.
- Give the comic a clear title.
- Each panel must have a concise scene description.
- Each panel must describe the main action.
- Maintain character and story continuity from panel 1 to panel 5.
- The story should have a beginning, development, and ending.
"""

    response = client.models.generate_content(
        model=settings.GEMINI_OUTLINE_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": OutlineResponse,
        },
    )

    return OutlineResponse.model_validate_json(response.text)