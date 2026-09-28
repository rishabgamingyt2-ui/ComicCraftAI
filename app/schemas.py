from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1200)
    character_name: str = Field(default="Main Character", max_length=100)
    setting: str = Field(default="A realistic Indian setting", max_length=200)
    tone: str = Field(default="Inspirational", max_length=100)
    art_style: str = Field(default="Cinematic comic style", max_length=150)


class PanelOutline(BaseModel):
    panel_number: int
    scene: str
    action: str


class OutlineResponse(BaseModel):
    title: str
    panels: list[PanelOutline]


class PanelStory(BaseModel):
    panel_number: int
    scene_description: str
    caption: str
    narration: str
    dialogue: str
    image_prompt: str


class StoryResponse(BaseModel):
    title: str
    panels: list[PanelStory]


class ComicPanel(BaseModel):
    panel_number: int
    scene_description: str
    caption: str
    narration: str
    dialogue: str
    image_prompt: str
    image_path: str


class ComicResponse(BaseModel):
    title: str
    panels: list[ComicPanel]
    pdf_filename: str | None = None