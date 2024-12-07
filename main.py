from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
import MetaTrader5 as mt5

symbols = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "USDCAD",
    "AUDUSD",
    "AUDNZD",
    "AUDCAD",
    "AUDCHF",
    "AUDJPY",
    "XAUUSD",
    "XAGUSD",
]

if not mt5.initialize():
    mt5.shutdown()
    print("Initialization failed.")


def get_rsi(symbol: str, rsi_window: int = 5, plot: bool = False):
    end = datetime.now()
    start = end - timedelta(days=2000)

    ticks = pd.DataFrame(mt5.copy_rates_range(symbol, mt5.TIMEFRAME_W1, start, end))

    delta = ticks["close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    gain_ema = gain.ewm(alpha=1 / rsi_window, adjust=False).mean()
    loss_ema = loss.ewm(alpha=1 / rsi_window, adjust=False).mean()

    rs = gain_ema / loss_ema

    ticks["rsi"] = 100 - (100 / (1 + rs))

    if plot:
        ticks["time"] = pd.to_datetime(ticks["time"], unit="s")
        plt.plot(ticks["time"], ticks["rsi"], "b-", label=f"RSI ({rsi_window})")
        plt.legend(loc="upper left")
        plt.title(symbol)
        plt.show()

    return ticks["rsi"].tail(1).values[0]


for symbol in symbols:
    print(f"{symbol}: {get_rsi(symbol)}")
