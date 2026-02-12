"""Longbridge API helpers."""

from pathlib import Path
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


def _load_env_file() -> dict[str, str]:
    """Load credentials from .env.longbridge file.

    Searches for the file in the provider package directory.
    """
    env_vars: dict[str, str] = {}
    env_path = Path(__file__).resolve().parent.parent.parent / ".env.longbridge"

    if not env_path.is_file():
        return env_vars

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if value:
                env_vars[key] = value

    return env_vars


def get_config(credentials: dict[str, str] | None) -> Any:
    """Create a LongPort Config from credentials.

    Resolution order:
    1. credentials dict passed by OpenBB core (from user_settings / env vars)
    2. .env.longbridge file in the provider package directory
    3. LongPort SDK Config.from_env() fallback
    """
    from longport.openapi import Config  # pylint: disable=import-outside-toplevel

    app_key = ""
    app_secret = ""
    access_token = ""

    # 1) Try credentials dict from OpenBB core
    if credentials:
        app_key = credentials.get("longbridge_app_key", "")
        app_secret = credentials.get("longbridge_app_secret", "")
        access_token = credentials.get("longbridge_access_token", "")

    # 2) Fallback: load from .env.longbridge file
    if not all([app_key, app_secret, access_token]):
        env_vars = _load_env_file()
        app_key = app_key or env_vars.get("LONGBRIDGE_APP_KEY", "")
        app_secret = app_secret or env_vars.get("LONGBRIDGE_APP_SECRET", "")
        access_token = access_token or env_vars.get("LONGBRIDGE_ACCESS_TOKEN", "")

    # 3) Fallback: let LongPort SDK load from system env
    if not all([app_key, app_secret, access_token]):
        return Config.from_env()

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
