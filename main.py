from fastapi import FastAPI
from db import models
from db.database import engine
from router import wallet, scraper

app = FastAPI()
app.include_router(wallet.router)
app.include_router(scraper.router)
models.Base.metadata.create_all(engine)
