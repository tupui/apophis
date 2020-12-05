"""Kraken.com cryptocurrency Exchange API."""
import base64
import hashlib
import hmac
import time
import urllib.parse

from typing import Dict, Optional

import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


version = "1.0"

API_PUBLIC = {
    "Time",
    "Assets",
    "AssetPairs",
    "Ticker",
    "OHLC",
    "Depth",
    "Trades",
    "Spread",
    # Futures
    "instruments",
    "tickers",
    "orderbook",
    "history",
}
API_PRIVATE_GET = {
    # Futures
    "accounts",
    "openorders",
    "fills",
    "openpositions",
    "transfers",
    "notifications",
    "historicorders",
    "recentorders",
}
API_PRIVATE_POST = {
    "Balance",
    "BalanceEx",
    "TradeBalance",
    "OpenOrders",
    "ClosedOrders",
    "QueryOrders",
    "TradesHistory",
    "QueryTrades",
    "OpenPositions",
    "Ledgers",
    "QueryLedgers",
    "TradeVolume",
    "AddExport",
    "ExportStatus",
    "RetrieveExport",
    "RemoveExport",
    "GetWebSocketsToken",
    "AddOrder",
    "CancelOrder",
    "CancelAll",
    # Futures
    "transfer",
    "sendorder",
    "cancelorder",
    "cancelallorders",
    "cancelallordersafter",
    "batchorder",
    "withdrawal",
}
API_METHODS = API_PUBLIC | API_PRIVATE_GET | API_PRIVATE_POST


class Apophis:
    """Interact with Kraken's API.

    Without specifying key/secret pair, only public queries can be performed.

    Parameters
    ----------
    key : str, optional
        Public key identifier for queries to the API.
    secret : str, optional
        Private key used to sign messages.
    future : bool
        Use "Kraken Future" instead of "Kraken".

    """

    def __init__(
        self,
        key: Optional[str] = None,
        secret: Optional[str] = None,
        future: bool = False,
    ):
        # API keys
        self.api_key = key
        self.api_secret = secret

        self.future = future
        if self.future:
            self.uri = "https://futures.kraken.com/derivatives"
            self.apiversion = "/api/v3/"
        else:
            self.uri = "https://api.kraken.com"
            self.apiversion = "/0/"

        # Session
        self.session = requests.Session()
        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=False,  # noqa
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({"User-Agent": "Apophis/" + version})

        self.timeout = 10
        self.response = None
        self._json_options = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Close the session."""
        self.session.close()

    def _query(self, method: str, data: Dict, endpoint: str, headers: Dict) -> Dict:
        """Low-level query handling.

        Parameters
        ----------
        method : str
            Method.
        data : dict
            API request parameters.
        endpoint : str
            API URL path sans host.
        headers: dict, optional
            HTTPS headers.

        Returns
        -------
        response : dict
          Deserialized response.

        """
        url = self.uri + endpoint

        if method in API_PRIVATE_GET or method in API_PUBLIC:
            session_call = self.session.get
            params = {"params": data, "headers": headers}
        elif method in API_PRIVATE_POST:
            session_call = self.session.post
            params = {"data": data, "headers": headers}
        else:
            raise KeyError(f"Invalid method {method}")

        # Retry strategy: 4 times if API issue (ex. rate limit) with increasing
        # sleep to lower counter down. Last is 4 to be able to do a +2 ops.
        api_call = 0
        sleeper = [0, 2, 4, 0]
        while api_call < 4:
            self.response = session_call(url, timeout=self.timeout, **params)

            # Look for errors
            resp = self.response.json()
            if not self.future:
                error = resp["error"]
            else:
                if resp["result"] == "success":
                    error = []
                else:
                    error = resp["error"]
            if error:
                time.sleep(sleeper[api_call])
                api_call += 1
                continue

            if self.response.status_code not in (200, 201, 202):
                self.response.raise_for_status()
            else:
                break
        else:
            raise ConnectionError(
                f"{error}\n" f"-> URL: {url}\n-> Params: {params}\n"  # noqa
            )

        return self.response.json(**self._json_options)

    def query(self, method: str, data: Optional[Dict] = None):
        """Performs an API query that requires a valid key/secret pair.

        Parameters
        ----------
        method : str
            Method.
        data : dict, optional
            API request parameters.

        Returns
        -------
        response : dict
            Deserialized response.

        """
        if method not in API_METHODS:
            raise ValueError(
                f"Method {method} does not exists. Can only be "
                f"one of: {API_METHODS}"
            )

        if data is None:
            data = {}

        endpoint = self.apiversion + method

        # create authentication headers
        if method in API_PRIVATE_GET or method in API_PRIVATE_POST:
            if self.api_key is None or self.api_secret is None:
                raise ConnectionError("Need API keys to connect")

            if not self.future:
                endpoint = self.apiversion + "private/" + method
            headers = self._sign_message(data, endpoint)
        else:
            if not self.future:
                endpoint = self.apiversion + "public/" + method
            headers = {}

        return self._query(method, data, endpoint, headers)

    def _sign_message(self, data: Dict, endpoint: str) -> Dict[str, str]:
        """Sign request data according to Kraken's scheme.

        Parameters
        ----------
        data : dict
            API request parameters.
        endpoint : str
            API URL path sans host.

        Return
        ------
        headers : dict
            Signed headers.

        """
        nonce = str(int(1000 * time.time()))
        if not self.future:
            data["nonce"] = nonce

        data = urllib.parse.urlencode(data)
        # Cryptographic hash algorithms
        if not self.future:
            message = (nonce + data).encode()
            sha256_hash = endpoint.encode() + hashlib.sha256(message).digest()
        else:
            message = (data + nonce + endpoint).encode()
            sha256_hash = hashlib.sha256(message).digest()

        # Signing with API secret
        api_secret = base64.b64decode(self.api_secret)
        signature = hmac.new(api_secret, sha256_hash, hashlib.sha512).digest()
        signature = base64.b64encode(signature).decode()

        if not self.future:
            headers = {"API-Key": self.api_key, "API-Sign": signature}
        else:
            headers = {"APIKey": self.api_key, "Nonce": nonce, "Authent": signature}

        return headers
