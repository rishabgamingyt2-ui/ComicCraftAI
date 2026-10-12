
from pathlib import Path
import logging
import shutil

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)


def _create_placeholder(prompt: str, output_path: Path) -> Path:
    """Create a placeholder image for development/testing."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
    """Generate an image using Hugging Face Inference Providers."""
    if not settings.HF_API_KEY:
        raise RuntimeError(
            "HF_API_KEY is missing. Configure it in Streamlit Secrets."
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    return output_path


def _generate_with_qwen(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate a comic panel using the public Qwen Image Space."""
    from gradio_client import Client

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Connecting to the Qwen Image Space.")

        client = Client("Qwen/Qwen-Image-2.1")

        logger.info("Preparing the Qwen generation request.")

        client.predict(
            [],
            prompt,
            False,
            False,
            "speed",
            0,
            True,
            api_name="/prepare_request",
        )

        logger.info("Requesting image generation from Qwen.")

        result = client.predict(
            prompt,
            False,
            False,
            "./generation_logs_paper_case",
            0,
            settings.IMAGE_HEIGHT,
            settings.IMAGE_WIDTH,
            "",
            api_name="/generate_request",
        )

        # Some Gradio endpoints return a file path directly;
        # others return a dictionary containing the file path.
        if isinstance(result, dict):
            result = result.get("path") or result.get("name")

        # Handle a list or tuple if the Space returns a wrapped result.
        if isinstance(result, (list, tuple)) and result:
            result = result[0]

        if isinstance(result, dict):
            result = result.get("path") or result.get("name")

        if not isinstance(result, (str, Path)):
            raise RuntimeError(
                "Qwen returned an unsupported result instead of an image path. "
                f"Result type: {type(result).__name__}"
            )

        source_path = Path(result)

        if not source_path.is_file():
            raise RuntimeError(
                "Qwen returned a file path that does not exist in this runtime."
            )

        if source_path.resolve() != output_path.resolve():
            shutil.copy2(source_path, output_path)

        # Verify the output is a readable image.
        with Image.open(output_path) as generated_image:
            generated_image.verify()

        logger.info("Qwen image generated successfully.")

        return output_path

    except Exception as exc:
        # Log the full exception for diagnosis in Streamlit Cloud logs.
        logger.exception("Qwen image generation failed.")

        # Preserve clear validation errors.
        if isinstance(exc, RuntimeError):
            raise

        # Avoid hiding the actual API or connection error.
        raise RuntimeError(
            f"Qwen image generation failed ({type(exc).__name__}): {exc}"
        ) from exc


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
        torch_dtype=(
            torch.float16 if device == "cuda" else torch.float32
        ),
    ).to(device)

    result = pipeline(
        prompt,
        width=settings.IMAGE_WIDTH,
        height=settings.IMAGE_HEIGHT,
        num_inference_steps=settings.IMAGE_STEPS,
        guidance_scale=settings.IMAGE_GUIDANCE,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.images[0].save(output_path)

    return output_path


def generate_image(prompt: str, filename: str) -> Path:
    """Generate one comic panel image using the configured provider."""
    settings.PANELS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = settings.PANELS_DIR / filename

    provider = settings.IMAGE_PROVIDER.lower().strip()

    logger.info("Image provider selected: %s", provider)

    if provider == "placeholder":
        return _create_placeholder(prompt, output_path)

    if provider in {"hf", "auto"}:
        return _generate_with_huggingface(prompt, output_path)

    if provider == "qwen":
        return _generate_with_qwen(prompt, output_path)

    if provider == "local":
        return _generate_with_local_diffusers(prompt, output_path)

    raise ValueError(
        f"Unsupported IMAGE_PROVIDER: {settings.IMAGE_PROVIDER}"
    )
