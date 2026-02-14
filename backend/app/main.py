from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, database, crud, schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Film Integration DB")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_model=schemas.SearchResponse)
async def search(q: str, page: int = 1, db: Session = Depends(get_db)):
    return crud.search_titles(db, query=q, page=page)


@app.get("/title/{title_id}", response_class=HTMLResponse)
async def get_title_page(title_id: int, request: Request, db: Session = Depends(get_db)):
    title = crud.get_title_with_details(db, title_id=title_id)
    if not title:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse("title.html", {"request": request, "title": title})
