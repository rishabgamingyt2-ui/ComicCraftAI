from uuid import uuid4

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.layout_builder import build_comic_layout
from app.schemas import PromptRequest
from app.services.image_generator import generate_image


router = APIRouter()

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR)
)


# ============================================================
# HOME PAGE
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
        },
    )


# ============================================================
# GENERATE COMIC - HTML FORM
# ============================================================

@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form("Main Character"),
    setting: str = Form("A realistic Indian setting"),
    tone: str = Form("Inspirational"),
    art_style: str = Form("Cinematic comic style"),
):
    user_request = PromptRequest(
        prompt=prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style,
    )

    # Step 1: Generate 5-panel outline
    outline = generate_outline(user_request)

    # Step 2: Generate detailed story
    story = generate_story(
        user_request,
        outline,
    )

    # Step 3: Generate images
    image_paths = []

    for panel in story.panels:
        filename = (
            f"panel_{panel.panel_number}_"
            f"{uuid4().hex[:8]}.png"
        )

        image_path = generate_image(
            panel.image_prompt,
            filename,
        )

        image_paths.append(image_path)

    # Step 4: Build comic layout
    comic_panels = build_comic_layout(
        story.panels,
        image_paths,
    )

    # Step 5: Create PDF
    pdf_filename = (
        f"comic_{uuid4().hex[:10]}.pdf"
    )

    save_pdf(
        story.title,
        comic_panels,
        pdf_filename,
    )

    # Step 6: Show preview
    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context={
            "title": story.title,
            "panels": comic_panels,
            "pdf_filename": pdf_filename,
        },
    )


# ============================================================
# GENERATE COMIC - JSON API
# ============================================================

@router.post("/generate-comic/json")
async def generate_comic_json(
    payload: PromptRequest,
):
    # Step 1: Generate outline
    outline = generate_outline(payload)

    # Step 2: Generate story
    story = generate_story(
        payload,
        outline,
    )

    # Step 3: Generate images
    image_paths = []

    for panel in story.panels:
        filename = (
            f"panel_{panel.panel_number}_"
            f"{uuid4().hex[:8]}.png"
        )

        image_path = generate_image(
            panel.image_prompt,
            filename,
        )

        image_paths.append(image_path)

    # Step 4: Build comic
    comic_panels = build_comic_layout(
        story.panels,
        image_paths,
    )

    # Step 5: Create PDF
    pdf_filename = (
        f"comic_{uuid4().hex[:10]}.pdf"
    )

    save_pdf(
        story.title,
        comic_panels,
        pdf_filename,
    )

    # Step 6: Return JSON
    return {
        "title": story.title,
        "panels": [
            panel.model_dump()
            for panel in comic_panels
        ],
        "pdf_filename": pdf_filename,
    }


# ============================================================
# API ALIAS
# ============================================================

@router.post("/api/generate-comic")
async def api_generate_comic(
    payload: PromptRequest,
):
    return await generate_comic_json(payload)


# ============================================================
# EXPORT SUCCESS PAGE
# ============================================================

@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
    filename: str,
):
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "filename": filename,
        },
    )


# ============================================================
# DOWNLOAD PDF
# ============================================================

@router.get("/download/{filename}")
async def download_pdf(
    filename: str,
):
    file_path = settings.EXPORTS_DIR / filename

    if not file_path.exists():
        return HTMLResponse(
            content="PDF file not found.",
            status_code=404,
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf",
    )


# ============================================================
# TEST IMAGE
# ============================================================

@router.get("/test-image")
async def test_image():
    filename = f"test_{uuid4().hex[:8]}.png"

    image_path = generate_image(
        "A simple comic panel test image",
        filename,
    )

    return {
        "message": "Test image generated successfully.",
        "image_path": str(image_path),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
    }