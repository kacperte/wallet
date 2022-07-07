import requests
import time


def run_endpoints():
    requests.post("https://wallet-reputation.herokuapp.com/scraper/run-nc")
    requests.post("https://wallet-reputation.herokuapp.com/scraper/run-lp")
    time.sleep(180)
    requests.post("https://wallet-reputation.herokuapp.com/wallet/run")


if __name__ == "__main__":
    run_endpoints()
    print("Process complete")
