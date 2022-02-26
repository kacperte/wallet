from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import math
import random
import numpy as np
from db.database import SessionLocal
from db.models import DbNcTransaction
import os
from sqlalchemy import and_


class PolygonscanScraper:
    """
    Class to scrap data from https://polygonscan.com/, clean and save in database
    """

    def __init__(self):
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
        self.session = SessionLocal()

    def scrap_from_url(self, url):
        # Connect to url
        self.driver.get(url)

        # Cookies
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#btnCookie"))
        ).click()

        # Locate number of total transfer to check how many pages have table
        num_trans = self.driver.find_element(By.XPATH, '//*[@id="totaltxns"]').text
        num_trans = int(num_trans)
        num = math.ceil(num_trans / 25)

        # Switch to frame with NC transaction table
        WebDriverWait(self.driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, "iframe#tokentxnsiframe")
            )
        )

        # Switch DateTime format in table
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#lnkTokenTxnsAgeDateTime"))
        ).click()

        # Loop through a table
        for _ in range(num):
            # Select info from table
            data = (
                WebDriverWait(self.driver, 20)
                .until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "table.table.table-md-text-normal")
                    )
                )
                .get_attribute("outerHTML")
            )

            # Open as dataframe
            df = pd.read_html(data)[0]

            # Click to next page
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="maindiv"]/div[1]/nav/ul/li[4]')
                )
            ).click()

            # Clean dataframe
            cleaned_df = self.clean_data(data_to_clean=df)

            # Add to database
            self.add_to_db(cleaned_df)

    def add_to_db(self, df):
        # iterating through dataframe
        for row in df.values:
            # prepering new DbNcTransaction before adding to database
            new_trans = DbNcTransaction(
                txn_hash=row[0],
                method=row[1],
                datetime=row[2],
                From=row[3],
                to=row[4],
                quantity=row[5],
                id=row[6],
            )

            # check if row already exists -> return True or False
            exists = self.session.query(
                self.session.query(DbNcTransaction)
                .filter(
                    and_(
                        DbNcTransaction.txn_hash == row[0],
                        DbNcTransaction.method == row[1],
                        DbNcTransaction.datetime == row[2],
                        DbNcTransaction.From == row[3],
                        DbNcTransaction.to == row[4],
                        DbNcTransaction.quantity == row[5],
                    )
                )
                .exists()
            ).scalar()

            if not exists:
                try:
                    self.session.add(new_trans)
                    self.session.commit()
                    self.session.refresh(new_trans)
                finally:
                    self.session.close()

    @staticmethod
    def clean_data(data_to_clean):
        # Rename values from Method column to 'Purchase of NC coins'
        con_1 = (data_to_clean.Method == "Swap Exact Token...") & (
            data_to_clean.From == "0x78e16d2facb80ac536887d1376acd4eeedf2fa08"
        )
        con_2 = data_to_clean.Method == "Swap"
        con_3 = data_to_clean.Method == "Swap ETH For Exa..."
        con_4 = data_to_clean.Method == "Swap Exact ETH F..."
        con_5 = data_to_clean.Method == "0x415565b0"
        data_to_clean.loc[
            con_1 | con_2 | con_3 | con_4 | con_5, "Method"
        ] = "Purchase of NC coins"

        # Rename values from Method column to 'Sales of NC coins'
        con_1 = (data_to_clean.Method == "Swap Exact Token...") & (
            data_to_clean.From != "0x78e16d2facb80ac536887d1376acd4eeedf2fa08"
        )
        con_2 = data_to_clean.Method == "0x0773b509"
        data_to_clean.loc[con_1 | con_2, "Method"] = "Sales of NC coins"

        # Rename 'Add Liquidity ET...' to 'Add Liquidity'
        con_1 = data_to_clean.Method == "Add Liquidity ET..."
        data_to_clean.loc[con_1, "Method"] = "Add Liquidity"

        # Rename 'Remove Liquidity...' to 'Remove Liquidity'
        con_1 = data_to_clean.Method == "Remove Liquidity..."
        data_to_clean.loc[con_1, "Method"] = "Remove Liquidity"

        # Remove useless value form Method column
        value_to_remove = data_to_clean.loc[
            (data_to_clean.Method == "0xf574133c")
            | (data_to_clean.Method == "0x6d9cec22")
            | (data_to_clean.To == "QuickSwap: Router")
            | (data_to_clean.To == "Null Address: 0x000...dEaD")
            | (data_to_clean.To == "Paraswap v5: Augustus Swapper")
            | (data_to_clean.From == "QuickSwap: Router")
            | (data_to_clean.From == "Paraswap v5: Augustus Swapper")
        ].index
        data_to_clean = data_to_clean.drop(value_to_remove, axis=0)

        # Remove useless columns
        data_to_clean = data_to_clean.drop(["Unnamed: 4", "Unnamed: 7"], axis=1)

        # Format to date type
        data_to_clean = data_to_clean.rename(columns={"Date Time (UTC)": "Datetime"})
        data_to_clean["Datetime"] = pd.to_datetime(data_to_clean["Datetime"])

        # Set up unique id column
        data_to_clean["Id"] = np.arange(1, len(data_to_clean) + 1, 1)
        data_to_clean["Id"] = data_to_clean["Id"].apply(
            lambda x: x + random.randint(0, 99999999999)
        )

        return data_to_clean
