from pydantic import BaseModel


class WalletBase(BaseModel):
    adress: str = None
    time_in_nc: int = None
    paper_hands: bool = False
    proofs: str = None
    did_wallet_add_lp: bool = False
    how_many_time_add_lp: int = None
    lp_balance: int = None
    nc_balance: int = None
    claim_balance: int = None
    add_to_yf: bool = False

    class Config:
        orm_mode = True
