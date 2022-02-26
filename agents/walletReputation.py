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

session = SessionLocal()

PaperHand = namedtuple("PaperHand", "result paper_hand")
LP = namedtuple("LP", "balance add_lp_list added add_lp remove_lp")


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


class WalletReputation:
    def __init__(self, address: str):
        self.address = address.lower()
        self.session = SessionLocal()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
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
        paper_hand = [row.txn_hash for row in paper_hand_generator(self.address)]
        result = ",".join(paper_hand)
        paper_hand = bool(result)
        return PaperHand(result, paper_hand)

    def lp_balance(self):
        add_lp_list = [row.quantity for row in lp_balance_plus_generator(self.address)]
        remove_lp_list = [
            row.quantity for row in lp_balance_minus_generator(self.address)
        ]
        add_lp = round(sum(add_lp_list), 5)
        remove_lp = round(sum(remove_lp_list), 5)
        added = bool(add_lp_list)
        balance = add_lp - remove_lp

        return LP(round(balance, 2), len(add_lp_list), added, add_lp, remove_lp)

    def nc_balance(self):
        base_url = "https://polygonscan.com/token/0x64a795562b02830ea4e43992e761c96d208fc58d?a="
        self.driver.get(base_url + self.address)

        nc_balance = (
            WebDriverWait(self.driver, 20)
            .until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#ContentPlaceHolder1_divFilteredHolderBalance")
                )
            )
            .text
        )

        nc_balance = nc_balance.split()[1]
        nc_balance = round(float(nc_balance.replace(",", "")), 2)

        return nc_balance

    def time_in_nc(self):
        dates = [row.datetime for row in select_time_in_nc_generator(self.address)]
        nc_oldest_date = min(dates).strftime("%Y-%m-%d")
        today = datetime.today().strftime("%Y-%m-%d")
        how_long_nc = self.days_between(today, nc_oldest_date)

        return how_long_nc

    def add_reputation_to_db(self):
        q = self.session.query(DbNcTransaction).filter(
            DbNcTransaction.to == self.address
        )
        if not self.session.query(q.exists()).scalar():
            return {"Message": "Addres not exist"}

        new_wallet = DbWalletReputation(
            address=self.address,
            time_in_nc=self.time_in_nc(),
            paper_hands=self.paper_hand().paper_hand,
            proofs=self.paper_hand().result,
            did_wallet_add_lp=self.lp_balance().added,
            how_many_time_add_lp=self.lp_balance().add_lp_list,
            lp_balance=self.lp_balance().balance,
            nc_balance=self.nc_balance(),
        )

        q = self.session.query(DbWalletReputation).filter(
            DbWalletReputation.address == self.address
        )
        if not self.session.query(q.exists()).scalar():
            try:
                self.session.add(new_wallet)
                self.session.commit()
                self.session.refresh(new_wallet)
            except Exception as e:
                print(f"Add new: {e}")
        else:
            try:
                self.session.merge(new_wallet)
                self.session.commit()
            except Exception as e:
                print(f"Update: {e}")

        self.session.close

        return {"Message": "Success"}

    @staticmethod
    def days_between(d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)
