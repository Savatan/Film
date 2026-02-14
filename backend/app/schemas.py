from typing import List, Optional
from pydantic import BaseModel


class OfferOut(BaseModel):
    website_name: str
    rating_site: Optional[float]
    url: str

    class Config:
        orm_mode = True


class AttributeOut(BaseModel):
    attribute_name: str
    attribute_value: str

    class Config:
        orm_mode = True


class TitleOut(BaseModel):
    id: int
    canonical_title: str
    original_title: Optional[str]
    year: Optional[int]
    type: Optional[str]
    description: Optional[str]
    poster_url: Optional[str]
    rating_global: Optional[float]

    class Config:
        orm_mode = True


class TitleDetailOut(TitleOut):
    offers: List[OfferOut]
    attributes: List[AttributeOut]


class SearchResponse(BaseModel):
    total: int
    page: int
    per_page: int
    results: List[TitleOut]
