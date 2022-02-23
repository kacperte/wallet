from fastapi import APIRouter
from tasks import polygon_scraper_lp, polygon_scraper_nc

router = APIRouter(prefix="/scraper", tags=["scraper"])


# Connect to polygonscan, collect data (nc transaction) to create/update Database
@router.post(
    "/run-nc",
    summary="Scrap polygonscan/NC",
    description="This API call function scrapping all transaction from network.",
    response_description="Message with status",
)
async def create_or_update_database_nc():
    polygon_scraper_nc.delay()

    return {"Data": "OK"}


# Connect to polygonscan, collect data (lp transaction) to create/update Database
@router.post(
    "/run-lp",
    summary="Scrap polygonscan/LP",
    description="This API call function scrapping all transaction from network.",
    response_description="Message with status",
)
async def create_or_update_database_lp():
    polygon_scraper_lp.delay()

    return {"Data": "OK"}
