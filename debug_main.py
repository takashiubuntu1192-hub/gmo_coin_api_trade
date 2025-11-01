import time
import datetime
import json
from pathlib import Path
from market_data import MarketData
from trade_manager import TradeManager

# Load config from config.json located next to this script
config_path = Path(__file__).with_name("config.json")
if not config_path.exists():
    raise FileNotFoundError(f"config.json not found: {config_path}")
with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

API_KEY = cfg.get("API_KEY")
SECRET_KEY = cfg.get("SECRET_KEY")
ORDER_SIZE = cfg.get("ORDER_SIZE", "2000")

def job(market, trader, today):
    total = 0
    order_price = 0
    close_price = 0
    back_action = None
    idx = 0
    profit = 0
    deb_df = market.fetch_ohlc('5min', today, price_type="BID")
    deb_df_ask = market.fetch_ohlc('5min', today, price_type="ASK")
    back_time = datetime.datetime.now().time()

    while True:
      df = deb_df[1:10+idx]
      df_ask = deb_df_ask[1:10+idx]
      spread = df_ask["close"].iloc[-1] - df["close"].iloc[-1]

      osc, _ = market.calc_macd(df["close"])
      rsi = market.calc_rsi(df["close"], 3)
      slope_rsi = market.calc_slope(rsi, 2)
      sma = market.calc_sma(df["close"], 3)
      slope_sma = market.calc_slope(sma, 2)

      if back_action == "BUY":
        close_price = df_ask["close"].iloc[-1]
        profit = close_price - order_price
      elif back_action == "SELL":
        close_price = df["close"].iloc[-1]
        profit = order_price - close_price

      action = trader.judge_order(spread, osc, rsi, slope_rsi, slope_sma, profit)
      if action in ["BUY", "SELL"]:
          back_action = action
          order_price = df["close"].iloc[-1]
          trader.debug_open_positions()
          profit = 0
          print(f"{df['datetime'].iloc[-1].time()} action : {action} order_price : {order_price}")
      elif action == "CLOSE":
          total = total + profit
          print(f"{df['datetime'].iloc[-1].time()} action : {action} close_price : {close_price}")
          print("profit :", profit)
      
      now = df["datetime"].iloc[-1].time()
      idx = idx + 1
      if now >= datetime.time(18, 0, 0) and (action == "CLOSE" or action == None):
          break
    
    return total


def main():
    market = MarketData()
    trader = TradeManager(API_KEY, SECRET_KEY, ORDER_SIZE)
    # today = datetime.datetime(2025,1,6)
    today = datetime.datetime(2025,10,1)
    total = 0

    while True:
        # 土日をスキップ
        if today.weekday() < 5:
          profit = job(market, trader, today.strftime('%Y%m%d'))
          total = total + profit
          print("date :", today.strftime('%Y%m%d'))
          print("day_total :", profit)
          print("debug_total :", total)
          print("////////////////////////////////////")
        today = today + datetime.timedelta(days=1)

if __name__ == '__main__':
    main()