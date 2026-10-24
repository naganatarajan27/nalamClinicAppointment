from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class Page(BaseModel):
    total: int
    page: int
    page_size: int
