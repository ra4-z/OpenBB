"""Longbridge Equity Historical Price Model."""

# pylint: disable=unused-argument

from datetime import date as dateType, datetime
from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalData,
    EquityHistoricalQueryParams,
)
from openbb_core.provider.utils.descriptions import QUERY_DESCRIPTIONS
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field


class LongbridgeEquityHistoricalQueryParams(EquityHistoricalQueryParams):
    """Longbridge Equity Historical Price Query.

    Source: https://open.longportapp.com/
    """

    __json_schema_extra__ = {
        "symbol": {"multiple_items_allowed": False},
        "interval": {
            "choices": ["1m", "5m", "15m", "30m", "60m", "1d", "1W", "1M", "1Y"]
        },
    }

    interval: Literal[
        "1m", "5m", "15m", "30m", "60m", "1d", "1W", "1M", "1Y"
    ] = Field(
        default="1d",
        description=QUERY_DESCRIPTIONS.get("interval", ""),
    )
    adjustment: Literal["none", "forward", "backward"] = Field(
        default="none",
        description="Price adjustment type. 'forward' for forward-adjusted, "
        "'backward' for backward-adjusted, 'none' for no adjustment.",
    )


class LongbridgeEquityHistoricalData(EquityHistoricalData):
    """Longbridge Equity Historical Price Data."""

    turnover: float | None = Field(
        default=None,
        description="Turnover value for the period.",
    )


class LongbridgeEquityHistoricalFetcher(
    Fetcher[
        LongbridgeEquityHistoricalQueryParams,
        list[LongbridgeEquityHistoricalData],
    ]
):
    """Longbridge Equity Historical Price Fetcher."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> LongbridgeEquityHistoricalQueryParams:
        """Transform the query."""
        from dateutil.relativedelta import relativedelta  # pylint: disable=import-outside-toplevel

        transformed_params = params.copy()
        now = datetime.now().date()

        if transformed_params.get("start_date") is None:
            transformed_params["start_date"] = now - relativedelta(years=1)
        if transformed_params.get("end_date") is None:
            transformed_params["end_date"] = now

        return LongbridgeEquityHistoricalQueryParams(**transformed_params)

    @staticmethod
    def extract_data(
        query: LongbridgeEquityHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw data from the Longbridge API."""
        # pylint: disable=import-outside-toplevel
        from longport.openapi import (
            AdjustType,
            Period,
            QuoteContext,
        )
        from openbb_longbridge.utils.helpers import (
            ADJUST_MAP,
            PERIOD_MAP,
            format_symbol,
            get_config,
        )

        config = get_config(credentials)
        ctx = QuoteContext(config)

        symbol = format_symbol(query.symbol)
        period = getattr(Period, PERIOD_MAP[query.interval])
        adjust = getattr(AdjustType, ADJUST_MAP[query.adjustment])

        candlesticks = ctx.history_candlesticks_by_date(
            symbol=symbol,
            period=period,
            adjust_type=adjust,
            start=query.start_date,
            end=query.end_date,
        )

        if not candlesticks:
            raise EmptyDataError()

        results = []
        for c in candlesticks:
            results.append(
                {
                    "date": datetime.fromtimestamp(c.timestamp.timestamp()),
                    "open": float(c.open),
                    "high": float(c.high),
                    "low": float(c.low),
                    "close": float(c.close),
                    "volume": int(c.volume),
                    "turnover": float(c.turnover),
                }
            )

        return results

    @staticmethod
    def transform_data(
        query: LongbridgeEquityHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[LongbridgeEquityHistoricalData]:
        """Transform the data to the standard format."""
        return [
            LongbridgeEquityHistoricalData.model_validate(d) for d in data
        ]
