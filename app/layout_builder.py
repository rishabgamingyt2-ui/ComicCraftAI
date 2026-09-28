from pathlib import Path

from app.schemas import ComicPanel, PanelStory


def build_comic_layout(
    story_panels: list[PanelStory],
    image_paths: list[Path],
) -> list[ComicPanel]:
    if len(story_panels) != len(image_paths):
        raise ValueError(
            "The number of story panels must match the number of images."
        )

    comic_panels = []

    for story_panel, image_path in zip(story_panels, image_paths):
        comic_panels.append(
            ComicPanel(
                panel_number=story_panel.panel_number,
                scene_description=story_panel.scene_description,
                caption=story_panel.caption,
                narration=story_panel.narration,
                dialogue=story_panel.dialogue,
                image_prompt=story_panel.image_prompt,
                image_path=str(image_path),
            )
        )

    return comic_panels