from celery import Celery
import os
from agents.polygonScraper import PolygonscanScraper
from agents.walletReputation import WalletReputation

app = Celery("queue")

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

app.conf.update(
    BROKER_URL=os.environ["REDIS_URL"],
    CELERY_RESULT_BACKEND=f"db+{SQLALCHEMY_DATABASE_URL}",
)


@app.task(name="polygonScraper-NC")
def polygon_scraper_nc(
    nc_url: str = "https://polygonscan.com/token/0x64a795562b02830ea4e43992e761c96d208fc58d",
):
    PolygonscanScraper().scrap_from_url(url=nc_url)

    return {"message": "Success"}


@app.task(name="polygonScraper-LP")
def polygon_scraper_lp(
    lp_url: str = "https://polygonscan.com/token/0x78e16D2fACb80ac536887D1376ACD4EeeDF2fA08",
):
    PolygonscanScraper().scrap_from_url(url=lp_url)

    return {"message": "Success"}


@app.task(name="walletReputation")
def wallet_reputation(id: str):
    WalletReputation(id).add_reputation_to_db()

    return {"message": "Success"}


@app.task(name="walletReputationAll")
def wallet_reputation_all(adr_list: list):
    print(adr_list)
    for address in adr_list:
        WalletReputation(address).add_reputation_to_db()

    return {"message": "Success"}
