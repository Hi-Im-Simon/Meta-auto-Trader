import MetaTrader5 as mt5


def map_timeframe(timeframe: int) -> str:
    match timeframe:
        case mt5.TIMEFRAME_M1:
            return "M1"
        case mt5.TIMEFRAME_M5:
            return "M5"
        case mt5.TIMEFRAME_M15:
            return "M15"
        case mt5.TIMEFRAME_M30:
            return "M30"
        case mt5.TIMEFRAME_H1:
            return "H1"
        case mt5.TIMEFRAME_H4:
            return "H4"
        case mt5.TIMEFRAME_D1:
            return "D1"
        case mt5.TIMEFRAME_W1:
            return "W1"
        case mt5.TIMEFRAME_MN1:
            return "MN1"
        case _:
            return str(timeframe)
