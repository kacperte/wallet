from sqlalchemy.orm.session import Session
from db.models import DbWalletReputation
from fastapi import HTTPException, status


def get_wallet(db: Session, id: str):
    """
     Get concrete wallet reputation from Database

    :param db: connect to database
    :param id: Wallet adress
    :return: Wallet information
    """
    wallet = (
        db.query(DbWalletReputation)
        .filter(DbWalletReputation.adress == id.lower())
        .first()
    )
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet with adress {id} not found",
        )
    return wallet
