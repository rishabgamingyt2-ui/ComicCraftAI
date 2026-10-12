
def _generate_with_qwen(
    prompt: str,
    output_path: Path,
) -> Path:
    """Generate a comic panel using the Qwen Space with authentication."""
    import logging
    import os

    from gradio_client import Client

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Read the token without printing or exposing it.
        hf_token = os.environ.get("HF_TOKEN", "").strip()

        if not hf_token:
            try:
                import streamlit as st
                hf_token = str(st.secrets.get("HF_TOKEN", "")).strip()
            except Exception:
                hf_token = ""

        if not hf_token:
            raise RuntimeError(
                "HF_TOKEN is missing. Add it to Streamlit Secrets."
            )

        logging.info("Connecting to the authenticated Qwen Space.")

        client = Client(
            "Qwen/Qwen-Image-2.1",
            hf_token=hf_token,
        )

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

        if isinstance(result, dict):
            result = result.get("path") or result.get("name")

        if isinstance(result, (list, tuple)) and result:
            result = result[0]

        if isinstance(result, dict):
            result = result.get("path") or result.get("name")

        if not isinstance(result, (str, Path)):
            raise RuntimeError(
                "Qwen did not return a valid image file path."
            )

        source_path = Path(result)

        if not source_path.is_file():
            raise RuntimeError(
                "The generated image file was not found."
            )

        if source_path.resolve() != output_path.resolve():
            shutil.copy2(source_path, output_path)

        with Image.open(output_path) as image:
            image.verify()

        logging.info("Qwen image generated successfully.")
        return output_path

    except Exception as exc:
        logging.exception("Qwen image generation failed.")

        if isinstance(exc, RuntimeError):
            raise

        raise RuntimeError(
            f"Qwen image generation failed "
            f"({type(exc).__name__}): {exc}"
        ) from exc
