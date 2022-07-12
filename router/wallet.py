from fastapi import APIRouter, Depends, Request
from schemas import WalletBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.db_wallet import get_wallet, get_transactions_history
from tasks import wallet_reputation
from agents.walletReputation import all_addresses_generator


router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post(
    "/run",
    summary="Make Reputation Wallet for all address from NC Coin network ",
    description="This API call function creates a wallet reputation for the all addresses",
    response_description="Message with status",
)
async def create_or_update_all():
    """
    :return: status info
    """
    addresses_list = list(set([address for address in all_addresses_generator()]))
    addresses_list.remove("Null Address: 0x000…000")
    addresses_list.remove("0x: Exchange Proxy Flash Wallet")
    wallet_reputation.delay(addresses_list)

    return {"Status": "Tasks successfully add to execute"}


@router.get(
    "/wallet/{id}",
    response_model=WalletBase,
    summary="Retrieve one wallet",
    description="This API call function fetching a wallet reputation for the specified address. ",
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
    return result


@router.get(
    "/transactions/{id}",
    response_model=WalletBase,
    summary="Retrieve wallet transactions history",
    description="This API call function fetching a wallet reputation for the specified address. ",
    response_description="Wallet transactions status",
)
def get_transactions_info(request: Request, id: str, db: Session = Depends(get_db)):
    """
    :param request: request
    :param id: wallet adress
    :param db: connect to database
    :return: json
    """
    result = get_transactions_history(db, id)
    return result
