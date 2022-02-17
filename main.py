from fastapi import FastAPI
from db import models
from db.database import engine
from router import wallet, scraper


app = FastAPI()
app.include_router(wallet.router)
app.include_router(scraper.router)


@app.get("/")
def index():
    return {"message": "NC Wallet Reputation"}


models.Base.metadata.create_all(engine)
