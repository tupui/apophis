from unittest import mock

import pytest

from apophis import Apophis
from apophis.binance import BinanceAPI


def test_client():
    with Apophis() as client:
        # unknown method
        with pytest.raises(ValueError):
            client.query(method="toto")

        # trying to access private method
        with pytest.raises(ConnectionError):
            client.query(method="Balance")

        # known method but wrong url. accounts from Future only
        with pytest.raises(ConnectionError):
            client.query(method="tickers")

    with Apophis(future=True) as client_future:
        client_future.query(method="tickers")


def test_response():
    with Apophis() as client:
        response = client.query("Ticker", {"pair": "XXRPZEUR"})

        assert isinstance(response, dict)
        print(response["result"])
        assert 0 < float(response["result"]["XXRPZEUR"]["c"][0]) < 100


def test_binance_signing():
    """Example from Binance API's doc."""
    api_key = "vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0Mu" "IgwCIPy6utIco14y7Ju91duEh8A"
    api_secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZj" "InClVN65XAbvqqM6A7H5fATj0j"
    with BinanceAPI(key=api_key, secret=api_secret) as client:
        data = {
            "symbol": "LTCBTC",
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": 1,
            "price": 0.1,
        }

        with mock.patch("time.time", return_value=1499827319.559):
            data, header = client._sign_message(data)

        assert data["signature"] == (
            "c8db56825ae71d6d79447849e617115f4a920f" "a2acdcab2b053c4b2838bd6b71"
        )
