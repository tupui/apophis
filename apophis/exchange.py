import time

from abc import ABC, abstractmethod
from typing import Tuple

from .apophis import Apophis


class Exchange(ABC):
    """A generic Exchange class meant for subclassing.

    Exchange is a base class to construct specific exchange.
    It cannot be used directly.

    Parameters
    ----------
    key : str, optional
        Public key identifier for queries to the API.
    secret : str, optional
        Private key used to sign messages.
    future : bool
        Use "Kraken Future" instead of "Kraken".
    live : bool
        Go live for orders.

    Notes
    -----
    Instances of the class can access the attributes: ``fee`` for
    the total fee incurred by the buys and sells of the session ; ``n_buy``
    for the number of buys ; and ``n_sell`` for the number of sells.

    **Subclassing**

    When subclassing `Exchange` to create a new exchange,  ``__init__``m
    ``market_price``, ``_fee`` and ``_order`` must be redefined.

    * ``__init__(key, secret, future=False, live=False)``: at least these
      arguments should be passed to the constructor.
    * ``market_price(pair)``: Get the market price for a pair.
    * ``_fee()``: Returns maker and taker fees.
    * ``_order(pair, coins, price, side)``: Place an order with ``side`` one of
      ``sell``, ``buy``.

    Optionally, 2 other methods can be overwritten by subclasses:

    * ``buy``: Buy logic. Calls the underlying ``_order``.
    * ``sell``: Sell logic. Calls the underlying ``_order``.

    """

    @abstractmethod
    def __init__(
        self,
        key: str = None,
        secret: str = None,
        future: bool = False,
        live: bool = False,
    ):
        self.api = Apophis(key=key, secret=secret, future=future)
        self.live = live

        self.fee_maker, self.fee_taker = self._fees()
        self.fee = 0
        self.n_buy = 0
        self.n_sell = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Close the session."""
        self.api.session.close()

    @abstractmethod
    def market_price(self, pair: str) -> float:
        """Market price.

        Parameters
        ----------
        pair : str
            Pair of coins to get the price of.

        Returns
        -------
        price : float
            Exchange price of the pair.

        """

    @abstractmethod
    def _fees(self) -> Tuple[float, float]:
        """Cost of a transaction.

        Returns
        -------
        maker_fee : float
            Maker fee (sell).
        taker_fee : float
            Taker fee (buy).

        """

    @abstractmethod
    def _order(
        self, pair: str, volume: float, price: float, side: str
    ) -> Tuple[bool, float]:
        """Place an order.

        The function blocks until the order is completed.

        Parameters
        ----------
        pair : str
            Pair to trade.
        volume : float
            Volume of the pair to trade.
        price : float
            Limit price of the pair.
        side : str
            Can be ``buy`` or ``sell``.

        Returns
        -------
        order : bool
            True if the transaction succeeded.
        fee : float
            Cost of the transaction.

        """

    def buy(self, pair: str, volume: float, price: float) -> bool:
        """Buy order.

        Parameters
        ----------
        pair : str
            Pair to trade.
        volume : float
            Number of coins to buy.
        price : float
            Limit price of the pair.

        Returns
        -------
        processed : bool
            True if the transaction succeeded.

        """
        print(f"Buying {volume} {pair} at {price} -> {volume * price}€")
        if self.live:
            processed, fee = self._order(
                pair=pair, volume=volume, price=price, side="buy"
            )
        else:
            fee = volume * price * self.fee_taker
            processed = True

        if processed:
            self.fee += fee
            self.n_buy += 1

        return processed

    def sell(self, pair: str, volume: float, price: float) -> float:
        """

        Parameters
        ----------
        pair : str
            Pair to trade.
        volume : float
            Number of coins to sell.
        price : float
            Limit price of the pair.

        Returns
        -------
        processed : bool
            True if the transaction succeeded.

        """
        print(f"Selling {volume} {pair} at {price} -> {volume * price}€")
        if self.live:
            processed, fee = self._order(
                pair=pair, volume=volume, price=price, side="sell"
            )
        else:
            processed = True
            fee = volume * price * self.fee_maker

        if processed:
            self.fee += fee
            self.n_sell += 1

        return processed


class Kraken(Exchange):
    """Exchange for Kraken."""

    def __init__(self, key: str = None, secret: str = None, live: bool = False):
        super().__init__(key=key, secret=secret, live=live, future=False)

    def market_price(self, pair: str) -> float:
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

    def _order(self, pair: str, volume: float, price: float, side: str):
        payload = {
            "pair": pair,
            "type": side,
            "ordertype": "limit",
            "price": str(price),
            "volume": str(volume),
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
    """Exchange for Kraken Future."""

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

    def _order(self, pair: str, volume: float, price: float, side: str):
        payload = {
            "orderType": "lmt",
            "symbol": pair,
            "side": side,
            "limitPrice": price,
            "size": volume,
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
                fee = volume * price * self.fee_taker
            else:
                fee = volume * price * self.fee_maker

            return True, fee
