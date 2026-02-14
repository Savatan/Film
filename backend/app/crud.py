from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from . import models, schemas


PER_PAGE = 20


def search_titles(db: Session, query: str, page: int = 1) -> schemas.SearchResponse:
    q = db.query(models.Title).filter(
        func.lower(models.Title.canonical_title).contains(query.lower())
        | func.lower(models.Title.original_title).contains(query.lower())
    )

    total = q.count()
    items: List[models.Title] = (
        q.order_by(models.Title.rating_global.desc().nullslast())
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    return schemas.SearchResponse(
        total=total,
        page=page,
        per_page=PER_PAGE,
        results=items,
    )


def get_title_with_details(db: Session, title_id: int):
    return (
        db.query(models.Title)
        .filter(models.Title.id == title_id)
        .options(
            joinedload(models.Title.offers),
            joinedload(models.Title.attributes),
        )
        .first()
    )
