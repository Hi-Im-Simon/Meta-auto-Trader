from typing import TypedDict


class Timeframe(TypedDict):
    value: int
    weight: float


class TimeframeInit(TypedDict):
    """
    Timeframe definition for initialization. Values of type `str` are converted to `MetaTrader5.TIMEFRAME_*`.
    """

    value: int | str
    weight: float
