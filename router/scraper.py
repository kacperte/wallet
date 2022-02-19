from fastapi import APIRouter
from tasks import polygon_scraper

router = APIRouter(prefix="/scraper", tags=["scraper"])


# Connect to polygonscan, collect data and create/update Database
@router.post(
    "/run",
    summary="Scrap polygonscan/NC",
    description="This API call function scrapping all transaction from NC Coin network.",
    response_description="Message with status",
)
def create_or_update_database():
    result = polygon_scraper.delay()

    return {"Data": result}
