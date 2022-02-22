from fastapi import APIRouter, Depends
from schemas import WalletBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.db_wallet import get_wallet
from tasks import wallet_reputation

router = APIRouter(prefix="/wallet", tags=["wallet"])


# Make or update wallet
@router.post(
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
    result = wallet_reputation.delay(id)

    return {"message": result.get()}


# Read one user
@router.get(
    "/{id}",
    response_model=WalletBase,
    summary="Retrieve one wallet",
    description="This API call function fetching a wallet reputation for the specified address.",
    response_description="Wallet reputation status",
)
async def get_wallet_info(id: str, db: Session = Depends(get_db)):
    """

    :param id: wallet adress
    :param db: connect to database
    :return: json
    """
    return get_wallet(db, id)
