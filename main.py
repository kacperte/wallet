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


@app.get("/form")
def form_post(request: Request):
    result = "Type a number"
    return templates.TemplateResponse(
        "form.html", context={"request": request, "result": result}
    )


@app.post("/form")
def form_post(request: Request, num: int = Form(...)):
    result = num
    return templates.TemplateResponse(
        "form.html", context={"request": request, "result": result}
    )


models.Base.metadata.create_all(engine)
