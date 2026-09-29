import os
from pathlib import Path

import streamlit as st


# ---------------------------------------------------------
# Load secrets from Streamlit Cloud / local environment
# ---------------------------------------------------------
def load_secrets():
    secret_keys = [
        "GEMINI_API_KEY",
        "GEMINI_OUTLINE_MODEL",
        "GEMINI_STORY_MODEL",
        "IMAGE_PROVIDER",
        "HF_API_KEY",
        "HF_IMAGE_MODEL",
        "LOCAL_IMAGE_MODEL",
        "IMAGE_WIDTH",
        "IMAGE_HEIGHT",
        "IMAGE_STEPS",
        "IMAGE_GUIDANCE",
        "MAX_PANELS",
        "MAX_PROMPT_LENGTH",
    ]

    for key in secret_keys:
        try:
            if key in st.secrets:
                os.environ[key] = str(st.secrets[key])
        except Exception:
            pass


load_secrets()


# Import ComicCraft modules AFTER loading secrets
from app.config import settings
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.layout_builder import build_comic_layout
from app.services.image_generator import generate_image
from app.exporters import save_pdf


# ---------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ComicCraft AI",
    page_icon="🎨",
    layout="wide",
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("🎨 ComicCraft AI")
st.subheader("AI Comic Story Creator using Gemini Models")

st.write(
    "Create a personalized 5-panel comic story using Gemini AI "
    "and AI-generated images."
)

st.divider()


# ---------------------------------------------------------
# Input section
# ---------------------------------------------------------
st.header("📝 Create Your Comic")

prompt = st.text_area(
    "Story Idea",
    placeholder=(
        "Example: A brave young farmer discovers a new way "
        "to save his village..."
    ),
    height=150,
)

col1, col2 = st.columns(2)

with col1:
    character_name = st.text_input(
        "Main Character",
        value="Main Character",
    )

    setting = st.text_input(
        "Setting",
        value="A realistic Indian setting",
    )

with col2:
    tone = st.selectbox(
        "Tone",
        [
            "Inspirational",
            "Funny",
            "Dramatic",
            "Emotional",
            "Adventure",
        ],
    )

    art_style = st.selectbox(
        "Art Style",
        [
            "Cinematic comic style",
            "2D cartoon style",
            "3D cartoon style",
            "Realistic comic style",
            "Anime style",
        ],
    )


# ---------------------------------------------------------
# Generate Comic
# ---------------------------------------------------------
if st.button(
    "🚀 Generate Comic",
    type="primary",
    use_container_width=True,
):

    if not prompt.strip():
        st.warning("Please enter a story idea first.")
        st.stop()

    try:
        with st.status(
            "Creating your comic...",
            expanded=True,
        ) as status:

            st.write("🧠 Generating story outline...")

            from app.schemas import PromptRequest

            user_request = PromptRequest(
                prompt=prompt,
                character_name=character_name,
                setting=setting,
                tone=tone,
                art_style=art_style,
            )

            outline = generate_outline(user_request)

            st.write("✍️ Writing the 5-panel story...")

            story = generate_story(
                user_request,
                outline,
            )

            st.write("🎨 Generating comic images...")

            image_paths = []

            for panel in story.panels:
                filename = (
                    f"streamlit_panel_"
                    f"{panel.panel_number}.png"
                )

                image_path = generate_image(
                    panel.image_prompt,
                    filename,
                )

                image_paths.append(image_path)

            st.write("📐 Building comic layout...")

            comic_panels = build_comic_layout(
                story.panels,
                image_paths,
            )

            st.write("📄 Creating PDF...")

            pdf_filename = (
                f"streamlit_comic_{story.title[:20]}"
                ".pdf"
            )

            pdf_path = save_pdf(
                story.title,
                comic_panels,
                pdf_filename,
            )

            status.update(
                label="Comic generated successfully! 🎉",
                state="complete",
            )


        # -------------------------------------------------
        # Display result
        # -------------------------------------------------
        st.divider()

        st.header(f"📖 {story.title}")

        for panel in comic_panels:

            st.subheader(
                f"Panel {panel.panel_number}"
            )

            st.image(
                str(panel.image_path),
                use_container_width=True,
            )

            if hasattr(panel, "scene"):
                st.write(
                    f"**Scene:** {panel.scene}"
                )

            if hasattr(panel, "narration"):
                st.write(
                    f"**Narration:** {panel.narration}"
                )

            st.divider()


        # -------------------------------------------------
        # PDF download
        # -------------------------------------------------
        pdf_file_path = (
            settings.EXPORTS_DIR / pdf_filename
        )

        if pdf_file_path.exists():

            with open(
                pdf_file_path,
                "rb",
            ) as file:

                st.download_button(
                    label="📥 Download Comic PDF",
                    data=file.read(),
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                )

    except Exception as error:

        st.error(
            "Something went wrong while generating "
            "the comic."
        )

        st.exception(error)


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()

st.caption(
    "ComicCraft AI • Powered by Gemini + Hugging Face"
)