from typing import Union

import typer

from apophis import Kraken, KrakenFuture
from apophis.configuration import Credentials


app = typer.Typer()
exchange: Union[Kraken, KrakenFuture]
api_credentials = Credentials()


def close_exchange(*args, **kwargs):
    """Cleaning up."""
    exchange.close()


@app.callback(result_callback=close_exchange)
def open_exchange(
    key: str = api_credentials.key,
    secret: str = api_credentials.secret,
    future: bool = api_credentials.future,
) -> None:
    """Apophis."""
    global api_credentials, exchange
    api_credentials = Credentials(**locals())

    if api_credentials.future:
        exchange_ = KrakenFuture
    else:
        exchange_ = Kraken

    api_credentials = api_credentials.dict()
    del api_credentials["future"]

    exchange = exchange_(**api_credentials)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def query(data: typer.Context, method: str) -> None:
    """Apophis calls the Kraken."""
    data = dict([item.strip("--").split("=") for item in data.args])

    try:
        response = exchange.api.query(method=method, data=data)
    except ConnectionError as conn_err:
        typer.echo(f"Connection issue:\n{conn_err}")
        raise typer.Exit(code=1)
    except ValueError as val_err:
        typer.echo(val_err)
        raise typer.Exit(code=1)
    else:
        typer.echo(f"{response}")


def _order(pair: str, volume: float, price: float = None, side: str = "buy") -> None:
    if price is None:
        price = exchange.market_price(pair)

    exchange._order(pair=pair, volume=volume, price=price, side=side)


@app.command()
def buy(pair: str, volume: float, price: float = None) -> None:
    """Limit buy order."""
    _order(pair=pair, volume=volume, price=price, side="buy")


@app.command()
def sell(pair: str, volume: float, price: float = None) -> None:
    """Limit sell order."""
    _order(pair=pair, volume=volume, price=price, side="sell")


@app.command()
def price(pair: str):
    """Current market price."""
    price = exchange.market_price(pair)

    typer.echo(f"{pair}: {price}")
