"""Tests for Longbridge fetchers."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def credentials():
    """Return mock credentials."""
    return {
        "longbridge_app_key": "test_app_key",
        "longbridge_app_secret": "test_app_secret",
        "longbridge_access_token": "test_access_token",
    }


class MockCandlestick:
    """Mock candlestick data."""

    def __init__(self):
        self.open = "150.00"
        self.high = "155.00"
        self.low = "149.00"
        self.close = "153.00"
        self.volume = 1000000
        self.turnover = "153000000.00"
        self.timestamp = MagicMock()
        self.timestamp.timestamp.return_value = 1704067200.0  # 2024-01-01


class MockQuote:
    """Mock quote data."""

    def __init__(self, symbol="AAPL.US"):
        self.symbol = symbol
        self.name = "Apple Inc."
        self.exchange = "NASDAQ"
        self.last_done = "150.00"
        self.open = "148.00"
        self.high = "152.00"
        self.low = "147.00"
        self.prev_close = "149.00"
        self.volume = 50000000
        self.turnover = "7500000000.00"
        self.timestamp = MagicMock()
        self.timestamp.timestamp.return_value = 1704067200.0


class MockStaticInfo:
    """Mock static info data."""

    def __init__(self, symbol="AAPL.US"):
        self.symbol = symbol
        self.name_en = "Apple Inc."
        self.name_cn = "苹果公司"
        self.exchange = "NASDAQ"
        self.lot_size = 1
        self.security_type = "Equity"


class MockDepth:
    """Mock depth data."""

    def __init__(self):
        self.asks = [MagicMock(price="150.50", volume=100)]
        self.bids = [MagicMock(price="149.50", volume=200)]


@patch("openbb_longbridge.utils.helpers.Config")
@patch("openbb_longbridge.models.equity_historical.QuoteContext")
def test_equity_historical_fetcher(mock_ctx_class, mock_config, credentials):
    """Test EquityHistorical fetcher."""
    from openbb_longbridge.models.equity_historical import (
        LongbridgeEquityHistoricalFetcher,
    )

    mock_ctx = MagicMock()
    mock_ctx.history_candlesticks_by_date.return_value = [MockCandlestick()]
    mock_ctx_class.return_value = mock_ctx

    params = {
        "symbol": "AAPL.US",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 1, 31),
    }

    query = LongbridgeEquityHistoricalFetcher.transform_query(params)
    assert query.symbol == "AAPL.US"
    assert query.interval == "1d"
    assert query.adjustment == "none"

    data = LongbridgeEquityHistoricalFetcher.extract_data(query, credentials)
    assert len(data) == 1
    assert data[0]["open"] == 150.0
    assert data[0]["close"] == 153.0
    assert data[0]["volume"] == 1000000

    results = LongbridgeEquityHistoricalFetcher.transform_data(query, data)
    assert len(results) == 1
    assert results[0].close == 153.0


@patch("openbb_longbridge.utils.helpers.Config")
@patch("openbb_longbridge.models.equity_quote.QuoteContext")
def test_equity_quote_fetcher(mock_ctx_class, mock_config, credentials):
    """Test EquityQuote fetcher."""
    from openbb_longbridge.models.equity_quote import LongbridgeEquityQuoteFetcher

    mock_ctx = MagicMock()
    mock_ctx.quote.return_value = [MockQuote()]
    mock_ctx_class.return_value = mock_ctx

    params = {"symbol": "AAPL.US"}

    query = LongbridgeEquityQuoteFetcher.transform_query(params)
    assert query.symbol == "AAPL.US"

    data = LongbridgeEquityQuoteFetcher.extract_data(query, credentials)
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL.US"
    assert data[0]["last_price"] == 150.0

    results = LongbridgeEquityQuoteFetcher.transform_data(query, data)
    assert len(results) == 1
    assert results[0].symbol == "AAPL.US"


@patch("openbb_longbridge.utils.helpers.Config")
@patch("openbb_longbridge.models.equity_search.QuoteContext")
def test_equity_search_fetcher_symbol(mock_ctx_class, mock_config, credentials):
    """Test EquitySearch fetcher with symbol lookup."""
    from openbb_longbridge.models.equity_search import LongbridgeEquitySearchFetcher

    mock_ctx = MagicMock()
    mock_ctx.static_info.return_value = [MockStaticInfo()]
    mock_ctx_class.return_value = mock_ctx

    params = {"query": "AAPL", "is_symbol": True}

    query = LongbridgeEquitySearchFetcher.transform_query(params)
    data = LongbridgeEquitySearchFetcher.extract_data(query, credentials)
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL.US"
    assert data[0]["name"] == "Apple Inc."

    results = LongbridgeEquitySearchFetcher.transform_data(query, data)
    assert len(results) == 1


@patch("openbb_longbridge.utils.helpers.Config")
@patch("openbb_longbridge.models.market_snapshots.QuoteContext")
def test_market_snapshots_fetcher(mock_ctx_class, mock_config, credentials):
    """Test MarketSnapshots fetcher."""
    from openbb_longbridge.models.market_snapshots import (
        LongbridgeMarketSnapshotsFetcher,
    )

    mock_ctx = MagicMock()
    mock_ctx.quote.return_value = [MockQuote()]
    mock_ctx.depth.return_value = MockDepth()
    mock_ctx_class.return_value = mock_ctx

    params = {"symbol": "AAPL.US"}

    query = LongbridgeMarketSnapshotsFetcher.transform_query(params)
    data = LongbridgeMarketSnapshotsFetcher.extract_data(query, credentials)
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL.US"
    assert data[0]["ask_price"] == 150.5
    assert data[0]["bid_price"] == 149.5

    results = LongbridgeMarketSnapshotsFetcher.transform_data(query, data)
    assert len(results) == 1


def test_helpers():
    """Test helper functions."""
    from openbb_longbridge.utils.helpers import format_symbol, parse_symbols

    assert format_symbol("AAPL") == "AAPL.US"
    assert format_symbol("700.HK") == "700.HK"
    assert format_symbol("aapl") == "AAPL.US"

    symbols = parse_symbols("AAPL, 700.HK, TSLA")
    assert symbols == ["AAPL.US", "700.HK", "TSLA.US"]
