from db.database import SessionLocal
from db.models import DbWalletReputation, DbNcTransaction
from datetime import datetime
from collections import namedtuple
import requests
from bs4 import BeautifulSoup
from typing import List

# Create namedtuple
PaperHand = namedtuple("PaperHand", "result paper_hand quantity")
LP = namedtuple("LP", "balance add_lp_list added add_lp remove_lp")
YF = namedtuple("YF", "balance yf_plus yf_minus added")


# Open db session for generator function
session = SessionLocal()


# Generator to optimize code
def select_time_in_nc_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.to == address.lower())
        .all()
    ):
        yield row


def paper_hand_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.From == address)
        .filter(DbNcTransaction.method == "Sales of NC coins")
        .all()
    ):
        yield row


def lp_balance_plus_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.to == address)
        .filter(DbNcTransaction.method == "Add Liquidity")
        .all()
    ):
        yield row


def lp_balance_minus_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.From == address)
        .filter(DbNcTransaction.method == "Remove Liquidity")
        .all()
    ):
        yield row


def claim_balance_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.to == address)
        .filter(DbNcTransaction.method == "Claim")
        .all()
    ):
        yield row


def yf_balance_plus_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.From == address)
        .filter(DbNcTransaction.method == "Stake")
        .all()
    ):
        yield row


def yf_balance_minus_generator(address: str):
    for row in (
        session.query(DbNcTransaction)
        .filter(DbNcTransaction.to == address)
        .filter(DbNcTransaction.method == "Unstake")
        .all()
    ):
        yield row


def all_addresses_generator():
    for row in session.query(DbNcTransaction).all():
        yield row.to


class WalletReputation:
    """
    Class responsible for creating, updating and adding wallet reputation to the database.
    """

    def __init__(self, addresses_list: List[str]):
        self.session = SessionLocal()
        self.addresses_list = addresses_list

    def paper_hand(self, address: str):
        # Check if address whenever has sold NC -> create list with txn hash
        paper_hand = [row.txn_hash for row in paper_hand_generator(address)]

        # Check how many NC wallet sold
        quantity = [row.quantity for row in paper_hand_generator(address)]
        quantity = round(sum(quantity), 5)

        # Join txn hash list to str seperate with comma
        result = ",".join(paper_hand)
        paper_hand = bool(result)
        return PaperHand(result, paper_hand, quantity)

    def lp_balance(self, address: str):
        # List with number of added LPs
        add_lp_list = [row.quantity for row in lp_balance_plus_generator(address)]

        # List with number of removed LP
        remove_lp_list = [row.quantity for row in lp_balance_minus_generator(address)]
        # Rounding value
        add_lp = round(sum(add_lp_list), 5)
        remove_lp = round(sum(remove_lp_list), 5)

        # Check if wallet ad LP - boolen value
        added = bool(add_lp_list)

        # Final LP balance
        balance = add_lp - remove_lp
        return LP(round(balance, 2), len(add_lp_list), added, add_lp, remove_lp)

    def nc_balance(self, address: str):
        # Generate wallet address URL and request for html content
        BASE_URL = "https://polygonscan.com/token/0x64a795562b02830ea4e43992e761c96d208fc58d?a="
        page_html = requests.get(url=BASE_URL + address).content

        # Make soup
        soup = BeautifulSoup(page_html, "html.parser")
        print(BASE_URL + address)

        # Retrive NC Balance value
        nc_balance = (
            soup.find("div", id="ContentPlaceHolder1_divFilteredHolderBalance")
            .text.split()[1]
            .replace(",", "")
        )

        # Change type and round value
        nc_balance = round(float(nc_balance.replace(",", "")), 2)

        return nc_balance

    def time_in_nc(self, address: str):
        # Create list with transactions date
        dates = [row.datetime for row in select_time_in_nc_generator(address)]

        # Check which transaction has the oldest date
        nc_oldest_date = min(dates).strftime("%Y-%m-%d")
        today = datetime.today().strftime("%Y-%m-%d")

        # Calculate how long wallet has NC
        how_long_nc = self.days_between(today, nc_oldest_date)

        return how_long_nc

    def claim_balance(self, address: str):
        # Create list with quantity of claim transactions
        claim_action = [row.quantity for row in claim_balance_generator(address)]

        # Rounding value
        claim_action = round(sum(claim_action), 5)
        return claim_action

    def yf_balance(self, address: str):
        plus_trans = round(
            sum([row.quantity for row in yf_balance_plus_generator(address)]), 5
        )
        minus_trans = round(
            sum([row.quantity for row in yf_balance_minus_generator(address)]), 5
        )
        yf_balance = plus_trans - minus_trans
        add_to_yf = bool(plus_trans)
        return YF(yf_balance, plus_trans, minus_trans, add_to_yf)

    def rank(self, address: str):
        paper_hands = self.paper_hand(address).paper_hand
        add_to_yf = self.yf_balance(address).added
        have_lp = self.lp_balance(address).balance
        how_much_sell = self.paper_hand(address).quantity

        # Wallet rank conditions
        condition_DH = not paper_hands and add_to_yf and have_lp > 0
        condition_DH2 = (
            paper_hands and add_to_yf and have_lp > 0 and how_much_sell <= 50000
        )
        condition_DH2a = (
            paper_hands and add_to_yf and have_lp > 0 and how_much_sell > 50000
        )
        condition_DH3 = not paper_hands and have_lp > 0
        condition_DH4 = paper_hands and have_lp > 0 and how_much_sell <= 50000
        condition_DH4a = paper_hands and have_lp > 0 and how_much_sell > 50000

        wallet_rank = "Diamond Hands5"

        if condition_DH:
            wallet_rank = "Diamond Hands"
        elif condition_DH2:
            wallet_rank = "Diamond Hands2"
        elif condition_DH2a:
            wallet_rank = "Diamond Hands2a"
        elif condition_DH3:
            wallet_rank = "Diamond Hands3"
        elif condition_DH4:
            wallet_rank = "Diamond Hands4"
        elif condition_DH4a:
            wallet_rank = "Diamond Hands4a"

        return wallet_rank

    def add_single_reputation_to_db(self, address: str):
        # Check if address exists
        query = self.session.query(DbNcTransaction).filter(
            DbNcTransaction.to == address
        )
        if not self.session.query(query.exists()).scalar():
            return {"Message": "Addres not exist"}

        # Prepare model for new wallet
        new_wallet = DbWalletReputation(
            adress=address,
            time_in_nc=self.time_in_nc(address),
            paper_hands=self.paper_hand(address).paper_hand,
            proofs=self.paper_hand(address).result,
            did_wallet_add_lp=self.lp_balance(address).added,
            how_many_time_add_lp=self.lp_balance(address).add_lp_list,
            lp_balance=self.lp_balance(address).balance,
            nc_balance=self.nc_balance(address),
            claim_balance=self.claim_balance(address),
            add_to_yf=self.yf_balance(address).added,
            wallet_rank=self.rank(address),
        )

        # Check if wallet is already in db
        query = self.session.query(DbWalletReputation).filter(
            DbWalletReputation.adress == address
        )

        # If no, generate new wallet
        if not self.session.query(query.exists()).scalar():
            try:
                self.session.add(new_wallet)
                self.session.commit()
                self.session.refresh(new_wallet)
            except Exception as e:
                print(f"Add new: {e}")
        # Update wallet
        else:
            try:
                self.session.merge(new_wallet)
                self.session.commit()
                self.session.close()
            except Exception as e:
                print(f"Update: {e}")

    def add_all_reputation_to_db(self):
        for address in self.addresses_list:
            # Check if address exists
            address = address.lower()
            query = self.session.query(DbNcTransaction).filter(
                DbNcTransaction.to == address
            )
            if not self.session.query(query.exists()).scalar():
                return {"Message": "Addres not exist"}

            # Prepare model for new wallet
            wallet = DbWalletReputation(
                adress=address,
                time_in_nc=self.time_in_nc(address),
                paper_hands=self.paper_hand(address).paper_hand,
                proofs=self.paper_hand(address).result,
                did_wallet_add_lp=self.lp_balance(address).added,
                how_many_time_add_lp=self.lp_balance(address).add_lp_list,
                lp_balance=self.lp_balance(address).balance,
                nc_balance=self.nc_balance(address),
                claim_balance=self.claim_balance(address),
                add_to_yf=self.yf_balance(address).added,
                wallet_rank=self.rank(address),
            )

            # Check if wallet is already in db
            query = self.session.query(DbWalletReputation).filter(
                DbWalletReputation.adress == address
            )

            # If no, generate new wallet
            if not self.session.query(query.exists()).scalar():
                try:
                    self.session.add(wallet)
                    self.session.commit()
                    self.session.refresh(wallet)
                except Exception as e:
                    print(f"Add new: {e}")
            # Update wallet
            else:
                try:
                    self.session.merge(wallet)
                    self.session.commit()
                    self.session.close()
                except Exception as e:
                    print(f"Update: {e}")

    @staticmethod
    def days_between(d1, d2) -> int:
        """

        :param d1: datatime format
        :param d2: datatime format
        :return: integer value
        """
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)
