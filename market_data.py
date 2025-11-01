import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

class MarketData:
    """為替データ取得とテクニカル指標計算"""

    def fetch_ohlc(self, interval: str, date: str, price_type: str = "BID") -> pd.DataFrame:
        url = f'https://forex-api.coin.z.com/public/v1/klines?symbol=USD_JPY&priceType={price_type}&interval={interval}&date={date}'
        res = requests.get(url)
        data = res.json()["data"]
        JST = timezone(timedelta(hours=+0), 'JST')
        ohlc = []
        for row in data:
            dt = datetime.fromtimestamp(float(row["openTime"]) / 1000).replace(tzinfo=timezone.utc).astimezone(tz=JST)
            ohlc.append({
                "datetime": dt,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
        return pd.DataFrame(ohlc)

    def calc_macd(self, close: pd.Series):
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        osc = macd - signal
        return osc, signal

    def calc_rsi(self, close: pd.Series, window: int = 8):
        diff = close.diff()
        up = diff.clip(lower=0)
        down = -diff.clip(upper=0)
        ma_up = up.rolling(window=window).mean()
        ma_down = down.rolling(window=window).mean()
        rsi = 100 * ma_up / (ma_up + ma_down)
        return rsi

    def calc_slope(self, data, window):
        x = np.arange(window)
        y = data[-window:]
        return np.polyfit(x, y, 1)[0]
    
    def calc_sma(self, close, window):
        sma = close.rolling(window=window).mean()
        return sma
   