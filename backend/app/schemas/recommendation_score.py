from pydantic import BaseModel, Field


class ProductScore(BaseModel):
    product_id: str
    score: float
    reasons: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)

