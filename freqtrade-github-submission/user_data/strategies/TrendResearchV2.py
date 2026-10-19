"""Three pre-specified research candidates; spot, 1h, finite-window indicators.

2024 selects a candidate. 2025 is evaluated only after selection; it is an
already-existing historical validation segment, not an untouched forward test.
"""
from pandas import DataFrame, concat
from freqtrade.strategy import IStrategy


class RegimeMomentumV2(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    startup_candle_count = 600
    process_only_new_candles = True
    minimal_roi = {}
    stoploss = -0.10
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    position_adjustment_enable = False
    order_types = {"entry": "market", "exit": "market", "stoploss": "market", "stoploss_on_exchange": False}
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for window in (24, 48, 72, 120, 200, 480):
            dataframe[f"sma{window}"] = dataframe.close.rolling(window).mean()
        previous = dataframe.close.shift(1)
        tr = concat([dataframe.high-dataframe.low,
                     (dataframe.high-previous).abs(), (dataframe.low-previous).abs()], axis=1).max(axis=1)
        dataframe["atr24"] = tr.rolling(24).mean()
        dataframe["atr_fraction"] = dataframe.atr24/dataframe.close
        denominator = dataframe.close.diff().abs().rolling(48).sum().replace(0, float("nan"))
        dataframe["efficiency48"] = dataframe.close.diff(48).abs()/denominator
        dataframe["high24"] = dataframe.high.rolling(24).max().shift(1)
        # Using a close-based trailing exit gives next-open execution, without
        # claiming an intrabar ATR trailing-stop fill.
        dataframe["chandelier"] = dataframe.high.rolling(72).max()-5*dataframe.atr24
        return dataframe

    def entry_condition(self, d):
        return (d.close>d.sma200) & (d.sma48>d.sma200) & (d.sma200>d.sma200.shift(24))

    def exit_condition(self, d):
        return ((d.close<d.sma200*0.99) & (d.close.shift(1)<d.sma200.shift(1)*0.99)) | (d.sma48<d.sma200)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        condition = self.entry_condition(dataframe) & (dataframe.volume>0) & (dataframe.atr_fraction<0.04)
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, self.__class__.__name__)
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_tag"] = ""
        condition = self.exit_condition(dataframe) & (dataframe.volume>0)
        dataframe.loc[condition, ["exit_long", "exit_tag"]] = (1, "regime_exit")
        return dataframe


class ChandelierMomentumV2(RegimeMomentumV2):
    def entry_condition(self, d):
        return super().entry_condition(d) & (d.close>d.high24) & (d.efficiency48>0.15)

    def exit_condition(self, d):
        return (d.close<d.chandelier) | ((d.close<d.sma200) & (d.close.shift(1)<d.sma200.shift(1)))


class DualHorizonTrendV2(RegimeMomentumV2):
    def entry_condition(self, d):
        return (d.close>d.sma480) & (d.sma120>d.sma480) & (d.sma480>d.sma480.shift(48)) & (d.sma24>d.sma72)

    def exit_condition(self, d):
        return ((d.sma24<d.sma72) & (d.close<d.sma120)) | (d.close<d.sma480*0.98)
