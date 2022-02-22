from db.database import SessionLocal
from db.models import DbWalletReputation, DbNcTransaction
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

session = SessionLocal()


class WalletReputation:
    def __init__(self, adress: str):
        self.adress = adress.lower()
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
        paper_hand = []
        for row in (
            session.query(DbNcTransaction)
            .filter(DbNcTransaction.From == self.adress)
            .filter(DbNcTransaction.method == "Sales of NC coins")
            .all()
        ):
            paper_hand.append(row.txn_hash)

        paper_hand = ",".join(paper_hand)
        result = True if len(paper_hand) > 0 else False
        return result, paper_hand

    def lp_balance(self):
        add_lp_list = []
        remove_lp_list = []
        for row in (
            session.query(DbNcTransaction)
            .filter(DbNcTransaction.to == self.adress)
            .filter(DbNcTransaction.method == "Add Liquidity")
            .all()
        ):
            add_lp_list.append(row.quantity)

        for row in (
            session.query(DbNcTransaction)
            .filter(DbNcTransaction.From == self.adress)
            .filter(DbNcTransaction.method == "Remove Liquidity")
            .all()
        ):
            remove_lp_list.append(row.quantity)

        add_lp = round(sum(add_lp_list), 5)
        remove_lp = round(sum(remove_lp_list), 5)
        added = True if len(add_lp_list) > 0 else False
        balance = add_lp - remove_lp

        return round(balance, 2), len(add_lp_list), added, add_lp, remove_lp

    def nc_balance(self):
        base_url = "https://polygonscan.com/token/0x64a795562b02830ea4e43992e761c96d208fc58d?a="
        self.driver.get(base_url + self.adress)

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
        dates = []
        for row in (
            session.query(DbNcTransaction)
            .filter(DbNcTransaction.to == self.adress)
            .all()
        ):
            dates.append(row.datetime)
        nc_oldest_date = min(dates).strftime("%Y-%m-%d")
        today = datetime.today().strftime("%Y-%m-%d")
        how_long_nc = self.days_between(today, nc_oldest_date)

        return how_long_nc

    def add_reputation_to_db(self):
        q = self.session.query(DbNcTransaction).filter(
            DbNcTransaction.to == self.adress
        )
        if not self.session.query(q.exists()).scalar():
            return {"Message": "Addres not exist"}
        result = {
            "adress": self.adress,
            "time_in_nc": self.time_in_nc(),
            "paper_hands": self.paper_hand()[0],
            "proofs": self.paper_hand()[1],
            "did_wallet_add_lp": self.lp_balance()[2],
            "how_may_time_add_lp": self.lp_balance()[1],
            "lp_balance": self.lp_balance()[0],
            "nc_balance": self.nc_balance(),
        }

        new_wallet = DbWalletReputation(
            adress=result["adress"],
            time_in_nc=result["time_in_nc"],
            paper_hands=result["paper_hands"],
            proofs=result["proofs"],
            did_wallet_add_lp=result["did_wallet_add_lp"],
            how_many_time_add_lp=result["how_may_time_add_lp"],
            lp_balance=result["lp_balance"],
            nc_balance=result["nc_balance"],
        )

        q = self.session.query(DbWalletReputation).filter(
            DbWalletReputation.adress == result["adress"]
        )
        if not self.session.query(q.exists()).scalar():
            try:
                self.session.add(new_wallet)
                self.session.commit()
                self.session.refresh(new_wallet)
            finally:
                self.session.close
        else:
            try:
                self.session.merge(new_wallet)
                self.session.commit()
            finally:
                self.session.close

        return {"Message": "Success"}

    @staticmethod
    def days_between(d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)
