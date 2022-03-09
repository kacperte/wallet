import json

from fastapi import APIRouter, Depends, Request
from schemas import WalletBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.db_wallet import get_wallet
from tasks import wallet_reputation
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/wallet", tags=["wallet"])
templates = Jinja2Templates(directory="templates")
# router.mount("/static", StaticFiles(directory="static"), name="static")


# Make or update wallet
@router.get(
    "/run/{id}",
    summary="Make Reputation Wallet ",
    description="This API call function creates a wallet reputation for the specified address.",
    response_description="Message with status",
)
async def create_or_update_database(id: str):
    """

    :param id: wallet adress
    :return: status info
    """
    wallet_reputation.delay(id)

    return {"Status": "Task successfully add to execute"}


# Read one user
@router.get(
    "/{id}",
    response_model=WalletBase,
    summary="Retrieve one wallet",
    description="This API call function fetching a wallet reputation for the specified address.",
    response_description="Wallet reputation status",
)
def get_wallet_info(request: Request, id: str, db: Session = Depends(get_db)):
    """

    :param request: request
    :param id: wallet adress
    :param db: connect to database
    :return: json
    """
    result = get_wallet(db, id)
    return JSONResponse(content=json.dumps(result))
