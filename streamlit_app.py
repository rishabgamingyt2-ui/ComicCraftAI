
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
        "HF_TOKEN",
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


# Import modules after loading secrets
from app.config import settings
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.layout_builder import build_comic_layout
from app.services.image_generator import generate_image
from app.exporters import save_pdf


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ComicCraft AI",
    page_icon="🎨",
    layout="wide",
)


# ---------------------------------------------------------
# Custom styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .comic-panel {
        max-width: 650px;
        margin-left: auto;
        margin-right: auto;
    }

    .comic-panel img {
        max-width: 100%;
        height: auto;
        object-fit: contain;
    }

    div[data-testid="stImage"] {
        max-width: 650px;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
        from app.schemas import PromptRequest

        with st.status(
            "Creating your comic...",
            expanded=True,
        ) as status:
            st.write("🧠 Generating story outline...")

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
                    f"streamlit_panel_{panel.panel_number}.png"
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
                f"streamlit_comic_{story.title[:20]}.pdf"
            )

            pdf_path = save_pdf(
                story.title,
                comic_panels,
                pdf_filename,
            )

            status.update(
                label="Comic generated successfully! 🎉",
                state="complete",
                expanded=False,
            )

        # -------------------------------------------------
        # Display result
        # -------------------------------------------------
        st.divider()
        st.header(f"📖 {story.title}")

        for panel in comic_panels:
            st.subheader(f"Panel {panel.panel_number}")

            image_path = Path(panel.image_path)

            if image_path.is_file():
                # Limit display width while preserving aspect ratio.
                st.image(
                    str(image_path),
                    width=550,
                )
            else:
                st.warning(
                    f"Image for Panel {panel.panel_number} "
                    "could not be found."
                )

            if hasattr(panel, "scene") and panel.scene:
                st.write(f"**Scene:** {panel.scene}")

            if (
                hasattr(panel, "narration")
                and panel.narration
            ):
                st.write(
                    f"**Narration:** {panel.narration}"
                )

            with st.expander("View image prompt"):
                matching_panel = next(
                    (
                        item
                        for item in story.panels
                        if item.panel_number == panel.panel_number
                    ),
                    None,
                )

                if matching_panel:
                    st.write(matching_panel.image_prompt)

            st.divider()

        # -------------------------------------------------
        # PDF download
        # -------------------------------------------------
        pdf_file_path = settings.EXPORTS_DIR / pdf_filename

        if pdf_file_path.exists():
            with open(pdf_file_path, "rb") as file:
                st.download_button(
                    label="📥 Download Comic PDF",
                    data=file.read(),
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.warning(
                "The comic was generated, but the PDF file "
                "could not be found."
            )

    except Exception as error:
        st.error(
            "Something went wrong while generating the comic."
        )
        st.exception(error)


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()

st.caption(
    "ComicCraft AI • Powered by Gemini + AI image generation"
)
