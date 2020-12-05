import pytest

from apophis import Apophis


def test_client():
    with Apophis() as client:
        # unknown method
        with pytest.raises(ValueError):
            client.query(method='toto')

        # trying to access private method
        with pytest.raises(ConnectionError):
            client.query(method='Balance')

        # known method but wrong url. accounts from Future only
        with pytest.raises(ConnectionError):
            client.query(method='tickers')

    with Apophis(future=True) as client_future:
        client_future.query(method='tickers')


def test_response():
    with Apophis() as client:
        response = client.query('Ticker', {'pair': 'XXRPZEUR'})

        assert isinstance(response, dict)
        print(response['result'])
        assert 0 < float(response['result']['XXRPZEUR']['c'][0]) < 100
