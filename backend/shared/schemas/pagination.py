from pydantic import BaseModel, Field

class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total_items: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)

class Page(BaseModel):
    items: list[object]
    pagination: Pagination
