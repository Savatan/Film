from typing import List, Dict
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
import json

from . import models


def normalize_title(title: str) -> str:
    if not title:
        return ""
    t = title.lower().strip()
    for suffix in ["(фильм)", "(сериал)", "(movie)", "(tv series)"]:
        t = t.replace(suffix, "")
    return " ".join(t.split())


def deduplicate_raw_offers(db: Session, similarity_threshold: int = 90):
    raw_items: List[models.RawOffer] = db.query(models.RawOffer).all()

    groups: List[List[models.RawOffer]] = []

    for item in raw_items:
        placed = False
        norm_title = normalize_title(item.raw_original_title or item.raw_title)
        for group in groups:
            g0 = group[0]
            g0_norm = normalize_title(g0.raw_original_title or g0.raw_title)
            if item.raw_year and g0.raw_year and item.raw_year == g0.raw_year:
                if norm_title == g0_norm or fuzz.ratio(norm_title, g0_norm) >= similarity_threshold:
                    group.append(item)
                    placed = True
                    break
        if not placed:
            groups.append([item])

    for group in groups:
        rep = group[0]
        title = models.Title(
            canonical_title=rep.raw_title,
            original_title=rep.raw_original_title,
            year=rep.raw_year,
            type=rep.raw_type,
            description=rep.raw_description,
        )
        db.add(title)
        db.flush()

        all_genres = set()
        all_countries = set()
        ratings = []

        for item in group:
            offer = models.Offer(
                title_id=title.id,
                website_name=item.source,
                website_internal_id=None,
                rating_site=item.raw_rating,
                url=item.url,
            )
            db.add(offer)
            if item.raw_rating is not None:
                ratings.append(item.raw_rating)

            if item.raw_genres:
                try:
                    genres = json.loads(item.raw_genres)
                    all_genres.update(genres)
                except Exception:
                    pass
            if item.raw_countries:
                try:
                    countries = json.loads(item.raw_countries)
                    all_countries.update(countries)
                except Exception:
                    pass

        if ratings:
            title.rating_global = sum(ratings) / len(ratings)

        for g in all_genres:
            db.add(models.TitleAttribute(
                title_id=title.id,
                attribute_name="genre",
                attribute_value=g,
            ))
        for c in all_countries:
            db.add(models.TitleAttribute(
                title_id=title.id,
                attribute_name="country",
                attribute_value=c,
            ))

    db.commit()
