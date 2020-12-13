import pandas as pd
import pytest

from apophis import Kraken, KrakenFuture


def test_exchange():
    with Kraken() as exchange:
        price = exchange.market_price("XXRPZEUR")
        assert 0 < price < 100

        order = exchange.buy("XXRPZEUR", 1000, 0.5)
        assert order
        assert exchange.n_buy == 1
        assert exchange.n_sell == 0
        buy_fee = exchange.fee
        exchange.buy("XXRPZEUR", 1000, 0.5)
        exchange.buy("XXRPZEUR", 1000, 0.5)
        assert exchange.fee == buy_fee * 3

        exchange.fee = 0
        order = exchange.sell("XXRPZEUR", 1000, 0.5)
        assert order
        assert exchange.n_buy == 3
        assert exchange.n_sell == 1
        sell_fee = exchange.fee
        exchange.sell("XXRPZEUR", 1000, 0.5)
        exchange.sell("XXRPZEUR", 1000, 0.5)
        assert exchange.fee == sell_fee * 3

        exchange.fee = 0
        exchange.buy("XXRPZEUR", 1000, 0.5)
        exchange.sell("XXRPZEUR", 1000, 0.5)
        assert exchange.fee == sell_fee + buy_fee


def test_ohlc():
    with Kraken() as exchange:
        ohlc = exchange.ohlc("XXRPZEUR")
        ohlc_historical = exchange.ohlc_from_trades("XXRPZEUR")

    assert len(ohlc) == 720
    assert 719 <= len(ohlc_historical) <= 721

    df_diff = pd.concat([ohlc, ohlc_historical]).drop_duplicates(keep=False)
    assert len(df_diff) / 720 < 0.05


def test_live():
    """Cannot test more without private API keys."""
    with pytest.raises(ConnectionError):
        with Kraken(live=True) as exchange:
            exchange.buy("XXRPZEUR", 1000, 0.5)

    with pytest.raises(ConnectionError):
        with Kraken(live=True) as exchange:
            exchange.sell("XXRPZEUR", 1000, 0.5)


def test_future_exchange():
    with KrakenFuture() as exchange:
        price = exchange.market_price("pi_xrpusd")
        assert 0 < price < 100
