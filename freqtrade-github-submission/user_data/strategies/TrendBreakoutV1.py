"""Freqtrade V3 spot strategy. Parameters frozen before historical evaluation."""
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class TrendBreakoutV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    startup_candle_count = 240
    process_only_new_candles = True
    minimal_roi = {}
    stoploss = -0.08
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    position_adjustment_enable = False
    order_types = {
        "entry": "market", "exit": "market", "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma50"] = dataframe["close"].rolling(50, min_periods=50).mean()
        dataframe["sma200"] = dataframe["close"].rolling(200, min_periods=200).mean()
        # Exclude the current candle from breakout channels.
        dataframe["prior_high48"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["prior_low20"] = dataframe["low"].rolling(20).min().shift(1)
        dataframe["trend_rising"] = dataframe["sma200"] > dataframe["sma200"].shift(24)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        condition = (
            (dataframe["volume"] > 0)
            & (dataframe["close"] > dataframe["sma200"])
            & (dataframe["sma50"] > dataframe["sma200"])
            & dataframe["trend_rising"]
            & (dataframe["close"] > dataframe["prior_high48"])
        )
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "trend_breakout48")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_tag"] = ""
        condition = (dataframe["volume"] > 0) & (
            (dataframe["close"] < dataframe["prior_low20"])
            | (dataframe["close"] < dataframe["sma200"])
        )
        dataframe.loc[condition, ["exit_long", "exit_tag"]] = (1, "channel_or_trend_exit")
        return dataframe
