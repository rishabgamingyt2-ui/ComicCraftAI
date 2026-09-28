from pathlib import Path

from fpdf import FPDF

from app.config import settings
from app.schemas import ComicPanel


def save_pdf(
    title: str,
    panels: list[ComicPanel],
    filename: str,
) -> Path:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    for panel in panels:
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(
            0,
            12,
            title[:100],
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Panel number
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(
            0,
            8,
            f"Panel {panel.panel_number}",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Image
        image_path = Path(panel.image_path)

        if image_path.exists():
            pdf.image(
                str(image_path),
                x=15,
                y=45,
                w=180,
                h=100,
            )

        pdf.ln(108)

        # Scene
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(
            0,
            7,
            "Scene",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 10)

        scene_text = str(panel.scene_description or "")
        pdf.multi_cell(
            180,
            6,
            scene_text,
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.ln(3)

        # Narration
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(
            0,
            7,
            "Narration",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 10)

        narration_text = str(panel.narration or "")
        pdf.multi_cell(
            180,
            6,
            narration_text,
            new_x="LMARGIN",
            new_y="NEXT",
        )

    output_path = settings.EXPORTS_DIR / filename
    pdf.output(str(output_path))

    return output_path