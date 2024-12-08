import json

from src.AutoTrader import AutoTrader
from src.config.setup import *

file_symbols = open("symbols.json", "r")
symbols = json.load(file_symbols)
file_timeframes = open("timeframes.json", "r")
timeframes = json.load(file_timeframes)

trader = AutoTrader(
    symbols=symbols,
    timeframes=timeframes,
    get_invest_value=lambda symbol, balance, recommendation_factor: balance
    * recommendation_factor,
    ignore_warnings=True,
)
trader.calculate_rf()
