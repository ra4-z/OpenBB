"""Longbridge Market Snapshots Model."""

# pylint: disable=unused-argument

from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import DATA_DESCRIPTIONS, QUERY_DESCRIPTIONS
from pydantic import Field, field_validator


class LongbridgeMarketSnapshotsQueryParams(QueryParams):
    """Longbridge Market Snapshots Query.

    Get real-time market snapshots including depth, trades, and broker data.

    Source: https://open.longportapp.com/
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """Convert field to uppercase."""
        return v.upper()


class LongbridgeMarketSnapshotsData(Data):
    """Longbridge Market Snapshots Data."""

    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))
    last_done: float | None = Field(
        default=None,
        description="Last done (traded) price.",
    )
    open: float | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("open", "")
    )
    high: float | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("high", "")
    )
    low: float | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("low", "")
    )
    prev_close: float | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("prev_close", "")
    )
    volume: int | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("volume", "")
    )
    turnover: float | None = Field(
        default=None,
        description="Turnover value.",
    )
    timestamp: datetime | None = Field(
        default=None,
        description="Timestamp of the snapshot.",
    )
    ask_price: float | None = Field(
        default=None,
        description="Best ask price.",
    )
    ask_volume: int | None = Field(
        default=None,
        description="Volume at the best ask.",
    )
    bid_price: float | None = Field(
        default=None,
        description="Best bid price.",
    )
    bid_volume: int | None = Field(
        default=None,
        description="Volume at the best bid.",
    )


class LongbridgeMarketSnapshotsFetcher(
    Fetcher[
        LongbridgeMarketSnapshotsQueryParams,
        list[LongbridgeMarketSnapshotsData],
    ]
):
    """Longbridge Market Snapshots Fetcher."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> LongbridgeMarketSnapshotsQueryParams:
        """Transform the query."""
        return LongbridgeMarketSnapshotsQueryParams(**params)

    @staticmethod
    def extract_data(
        query: LongbridgeMarketSnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw data from the Longbridge API."""
        # pylint: disable=import-outside-toplevel
        from longport.openapi import QuoteContext
        from openbb_longbridge.utils.helpers import get_config, parse_symbols

        config = get_config(credentials)
        ctx = QuoteContext(config)
        symbols = parse_symbols(query.symbol)

        # Get quotes for snapshot data (includes depth info)
        quotes = ctx.quote(symbols)

        results = []
        for q in quotes:
            ts = None
            if hasattr(q, "timestamp") and q.timestamp:
                ts = datetime.fromtimestamp(q.timestamp.timestamp())

            results.append(
                {
                    "symbol": q.symbol,
                    "last_done": float(q.last_done) if q.last_done else None,
                    "open": float(q.open) if q.open else None,
                    "high": float(q.high) if q.high else None,
                    "low": float(q.low) if q.low else None,
                    "prev_close": float(q.prev_close) if q.prev_close else None,
                    "volume": int(q.volume) if q.volume else None,
                    "turnover": float(q.turnover) if q.turnover else None,
                    "timestamp": ts,
                }
            )

        # Try to get depth data for additional bid/ask info
        for i, symbol in enumerate(symbols):
            try:
                depth = ctx.depth(symbol)
                if depth and i < len(results):
                    asks = depth.asks if hasattr(depth, "asks") else []
                    bids = depth.bids if hasattr(depth, "bids") else []

                    if asks:
                        results[i]["ask_price"] = float(asks[0].price)
                        results[i]["ask_volume"] = int(asks[0].volume)
                    if bids:
                        results[i]["bid_price"] = float(bids[0].price)
                        results[i]["bid_volume"] = int(bids[0].volume)
            except Exception:  # noqa: BLE001
                pass

        return results

    @staticmethod
    def transform_data(
        query: LongbridgeMarketSnapshotsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[LongbridgeMarketSnapshotsData]:
        """Transform the data."""
        return [LongbridgeMarketSnapshotsData.model_validate(d) for d in data]
