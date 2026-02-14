import json
from pathlib import Path
from sqlalchemy.orm import Session

from . import database, models
from .deduplication import deduplicate_raw_offers


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_raw_json_to_db(db: Session, source: str, path: Path):
    with path.open("r", encoding="utf-8") as f:
        items = json.load(f)
    for item in items:
        db.add(models.RawOffer(
            source=source,
            raw_title=item.get("title"),
            raw_original_title=item.get("original_title"),
            raw_year=item.get("year"),
            raw_type=item.get("type"),
            raw_description=item.get("description"),
            raw_rating=item.get("rating"),
            raw_genres=json.dumps(item.get("genres") or []),
            raw_countries=json.dumps(item.get("countries") or []),
            url=item.get("url"),
        ))
    db.commit()


def run_etl():
    db = database.SessionLocal()
    try:
        models.Base.metadata.create_all(bind=database.engine)
        data_dir = DATA_DIR
        sources = [
            ("imdb", data_dir / "imdb.json"),
            ("tmdb", data_dir / "tmdb.json"),
            ("kinopoisk", data_dir / "kinopoisk.json"),
        ]
        for source, path in sources:
            if path.exists():
                load_raw_json_to_db(db, source, path)
        deduplicate_raw_offers(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_etl()
