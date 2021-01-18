"""Low level client for Binance."""
import hashlib
import hmac
import threading
import time
import urllib.parse

from typing import Dict, Optional

import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


version = "1.0"

API_PUBLIC = {
    "ping",
    "time",
    "exchangeInfo",
    "depth",
    "trades",
    "aggTrades",
    "avgPrice",
    "ticker/24hr",
    "ticker/price",
    "ticker/bookTicker",
}
API_PUBLIC_KEY = {"historicalTrades"}
API_SIGNED = {"order/test", "order", "openOrders", "allOrders"}
API_METHODS = API_PUBLIC | API_PUBLIC_KEY | API_SIGNED


class BinanceAPI:
    """Interact with Binance's API.

    Without specifying key/secret pair, only public queries can be performed.

    You can change the attribute ``uri`` if you want to call the conformance
    environment of Binance.

    Parameters
    ----------
    key : str, optional
        Public key identifier for queries to the API.
    secret : str, optional
        Private key used to sign messages.

    """

    def __init__(
        self,
        key: Optional[str] = None,
        secret: Optional[str] = None,
    ):
        # API keys
        self.api_key = key
        self.api_secret = secret

        self.uri = "https://api.binance.com"
        self.apiversion = "/api/v3/"

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

        self.lock = threading.Lock()

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

    def query(self, method: str, endpoint: str, data: Optional[Dict] = None):
        """Performs an API query.

        Parameters
        ----------
        method : str
            CRUD method.
        endpoint : str
            Endpoint.
        data : dict, optional
            API request parameters.

        Returns
        -------
        response : dict
            Deserialized response.

        """
        if endpoint not in API_METHODS:
            raise ValueError(
                f"Endpoint {endpoint} does not exists. Can only be "
                f"one of: {API_METHODS}"
            )

        if data is None:
            data = {}

        # need authentication headers
        if endpoint in API_PUBLIC_KEY or endpoint in API_SIGNED:
            if self.api_key is None or self.api_secret is None:
                raise ConnectionError("Need API keys to connect")

        url = self.uri + self.apiversion + endpoint

        if method == "get":
            params = {"params": data}
        elif method in ["post", "put", "delete"]:
            params = {"data": data}
        else:
            raise KeyError(f"Invalid method {method}")

        # Retry strategy: 4 times if API issue (ex. rate limit) with increasing
        # sleep to lower counter down. Last is 4 to be able to do a +2 ops.
        api_call = 0
        sleeper = [0, 2, 4, 0]
        while api_call < 4:

            self.lock.acquire()  # nonce call must be sequential
            if endpoint in API_PUBLIC_KEY or endpoint in API_SIGNED:
                data = self._sign_message(data)
                params["headers"] = {"X-MBX-APIKEY": self.api_key}

            if endpoint in API_SIGNED:
                params["data"] = data

            with getattr(self.session, method)(
                url, timeout=self.timeout, **params
            ) as self.response:

                self.lock.release()

                # Look for errors
                resp = self.response.json(**self._json_options)
                if "code" in resp:
                    error = resp["msg"]
                else:
                    error = None

                if error is not None:
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

        return resp

    def _sign_message(self, data: Dict) -> Dict[str, str]:
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
        data = data.copy()
        if "recvWindow" not in data:
            data.update({"recvWindow": 5000})

        timestamp = str(int(1000 * time.time()))
        data.update({"timestamp": timestamp})

        message = urllib.parse.urlencode(data)

        # Signing with API secret
        signature = hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256)
        signature = signature.hexdigest()

        data.update({"signature": signature})

        return data
