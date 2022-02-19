from celery import Celery
import os
from agents.polygonScraper import PolygonscanScraper
from agents.walletReputation import WalletReputation

app = Celery("queue")
app.conf.update(
     BROKER_URL=os.environ["REDIS_URL"],
     CELERY_RESULT_BACKEND=os.environ["DATABASE_URL"]
 )


@app.task(name="polygonScraper")
def polygon_scraper(
        nc_url: str = "https://polygonscan.com/token/0x64a795562b02830ea4e43992e761c96d208fc58d",
        lp_url: str = "https://polygonscan.com/token/0x78e16D2fACb80ac536887D1376ACD4EeeDF2fA08"
):
    PolygonscanScraper().scrap_from_url(
        url=nc_url
    )
    PolygonscanScraper().scrap_from_url(
        url=lp_url
    )
    return {"message": "Success"}


@app.task(name="walletReputation")
def wallet_reputation(id: str):
    WalletReputation(id).add_reputation_to_db()

    return {"message": "Success"}
