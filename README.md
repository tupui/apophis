[![Tests](https://github.com/tupui/apophis/workflows/Tests/badge.svg?branch=master)](
https://github.com/tupui/apophis/actions?query=workflow%3A%22Tests%22
)
[![Code Quality](https://github.com/tupui/apophis/workflows/Code%20Quality/badge.svg?branch=master)](
https://github.com/tupui/apophis/actions?query=workflow%3A%22Code+Quality%22
)
[![Package version](https://img.shields.io/pypi/v/apophis?label=pypi%20package)](
https://pypi.org/project/apophis
)

# Apophis: A python client for Kraken

Apophis is a Python client for Kraken's REST API. It provides a common interface
for both *Kraken* and *Kraken Future*.

**You want to say thanks?**

<p align="center">
<a href="https://www.buymeacoffee.com/tupui" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee: https://www.buymeacoffee.com/tupui" height=30" ></a>
</p>

## Quickstart

Public endpoints can be accessed without authentication.
```python
from apophis import Kraken

with Kraken() as exchange:
    price = exchange.market_price(pair='XXRPZEUR')
    print(price)

# 0.51081
```

For placing orders, authentication is necessary:
```python
from apophis import Kraken

key = ...
secret = ...
with Kraken(key, secret) as exchange:
    order = exchange.buy(pair='XXRPZEUR', volume=1000, price=0.5)

# Buying 1000 XXRPZEUR at 0.5 -> 500.0€
```

Alternatively, the low level API can be directly used to perform any kind of
query.

```python
from apophis import Apophis

with Apophis() as client:
    response = client.query('Ticker', {'pair': 'XXRPZEUR'})
    print(response['result'])

# {'XXRPZEUR': {'a': ['0.48683000', '33129', '33129.000'],
#               'b': ['0.48659000', '2915', '2915.000'],
#               'c': ['0.48719000', '41.55695712'],
#               'v': ['13015397.92184023', '46789050.96995769'],
#               'p': ['0.48149626', '0.47328592'],
#               't': [5110, 19079],
#               'l': ['0.45331000', '0.44697000'],
#               'h': ['0.49354000', '0.49681000'],
#               'o': '0.45730000'}}
```

Last but not least, there is a fully functional CLI:
```bash
❯ apophis query Ticker pair=XXRPZEUR
{'error': [], 'result': {'XXRPZEUR': {'a': ['0.45586000', '6356', '6356.000'], 'b': ['0.45561000', '63000', '63000.000'], 'c': ['0.45521000', '71.58800000'], 'v': ['27100060.07361936', '45765330.64314690'], 'p': ['0.43901689', '0.45396762'], 't': [11527, 19747], 'l': ['0.41500000', '0.41500000'], 'h': ['0.46588000', '0.49300000'], 'o': '0.46153000'}}}
❯ apophis price "XXRPZEUR"
XXRPZEUR: 0.45352
```




## Installation

The latest stable release (and older versions) can be installed from PyPI:

    pip install apophis

You may instead want to use the development version from Github. Poetry is
needed and can be installed either from PyPI or:

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

Then once you cloned the repository, you can install it with:

    poetry install

## Contributing

Want to add a cool logo, more doc, tests or new features? Contributors are more
than welcome! Feel free to open an [issue](https://github.com/tupui/apophis/issues)
or even better propose changes with a [PR](https://github.com/tupui/apophis/compare).
Have a look at the contributing guide.
