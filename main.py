from fastapi import FastAPI
from db import models
from db.database import engine
from router import wallet, scraper
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(wallet.router)
app.include_router(scraper.router)
models.Base.metadata.create_all(engine)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
