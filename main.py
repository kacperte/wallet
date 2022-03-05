from fastapi import FastAPI, Request, Form
from db import models
from db.database import engine
from router import wallet, scraper
from fastapi.templating import Jinja2Templates


app = FastAPI()
app.include_router(wallet.router)
app.include_router(scraper.router)
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request, id: str = Form(...)):
    return templates.TemplateResponse("main_page.html", context={"request": request})


models.Base.metadata.create_all(engine)
