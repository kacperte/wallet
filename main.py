from fastapi import FastAPI, Request, Form
from db import models
from db.database import engine
from router import wallet, scraper
from fastapi.templating import Jinja2Templates
import requests


app = FastAPI()
app.include_router(wallet.router)
app.include_router(scraper.router)
templates = Jinja2Templates(directory="templates/")


@app.get("/main")
def index(request: Request):
    result = "whateva"
    return templates.TemplateResponse(
        "main_page.html", context={"request": request, "result": result}
    )


@app.post("/main")
def index(request: Request, address: str = Form(...)):
    URL = "https://wallet-reputation.herokuapp.com/wallet/"
    result = address
    return templates.TemplateResponse(
        "main_page.html", context={"request": request, "result": result}
    )


models.Base.metadata.create_all(engine)
