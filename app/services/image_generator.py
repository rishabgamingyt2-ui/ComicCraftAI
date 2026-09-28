from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import settings


def _create_placeholder(
    prompt: str,
    output_path: Path,
) -> Path:
    """Create a simple placeholder image for development/testing."""

    width = settings.IMAGE_WIDTH
    height = settings.IMAGE_HEIGHT

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title = "ComicCraft"
    subtitle = "AI Comic Panel"

    try:
        title_font = ImageFont.truetype("arial.ttf", 42)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    title_box = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_box[2] - title_box[0]
    title_height = title_box[3] - title_box[1]

    draw.text(
        ((width - title_width) / 2, height / 2 - 80),
        title,
        fill="black",
        font=title_font,
    )

    subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_box[2] - subtitle_box[0]

    draw.text(
        ((width - subtitle_width) / 2, height / 2),
        subtitle,
        fill="black",
        font=subtitle_font,
    )

    image.save(output_path)

    return output_path


def _generate_with_huggingface(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate an image using Hugging Face."""

    if not settings.HF_API_KEY:
        raise RuntimeError(
            "HF_API_KEY is missing. Add it to the .env file."
        )

    from huggingface_hub import InferenceClient

    client = InferenceClient(
        provider="auto",
        api_key=settings.HF_API_KEY,
    )

    image = client.text_to_image(
        prompt,
        model=settings.HF_IMAGE_MODEL,
    )

    image.save(output_path)

    return output_path


def _generate_with_local_diffusers(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate an image using a local Diffusers model."""

    import torch
    from diffusers import StableDiffusionPipeline

    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipeline = StableDiffusionPipeline.from_pretrained(
        settings.LOCAL_IMAGE_MODEL,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )

    pipeline = pipeline.to(device)

    result = pipeline(
        prompt,
        width=settings.IMAGE_WIDTH,
        height=settings.IMAGE_HEIGHT,
        num_inference_steps=settings.IMAGE_STEPS,
        guidance_scale=settings.IMAGE_GUIDANCE,
    )

    image = result.images[0]
    image.save(output_path)

    return output_path


def generate_image(
    prompt: str,
    filename: str,
) -> Path:
    """Generate one comic panel image."""

    settings.PANELS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = settings.PANELS_DIR / filename

    provider = settings.IMAGE_PROVIDER.lower().strip()

    if provider == "placeholder":
        return _create_placeholder(prompt, output_path)

    if provider in {"hf", "auto"}:
        return _generate_with_huggingface(prompt, output_path)

    if provider == "local":
        return _generate_with_local_diffusers(prompt, output_path)

    raise ValueError(
        f"Unsupported IMAGE_PROVIDER: {settings.IMAGE_PROVIDER}"
    )