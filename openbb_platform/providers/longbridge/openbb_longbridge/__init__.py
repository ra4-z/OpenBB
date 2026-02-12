"""Longbridge/LongPort data provider module."""

from openbb_core.provider.abstract.provider import Provider
from openbb_longbridge.models.equity_historical import (
    LongbridgeEquityHistoricalFetcher,
)
from openbb_longbridge.models.equity_quote import LongbridgeEquityQuoteFetcher
from openbb_longbridge.models.equity_search import LongbridgeEquitySearchFetcher
from openbb_longbridge.models.market_snapshots import (
    LongbridgeMarketSnapshotsFetcher,
)

longbridge_provider = Provider(
    name="longbridge",
    website="https://open.longportapp.com",
    description="""LongPort (Longbridge) is a Hong Kong-based brokerage providing
programmatic trading and market data access for HK, US, and China A-share markets
through its OpenAPI platform.""",
    credentials=["app_key", "app_secret", "access_token"],
    fetcher_dict={
        "EquityHistorical": LongbridgeEquityHistoricalFetcher,
        "EquityQuote": LongbridgeEquityQuoteFetcher,
        "EquitySearch": LongbridgeEquitySearchFetcher,
        "MarketSnapshots": LongbridgeMarketSnapshotsFetcher,
    },
    repr_name="LongBridge (LongPort)",
    instructions="Get your API credentials at https://open.longportapp.com. "
    "You need app_key, app_secret, and access_token.",
)
