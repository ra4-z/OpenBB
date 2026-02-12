"""Longbridge Equity Search Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_search import (
    EquitySearchData,
    EquitySearchQueryParams,
)
from pydantic import Field


class LongbridgeEquitySearchQueryParams(EquitySearchQueryParams):
    """Longbridge Equity Search Query.

    Uses the static_info endpoint to search for securities.

    Source: https://open.longportapp.com/
    """

    market: Literal["HK", "US", "SH", "SZ", "SG", "JP"] = Field(
        default="US",
        description="Market to search in. One of: HK, US, SH, SZ, SG, JP.",
    )


class LongbridgeEquitySearchData(EquitySearchData):
    """Longbridge Equity Search Data."""

    exchange: str | None = Field(
        default=None,
        description="Exchange where the security is listed.",
    )
    lot_size: int | None = Field(
        default=None,
        description="Board lot size for the security.",
    )
    security_type: str | None = Field(
        default=None,
        description="Type of the security (e.g., Equity, ETF).",
    )


class LongbridgeEquitySearchFetcher(
    Fetcher[LongbridgeEquitySearchQueryParams, list[LongbridgeEquitySearchData]]
):
    """Longbridge Equity Search Fetcher."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> LongbridgeEquitySearchQueryParams:
        """Transform the query."""
        return LongbridgeEquitySearchQueryParams(**params)

    @staticmethod
    def extract_data(
        query: LongbridgeEquitySearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw data from the Longbridge API."""
        # pylint: disable=import-outside-toplevel
        from longport.openapi import QuoteContext
        from openbb_longbridge.utils.helpers import get_config

        config = get_config(credentials)
        ctx = QuoteContext(config)

        # If user provided a specific symbol query (is_symbol=True), use static_info
        if query.is_symbol and query.query:
            from openbb_longbridge.utils.helpers import format_symbol

            symbol = format_symbol(query.query)
            infos = ctx.static_info([symbol])

            results = []
            for info in infos:
                results.append(
                    {
                        "symbol": info.symbol,
                        "name": info.name_en or info.name_cn,
                        "exchange": info.exchange,
                        "lot_size": info.lot_size,
                        "security_type": str(info.security_type)
                        if hasattr(info, "security_type")
                        else None,
                    }
                )
            return results

        # For general queries, use security_list to get securities from the market
        from longport.openapi import Market, SecurityListCategory

        market = getattr(Market, query.market)

        securities = ctx.security_list(
            market=market,
            category=SecurityListCategory.Overnight,
        )

        results = []
        query_lower = query.query.lower() if query.query else ""

        for sec in securities:
            name = getattr(sec, "name_en", "") or getattr(sec, "name_cn", "") or ""
            symbol = getattr(sec, "symbol", "")

            # Filter by query string if provided
            if query_lower and query_lower not in name.lower() and query_lower not in symbol.lower():
                continue

            results.append(
                {
                    "symbol": symbol,
                    "name": name,
                }
            )

        return results

    @staticmethod
    def transform_data(
        query: LongbridgeEquitySearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[LongbridgeEquitySearchData]:
        """Transform the data."""
        return [LongbridgeEquitySearchData.model_validate(d) for d in data]
