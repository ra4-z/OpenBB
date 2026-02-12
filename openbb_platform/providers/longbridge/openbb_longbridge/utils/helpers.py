"""Longbridge API helpers."""

from typing import Any


MARKET_MAP = {
    "HK": "HK",
    "US": "US",
    "SH": "SH",
    "SZ": "SZ",
    "SG": "SG",
    "JP": "JP",
}

PERIOD_MAP = {
    "1d": "Day",
    "1W": "Week",
    "1M": "Month",
    "1Y": "Year",
    "1m": "Min_1",
    "5m": "Min_5",
    "15m": "Min_15",
    "30m": "Min_30",
    "60m": "Min_60",
}

ADJUST_MAP = {
    "none": "NoAdjust",
    "forward": "ForwardAdjust",
    "backward": "BackwardAdjust",
}


def get_config(credentials: dict[str, str] | None) -> Any:
    """Create a LongPort Config from credentials."""
    from longport.openapi import Config  # pylint: disable=import-outside-toplevel

    if credentials is None:
        return Config.from_env()

    app_key = credentials.get("longbridge_app_key", "")
    app_secret = credentials.get("longbridge_app_secret", "")
    access_token = credentials.get("longbridge_access_token", "")

    return Config(
        app_key=app_key,
        app_secret=app_secret,
        access_token=access_token,
    )


def format_symbol(symbol: str) -> str:
    """Format symbol to Longbridge format.

    If the symbol already has a market suffix (e.g., '700.HK'), return as-is.
    Otherwise, assume US market and append '.US'.
    """
    if "." in symbol:
        return symbol.upper()
    return f"{symbol.upper()}.US"


def parse_symbols(symbol: str) -> list[str]:
    """Parse comma-separated symbols and format them for Longbridge."""
    return [format_symbol(s.strip()) for s in symbol.split(",") if s.strip()]
