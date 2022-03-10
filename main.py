import json

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


@app.get("/")
def wallet_view(request: Request):
    result = "Type a address"
    return templates.TemplateResponse(
        "main_page.html", context={"request": request, "result": result}
    )


@app.post("/")
def wallet_view(request: Request, address: str = Form(...)):
    URL = "https://wallet-reputation.herokuapp.com/wallet/"
    result = requests.get(URL + address).json()

    return templates.TemplateResponse(
        "main_page.html", context={"request": request, "result": result}
    )


models.Base.metadata.create_all(engine)
