from math import ceil, floor
from typing import Callable

import MetaTrader5 as mt5
import numpy as np
import numpy.typing as npt
from colorama import Back
from rgbprint import Color
from tabulate import tabulate

from src.constants.general import DEFAULT_RSI_LEVEL_HIGH, DEFAULT_RSI_LEVEL_LOW
from src.models import Symbol, Timeframe, TimeframeInit
from src.models.exceptions import MT5InitFailure, NoDataException
from src.scripts import calculate_rsi
from src.utils import map_timeframe


class AutoTrader:

    def __init__(
        self,
        symbols: list[Symbol],
        timeframes: list[TimeframeInit],
        get_invest_value: Callable[
            [Symbol, float, float], float
        ] = lambda symbol, balance, recommendation_factor: balance
        * recommendation_factor,
        ignore_warnings: bool = False,
        print_steps: bool = True,
        print_results: bool = True,
        rsi_window: int = 5,
        rsi_level_low: float = DEFAULT_RSI_LEVEL_LOW,
        rsi_level_high: float = DEFAULT_RSI_LEVEL_HIGH,
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
        self.get_bet_value = get_invest_value
        self.ignore_warnings = ignore_warnings
        self.print_steps = print_steps
        self.print_results = print_results
        self.rsi_window = rsi_window
        self.rsi_level_low = rsi_level_low
        self.rsi_level_high = rsi_level_high
        self.rsi_level_middle = (rsi_level_low + rsi_level_high) / 2

    def calculate_rf(self) -> None:
        """
        Calculate the recommendation factor for each symbol. Takes all given timeframes into account.
        """
        if self.print_steps:
            table_headers = ["Symbol"]
            table_rows = []

        for symbol in self.symbols:
            rsis: npt.NDArray[np.float64] = np.array([])
            table_row = [symbol["name"]]

            for timeframe in self.timeframes:
                try:
                    rsi_value = calculate_rsi(self, symbol["name"], timeframe["value"])
                    rsis = np.append(rsis, rsi_value)
                    table_row.append(self.__auto_color(rsi_value))
                    if self.print_steps:
                        table_headers.append(map_timeframe(timeframe["value"]))
                except NoDataException as e:
                    if self.print_steps:
                        table_row.append("")
                    if not self.ignore_warnings:
                        print(e)
            table_headers.append("")
            table_headers.append("BUY")
            table_headers.append("SELL")

            weights = np.array([3 / i for i in range(5, len(rsis) + 5)])
            recommendation_factor_sell = np.average(rsis, weights=weights) / 100
            recommendation_factor_buy = 1 - recommendation_factor_sell

            if self.print_steps:
                table_row.append(self.__auto_color(recommendation_factor_buy, low=-1, high=0.5, middle=0, max=1, highlight=False))  # type: ignore
                table_row.append(self.__auto_color(recommendation_factor_sell, low=-1, high=0.5, middle=0, max=1, highlight=False))  # type: ignore)  # type: ignore
                table_rows.append(table_row)

        if self.print_steps:
            # Create and display table with collected data.
            print(
                tabulate(
                    table_rows,
                    headers=table_headers,
                    tablefmt="grid",
                    colalign=[
                        "center",
                        *["right" for _ in range(len(table_rows[0]) - 1)],
                    ],
                    floatfmt=".2f",
                ),
                self.color("BAD", Color(255, 0, 0)),
                self.color("OKAY", Color(255, 255, 255)),
                self.color("AMAZING", Color(0, 255, 0)),
            )

    def __auto_color(
        self,
        value: float,
        low: float | None = None,
        high: float | None = None,
        middle: float | None = None,
        min: float | None = None,
        max: float | None = None,
        highlight: bool = True,
    ) -> str:
        low = low if low is not None else self.rsi_level_low
        high = high if high is not None else self.rsi_level_high
        middle = middle if middle is not None else ((low + high) / 2)
        min = min if min is not None else 0
        max = max if max is not None else 100

        r, g, b = 255, 255, 255
        back = None

        if value >= high or value <= low:
            if value >= high:
                white = 255 - ceil(255 * ((value - high) / (max - high)))
            elif value <= low:
                white = 255 - ceil(255 * ((low - value) / (low - min)))
            r, b = white, white
            if highlight:
                back = Back.LIGHTBLACK_EX
        else:
            if value >= middle:
                white = floor(255 * ((value - middle) / (high - middle)))
            else:
                white = floor(255 * ((middle - value) / (middle - low)))
            g, b = white, white
        return self.color(value, Color(r, g, b), back=back)

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
