
from pathlib import Path
import logging
import os
import shutil
import time

import requests
from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)


def _create_placeholder(prompt: str, output_path: Path) -> Path:
    """Create a placeholder image for development and testing."""
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


def _get_huggingface_token() -> str:
    """Read a Hugging Face token without exposing it."""
    token = (
        os.environ.get("HF_TOKEN", "").strip()
        or os.environ.get("HF_API_KEY", "").strip()
        or str(getattr(settings, "HF_API_KEY", "") or "").strip()
    )

    if token:
        return token

    try:
        import streamlit as st

        token = (
            str(st.secrets.get("HF_TOKEN", "") or "").strip()
            or str(st.secrets.get("HF_API_KEY", "") or "").strip()
        )
    except Exception:
        token = ""

    return token


def _generate_with_huggingface(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate using Hugging Face Inference Providers."""
    token = _get_huggingface_token()

    if not token:
        raise RuntimeError(
            "Hugging Face token is missing from Streamlit Secrets."
        )

    from huggingface_hub import InferenceClient

    client = InferenceClient(
        provider="auto",
        api_key=token,
    )

    image = client.text_to_image(
        prompt,
        model=settings.HF_IMAGE_MODEL,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def _generate_with_ai_horde(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate a real image through the community-powered AI Horde API."""
    base_url = "https://aihorde.net/api/v2"

    headers = {
        "apikey": "0000000000",
        "Client-Agent": (
            "ComicCraftAI:1.0:"
            "github.com/rishabgamingyt2-ui/ComicCraftAI"
        ),
    }

    # AI Horde image dimensions should be multiples of 64.
    width = max(
        256,
        min(1024, (int(settings.IMAGE_WIDTH) // 64) * 64),
    )
    height = max(
        256,
        min(1024, (int(settings.IMAGE_HEIGHT) // 64) * 64),
    )

    payload = {
        "prompt": prompt,
        "params": {
            "width": width,
            "height": height,
            "steps": 20,
            "n": 1,
        },
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Submitting image request to AI Horde.")

    try:
        response = requests.post(
            f"{base_url}/generate/async",
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        request_id = response.json().get("id")

        if not request_id:
            raise RuntimeError(
                "AI Horde did not return a generation request ID."
            )

        logger.info("AI Horde request submitted successfully.")

        deadline = time.monotonic() + 600

        while time.monotonic() < deadline:
            time.sleep(5)

            status_response = requests.get(
                f"{base_url}/generate/status/{request_id}",
                headers=headers,
                timeout=30,
            )
            status_response.raise_for_status()
            status = status_response.json()

            if status.get("faulted"):
                raise RuntimeError(
                    "AI Horde could not complete this image request. "
                    "Try again later."
                )

            if status.get("done"):
                generations = status.get("generations") or []

                if not generations:
                    raise RuntimeError(
                        "AI Horde finished without returning an image."
                    )

                image_url = generations[0].get("img")

                if not image_url:
                    raise RuntimeError(
                        "AI Horde returned no image URL."
                    )

                image_response = requests.get(
                    image_url,
                    timeout=90,
                )
                image_response.raise_for_status()

                output_path.write_bytes(image_response.content)

                try:
                    with Image.open(output_path) as generated_image:
                        generated_image.verify()
                except Exception as exc:
                    output_path.unlink(missing_ok=True)
                    raise RuntimeError(
                        "AI Horde returned an invalid image file."
                    ) from exc

                logger.info("AI Horde image generation completed.")
                return output_path

        raise TimeoutError(
            "AI Horde is taking too long. Its queue may be busy. "
            "Please try again later."
        )

    except requests.RequestException as exc:
        logger.exception("AI Horde request failed.")
        raise RuntimeError(
            "Could not connect to AI Horde. Please try again later."
        ) from exc


def _generate_with_qwen(
    prompt: str,
    output_path: Path,
) -> Path:
    """Kept for compatibility; use AI Horde instead of exhausted Qwen."""
    logger.info("Redirecting Qwen provider to AI Horde.")
    return _generate_with_ai_horde(prompt, output_path)


def _generate_with_local_diffusers(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate using a locally installed Diffusers model."""
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
    """Generate one comic panel using the configured image provider."""
    settings.PANELS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = settings.PANELS_DIR / filename

    provider = str(settings.IMAGE_PROVIDER).lower().strip()
    logger.info("Image provider selected: %s", provider)

    if provider == "placeholder":
        return _create_placeholder(prompt, output_path)

    if provider in {"hf", "auto"}:
        return _generate_with_huggingface(prompt, output_path)

    if provider in {"qwen", "aihorde", "ai_horde"}:
        return _generate_with_ai_horde(prompt, output_path)

    if provider == "local":
        return _generate_with_local_diffusers(prompt, output_path)

    raise ValueError(
        f"Unsupported IMAGE_PROVIDER: {settings.IMAGE_PROVIDER}"
    )
