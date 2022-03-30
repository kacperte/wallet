from db.database import SessionLocal
from db.models import DbWalletReputation, DbNcTransaction
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
from collections import namedtuple

# Open db session for generator function
session = SessionLocal()

# Create namedtuple
PaperHand = namedtuple("PaperHand", "result paper_hand quantity")
LP = namedtuple("LP", "balance add_lp_list added add_lp remove_lp")
YF = namedtuple("YF", "balance yf_plus yf_minus added")


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
    Class responsible for creating, updating and adding to the wallet reputation database.
    """

    def __init__(self, address: str):
        """
        :param address: wallet address
        """
        self.address = address.lower()
        self.session = SessionLocal()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--remote-debugging-port=9222")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        prefs = {
            "download_restrictions": 3,
        }
        options.add_experimental_option("prefs", prefs)
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        self.driver = webdriver.Chrome(
            executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options
        )

    def paper_hand(self):
        # Check if address whenever has sold NC -> create list with txn hash
        paper_hand = [row.txn_hash for row in paper_hand_generator(self.address)]

        # Check how many NC wallet sold
        quantity = [row.quantity for row in paper_hand_generator(self.address)]
        quantity = round(sum(quantity), 5)

        # Join txn hash list to str seperate with comma
        result = ",".join(paper_hand)
        paper_hand = bool(result)
        return PaperHand(result, paper_hand, quantity)

    def lp_balance(self):
        # List with number of added LPs
        add_lp_list = [row.quantity for row in lp_balance_plus_generator(self.address)]

        # List with number of removed LP
        remove_lp_list = [
            row.quantity for row in lp_balance_minus_generator(self.address)
        ]
        # Rounding value
        add_lp = round(sum(add_lp_list), 5)
        remove_lp = round(sum(remove_lp_list), 5)

        # Check if wallet ad LP - boolen value
        added = bool(add_lp_list)

        # Final LP balance
        balance = add_lp - remove_lp
        return LP(round(balance, 2), len(add_lp_list), added, add_lp, remove_lp)

    def nc_balance(self):
        # Generate wallet address URL
        base_url = "https://polygonscan.com/token/0x64a795562b02830ea4e43992e761c96d208fc58d?a="
        self.driver.get(base_url + self.address)

        # Scrap NC balance info
        nc_balance = (
            WebDriverWait(self.driver, 20)
            .until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#ContentPlaceHolder1_divFilteredHolderBalance")
                )
            )
            .text
        )
        self.driver.close()

        # Clean value to final form
        nc_balance = nc_balance.split()[1]
        nc_balance = round(float(nc_balance.replace(",", "")), 2)

        return nc_balance

    def time_in_nc(self):
        # Create list with transactions date
        dates = [row.datetime for row in select_time_in_nc_generator(self.address)]

        # Check which transaction has the oldest date
        nc_oldest_date = min(dates).strftime("%Y-%m-%d")
        today = datetime.today().strftime("%Y-%m-%d")

        # Calculate how long wallet has NC
        how_long_nc = self.days_between(today, nc_oldest_date)

        return how_long_nc

    def claim_balance(self):
        # Create list with quantity of claim transactions
        claim_action = [row.quantity for row in claim_balance_generator(self.address)]

        # Rounding value
        claim_action = round(sum(claim_action), 5)
        return claim_action

    def yf_balance(self):
        plus_trans = round(
            sum([row.quantity for row in yf_balance_plus_generator(self.address)]), 5
        )
        minus_trans = round(
            sum([row.quantity for row in yf_balance_minus_generator(self.address)]), 5
        )
        yf_balance = plus_trans - minus_trans
        add_to_yf = bool(plus_trans)
        return YF(yf_balance, plus_trans, minus_trans, add_to_yf)

    def rank(self):
        paper_hands = self.paper_hand().paper_hand
        add_to_yf = self.yf_balance().added
        have_lp = self.lp_balance().balance
        how_much_sell = self.paper_hand().quantity

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

    def add_reputation_to_db(self):
        # Check if address exists
        query = self.session.query(DbNcTransaction).filter(
            DbNcTransaction.to == self.address
        )
        if not self.session.query(query.exists()).scalar():
            return {"Message": "Addres not exist"}

        # Prepare model for new wallet
        new_wallet = DbWalletReputation(
            adress=self.address,
            time_in_nc=self.time_in_nc(),
            paper_hands=self.paper_hand().paper_hand,
            proofs=self.paper_hand().result,
            did_wallet_add_lp=self.lp_balance().added,
            how_many_time_add_lp=self.lp_balance().add_lp_list,
            lp_balance=self.lp_balance().balance,
            nc_balance=self.nc_balance(),
            claim_balance=self.claim_balance(),
            add_to_yf=self.yf_balance().added,
            wallet_rank=self.rank(),
        )

        # Check if wallet is already in db
        query = self.session.query(DbWalletReputation).filter(
            DbWalletReputation.adress == self.address
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
            except Exception as e:
                print(f"Update: {e}")

        self.session.close

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
