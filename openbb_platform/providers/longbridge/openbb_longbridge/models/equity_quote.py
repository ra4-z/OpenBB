"""Longbridge Equity Quote Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_quote import (
    EquityQuoteData,
    EquityQuoteQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field


class LongbridgeEquityQuoteQueryParams(EquityQuoteQueryParams):
    """Longbridge Equity Quote Query.

    Source: https://open.longportapp.com/
    """

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}


class LongbridgeEquityQuoteData(EquityQuoteData):
    """Longbridge Equity Quote Data."""

    turnover: float | None = Field(
        default=None,
        description="Turnover value for the current trading day.",
    )
    last_done: float | None = Field(
        default=None,
        description="Last done price (last traded price).",
    )
    currency: str | None = Field(
        default=None,
        description="Currency of the quote.",
    )


class LongbridgeEquityQuoteFetcher(
    Fetcher[LongbridgeEquityQuoteQueryParams, list[LongbridgeEquityQuoteData]]
):
    """Longbridge Equity Quote Fetcher."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> LongbridgeEquityQuoteQueryParams:
        """Transform the query."""
        return LongbridgeEquityQuoteQueryParams(**params)

    @staticmethod
    def extract_data(
        query: LongbridgeEquityQuoteQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw data from the Longbridge API."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime, timezone

        from longport.openapi import QuoteContext
        from openbb_longbridge.utils.helpers import get_config, parse_symbols

        config = get_config(credentials)
        ctx = QuoteContext(config)
        symbols = parse_symbols(query.symbol)

        quotes = ctx.quote(symbols)

        if not quotes:
            raise EmptyDataError()

        results = []
        for q in quotes:
            last_ts = None
            if hasattr(q, "timestamp") and q.timestamp:
                last_ts = datetime.fromtimestamp(
                    q.timestamp.timestamp(), tz=timezone.utc
                )

            results.append(
                {
                    "symbol": q.symbol,
                    "name": getattr(q, "name", None),
                    "exchange": getattr(q, "exchange", None),
                    "last_price": float(q.last_done) if q.last_done else None,
                    "last_done": float(q.last_done) if q.last_done else None,
                    "open": float(q.open) if q.open else None,
                    "high": float(q.high) if q.high else None,
                    "low": float(q.low) if q.low else None,
                    "prev_close": float(q.prev_close) if q.prev_close else None,
                    "volume": int(q.volume) if q.volume else None,
                    "turnover": float(q.turnover) if q.turnover else None,
                    "last_timestamp": last_ts,
                    "currency": getattr(q, "currency", None),
                }
            )

        return results

    @staticmethod
    def transform_data(
        query: LongbridgeEquityQuoteQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[LongbridgeEquityQuoteData]:
        """Transform the data."""
        return [LongbridgeEquityQuoteData.model_validate(d) for d in data]
