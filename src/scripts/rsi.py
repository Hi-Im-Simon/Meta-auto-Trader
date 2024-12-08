from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import MetaTrader5 as mt5
import pandas as pd

from src.models.exceptions.NoDataException import NoDataException
from src.utils import map_timeframe

from .. import AutoTrader


def calculate_rsi(
    self: AutoTrader,
    symbol_name: str,
    timeframe: int,
    rsi_window: int = 5,
    plot: bool = False,
) -> float:
    """
    Calculate the RSI for a given symbol and timeframe.
    """
    end = datetime.now()
    start = end - timedelta(days=31)

    ticks = pd.DataFrame(mt5.copy_rates_range(symbol_name, timeframe, start, end))  # type: ignore

    delta = ticks["close"].diff()

    # If no data is available, throw an exception.
    if delta.dropna().empty:
        raise NoDataException(
            self.color_warn(
                f"[NO DATA] No data found for symbol '{symbol_name}' in timeframe '{map_timeframe(timeframe)}'(s)."
            )
        )

    gain = delta.where(delta > 0, 0)  # type: ignore
    loss = -delta.where(delta < 0, 0)  # type: ignore

    gain_ema = gain.ewm(alpha=1 / rsi_window, adjust=False).mean()
    loss_ema = loss.ewm(alpha=1 / rsi_window, adjust=False).mean()
    rs = gain_ema / loss_ema

    ticks["rsi"] = 100 - (100 / (1 + rs))

    if plot:
        ticks["time"] = pd.to_datetime(ticks["time"], unit="s")
        plt.plot(ticks["time"], ticks["rsi"], "b-", label=f"RSI ({rsi_window})")
        plt.legend(loc="upper left")
        plt.title(symbol_name)
        plt.show()

    return ticks["rsi"].tail(1).values[0]
