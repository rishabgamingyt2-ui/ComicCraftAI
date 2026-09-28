from google import genai

from app.config import settings
from app.schemas import OutlineResponse, PromptRequest, StoryResponse


def generate_story(
    request: PromptRequest,
    outline: OutlineResponse,
) -> StoryResponse:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your Gemini API key to the .env file."
        )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    outline_text = "\n".join(
        [
            f"Panel {panel.panel_number}: "
            f"Scene: {panel.scene} | Action: {panel.action}"
            for panel in outline.panels
        ]
    )

    prompt = f"""
You are the detailed story writer for ComicCraft.

Create the complete 5-panel comic story using the outline below.

Original user request:
{request.prompt}

Character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Comic title:
{outline.title}

Outline:
{outline_text}

Requirements:
- Create exactly 5 panels.
- Preserve the same character and story continuity.
- Give every panel a detailed scene description.
- Give every panel a short caption.
- Give every panel narration suitable for a comic.
- Give dialogue only when it naturally fits the scene.
- Create a detailed image-generation prompt for every panel.
- The image prompt must describe characters, environment, action,
  lighting, composition, and requested art style.
- Do not change the main character's identity between panels.
"""

    response = client.models.generate_content(
        model=settings.GEMINI_STORY_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": StoryResponse,
        },
    )

    return StoryResponse.model_validate_json(response.text)