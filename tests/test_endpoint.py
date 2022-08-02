import unittest
import requests


class TestEndpoint(unittest.TestCase):
    def setUp(self) -> None:
        self.scrap_nc_endpoint_url = (
            "https://wallet-reputation.herokuapp.com/scraper/run-nc"
        )
        self.scrap_lp_endpoint_url = (
            "https://wallet-reputation.herokuapp.com/scraper/run-lp"
        )
        self.run_wallet_reputation_url = (
            "https://wallet-reputation.herokuapp.com/wallet/run"
        )
        self.correct_id = "0xa792287a25b7af46e2507a875e4f554083f677ce"
        self.incorrect_id = "aa"
        self.get_wallet_info_url = (
            f"https://wallet-reputation.herokuapp.com/wallet/wallet/"
        )
        self.get_transaction_info_url = (
            f"https://wallet-reputation.herokuapp.com/wallet/transactions/"
        )

    def test_scrap_nc_endpoint_200(self):
        response = requests.post(self.scrap_nc_endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_scrap_lp_endpoint_200(self):
        response = requests.post(self.scrap_lp_endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_run_wallet_reputation_endpoint_200(self):
        response = requests.post(self.run_wallet_reputation_url)
        self.assertEqual(response.status_code, 200)

    def test_get_wallet_info_endpoint_200(self):
        response = requests.get(self.get_wallet_info_url + self.correct_id)
        self.assertEqual(response.status_code, 200)

    def test_get_transaction_info_url_200(self):
        response = requests.get(self.get_transaction_info_url + self.correct_id)
        self.assertEqual(response.status_code, 200)

    def test_get_wallet_info_endpoint_404(self):
        response = requests.get(self.get_wallet_info_url + self.incorrect_id)
        self.assertEqual(response.status_code, 404)

    def test_get_transaction_info_url_404(self):
        response = requests.get(self.get_transaction_info_url + self.incorrect_id)
        self.assertEqual(response.status_code, 404)
