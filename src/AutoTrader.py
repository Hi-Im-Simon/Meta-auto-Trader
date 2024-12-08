from importlib import import_module
from math import ceil, floor
from typing import Callable

import MetaTrader5 as mt5
import numpy as np
import numpy.typing as npt
from colorama import Back
from rgbprint import Color
from tabulate import tabulate

from src.constants.general import RSI_LEVEL_HIGH, RSI_LEVEL_LOW
from src.models import Symbol, Timeframe, TimeframeInit
from src.models.exceptions import MT5InitFailure, NoDataException
from src.scripts import get_rsi
from src.utils import map_timeframe


class AutoTrader:

    def __init__(
        self,
        symbols: list[Symbol],
        timeframes: list[TimeframeInit],
        get_bet_value: Callable[
            [Symbol, float, float], float
        ] = lambda symbol, balance, recommendation_factor: balance
        * recommendation_factor,
        ignore_warnings: bool = False,
        rsi_window: int = 5,
        rsi_level_low: float = RSI_LEVEL_LOW,
        rsi_level_high: float = RSI_LEVEL_HIGH,
    ):
        if not mt5.initialize():  # type: ignore
            mt5.shutdown()  # type: ignore
            raise MT5InitFailure("MetaTrader5 initialization has failed.")

        self.symbols = symbols
        for tf in timeframes:
            if type(tf["value"]) != int:
                if type(tf["value"]) == str:
                    tf_name = tf["value"].split(".")[-1]
                    tf["value"] = mt5.__getattribute__(tf_name)  # type: ignore
                else:
                    exit(f"Invalid timeframe {tf}.")

        self.timeframes: list[Timeframe] = timeframes  # type: ignore
        self.get_bet_value = get_bet_value
        self.ignore_warnings = ignore_warnings
        self.rsi_window = rsi_window
        self.rsi_level_low = rsi_level_low
        self.rsi_level_high = rsi_level_high
        self.rsi_level_middle = (rsi_level_low + rsi_level_high) / 2
        "".startswith

    def do(self):
        rows = []
        table_headers = ["Symbol"]
        for symbol in self.symbols:
            rsis: npt.NDArray[np.float64] = np.array([])

            for timeframe in self.timeframes:
                try:
                    rsis = np.append(
                        rsis, get_rsi(self, symbol["name"], timeframe["value"])
                    )
                    table_headers.append(map_timeframe(timeframe["value"]))
                except NoDataException as e:
                    if not self.ignore_warnings:
                        print(e)

            table_headers.append("")
            table_headers.append("RecF")
            weights = np.array([3 / i for i in range(5, len(rsis) + 5)])
            recommendation_factor = np.average(rsis, weights=weights)

            rows.append(
                [
                    symbol["name"],
                    *[self.__auto_color(rsi) for rsi in rsis],
                    "",
                    self.__auto_color(recommendation_factor, high=60),  # type: ignore
                ]
            )

        table = tabulate(
            rows,
            headers=table_headers,
            tablefmt="grid",
            colalign=["center", *["right" for _ in range(len(rows[0]) - 1)]],
            floatfmt=".2f",
        )
        print(table)

    def __auto_color(
        self,
        value: float,
        low: float = RSI_LEVEL_LOW,
        high: float = RSI_LEVEL_HIGH,
    ) -> str:

        middle = (low + high) / 2

        if value >= high:
            white = 255 - ceil(255 * ((value - high) / (100 - high)))
            return self.color(value, Color(white, 255, white), back=Back.LIGHTBLACK_EX)
        elif value <= low:
            white = 255 - ceil(255 * ((low - value) / (low)))
            return self.color(value, Color(white, 255, white), back=Back.LIGHTBLACK_EX)
        else:
            if value >= middle:
                white = floor(255 * ((value - middle) / (high - middle)))
                return self.color(value, Color(255, white, white))
            else:
                white = floor(255 * ((middle - value) / (middle - low)))
                return self.color(value, Color(255, white, white))

    def color(
        self,
        message: str | float,
        color: Color | tuple[int, int, int],
        back: str | None = None,
        style: str | None = None,
    ) -> str:
        return f"{back if back else ""}{style if style else ""}{color}{message}{Color.reset}"

    def color_success(self, message: str | float) -> str:
        return self.color(message, Color.green)

    def color_warn(self, message: str | float) -> str:
        return self.color(message, Color(255, 204, 0))

    def color_error(self, message: str | float) -> str:
        return self.color(message, Color.red)
