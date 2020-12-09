import typer

from apophis import Apophis, Kraken, KrakenFuture
from apophis.configuration import Credentials


app = typer.Typer()
api_credentials = Credentials()


@app.callback()
def callback(
    key: str = api_credentials.key,
    secret: str = api_credentials.secret,
    future: bool = api_credentials.future,
) -> None:
    """Apophis."""
    global api_credentials
    api_credentials = Credentials(**locals())


@app.command()
def query(method: str, data: str = None) -> None:
    """Apophis calls the Kraken."""
    with Apophis(**api_credentials.dict()) as client:
        try:
            response = client.query(method=method, data=data)
        except ConnectionError as conn_err:
            typer.echo(f"Connection issue:\n{conn_err}")
            raise typer.Exit(code=1)
        except ValueError as val_err:
            typer.echo(val_err)
            raise typer.Exit(code=1)
        else:
            typer.echo(f"{response}")


def _order(pair: str, volume: float, price: float = None, side: str = "buy") -> None:
    if api_credentials.future:
        exchange_ = KrakenFuture
    else:
        exchange_ = Kraken

    api_credentials_ = api_credentials.dict()
    del api_credentials_["future"]

    with exchange_(**api_credentials_) as exchange:
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
