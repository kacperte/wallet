from fastapi import APIRouter
from tasks import polygon_scraper_lp, polygon_scraper_nc

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post(
    "/run-nc",
    summary="Scrap polygonscan to retrive NC transaction",
    description="This API call function scrapping all transaction from NC network. After that "
    "transaction are cleaning and adding to Database.",
    response_description="Message with status",
)
async def create_or_update_database_nc():
    polygon_scraper_nc.delay()

    return {"Status": "Task successfully add to execute"}


@router.post(
    "/run-lp",
    summary="Scrap polygonscan to retrive LP transaction",
    description="This API call function scrapping all transaction from NC network. After that "
    "transaction are cleaning and adding to Database.",
    response_description="Message with status",
)
async def create_or_update_database_lp():
    polygon_scraper_lp.delay()

    return {"Status": "Task successfully add to execute"}
