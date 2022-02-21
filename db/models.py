from db.database import Base
from sqlalchemy import Column, Integer, String, Boolean, Date, BigInteger


class DbNcTransaction(Base):
    __tablename__ = "ncTransaction"

    id = Column(String, primary_key=True, index=True)
    txn_hash = Column(String)
    method = Column(String)
    datetime = Column(Date)
    From = Column(String)
    to = Column(String)
    quantity = Column(String)


class DbWalletReputation(Base):
    __tablename__ = "walletReputation"

    adress = Column(String, primary_key=True, index=True)
    time_in_nc = Column(Integer)
    paper_hands = Column(Boolean)
    proofs = Column(String)
    did_wallet_add_lp = Column(Boolean)
    how_many_time_add_lp = Column(Integer)
    lp_balance = Column(Integer)
    nc_balance = Column(Integer)
