import time

from abc import ABC, abstractmethod
from typing import Tuple

from .apophis import Apophis


class Exchange(ABC):
    @abstractmethod
    def __init__(
        self,
        key: str = None,
        secret: str = None,
        live: bool = False,
        future: bool = False,
    ):
        self.api = Apophis(key=key, secret=secret, future=future)
        self.live = live

        self.fee_maker, self.fee_taker = self._fees()
        self.fee = 0
        self.n_buy = 0
        self.n_sell = 0

    @abstractmethod
    def market_price(self, pair: str) -> float:
        """Market price from Kraken.

        :param pair: Coin's name.
        """

    @abstractmethod
    def _fees(self) -> Tuple[float, float]:
        """"""

    @abstractmethod
    def _order(self, pair: str, coins: float, price: float, type: str):
        """"""

    def buy(self, pair, coins, price):
        print(f"Buying {coins} {pair} at {price} -> {coins * price}€")
        if self.live:
            processed, fee = self._order(
                pair=pair, coins=coins, price=price, type="buy"
            )
        else:
            fee = coins * price * self.fee_taker
            processed = True

        if processed:
            self.fee += fee
            self.n_buy += 1

        return processed

    def sell(self, pair, coins, price):
        print(f"Selling {coins} {pair} at {price} -> {coins * price}€")
        if self.live:
            processed, fee = self._order(
                pair=pair, coins=coins, price=price, type="sell"
            )
        else:
            processed = True
            fee = coins * price * self.fee_maker

        if processed:
            self.fee += fee
            self.n_sell += 1

        return processed


class Kraken(Exchange):
    def __init__(self, key: str = None, secret: str = None, live: bool = False):
        super().__init__(key=key, secret=secret, live=live, future=False)

    def market_price(self, pair: str) -> float:
        """Market price from Kraken.

        :param pair: Coin's name.
        """
        response = self.api.query("Ticker", {"pair": pair})
        price = float(response["result"][pair]["c"][0])

        return price

    def _fees(self) -> Tuple[float, float]:
        try:
            fee_info = self.api.query("TradeVolume", {"pair": "XXRPZEUR"})
            fee_maker = float(fee_info["result"]["fees_maker"]["XXRPZEUR"]["fee"])
            fee_taker = float(fee_info["result"]["fees"]["XXRPZEUR"]["fee"])
        except ConnectionError:
            fee_maker = 0.16
            fee_taker = 0.26

        fee_maker /= 100
        fee_taker /= 100
        return fee_maker, fee_taker

    def _order(self, pair: str, coins: float, price: float, type: str):
        payload = {
            "pair": pair,
            "type": type,
            "ordertype": "limit",
            "price": str(price),
            "volume": str(coins),
            # "validate": True
        }
        response = self.api.query("AddOrder", payload)

        if "txid" not in response["result"]:
            print(f"Cannot place order! -> {response}")
            return False, None
        else:
            txid = response["result"]["txid"][0]

            time.sleep(5)
            response = self.api.query("ClosedOrders")

            while txid not in response["result"]["closed"]:
                print("Order not completed yet!")
                time.sleep(5)
                response = self.api.query("ClosedOrders")

            if type == "buy":
                fee = float(response["result"]["closed"][txid]["fee"])
            else:
                fee = float(response["result"]["closed"][txid]["fee"])

            return True, fee


class KrakenFuture(Exchange):
    def __init__(self, key: str = None, secret: str = None, live: bool = False):
        super().__init__(key=key, secret=secret, live=live, future=True)

    def market_price(self, pair: str) -> float:
        ticks = self.api.query("tickers")
        last = [tick["last"] for tick in ticks["tickers"] if tick["symbol"] == pair][0]
        return last

    def _fees(self) -> Tuple[float, float]:
        fee_maker = 0.02 / 100
        fee_taker = 0.05 / 100

        return fee_maker, fee_taker

    def _order(self, pair: str, coins: float, price: float, type: str):
        payload = {
            "orderType": "lmt",
            "symbol": pair,
            "side": type,
            "limitPrice": price,
            "size": coins,
        }
        response = self.api.query("sendorder", payload)

        status = response["sendStatus"]["status"]

        if status != "placed":
            print(f"Cannot place order! -> {status}")
            return False, None
        else:
            txid = response["sendStatus"]["order_id"]

            time.sleep(5)
            response = self.api.query("fills")
            not_done = not any(
                [event["order_id"] == txid for event in response["fills"]]
            )

            while not_done:
                print("Order not completed yet!")
                time.sleep(5)
                response = self.api.query("fills")
                not_done = not any(
                    [event["order_id"] == txid for event in response["fills"]]
                )

            if type == "buy":
                fee = coins * price * self.fee_taker
            else:
                fee = coins * price * self.fee_maker

            return True, fee
