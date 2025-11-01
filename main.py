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

def main():
    market = MarketData()
    trader = TradeManager(API_KEY, SECRET_KEY, ORDER_SIZE)
    today = datetime.datetime.now().strftime('%Y%m%d')
    # today = datetime.datetime(2025,8,18).strftime('%Y%m%d')
    total = 0
    order_price = 0
    close_price = 0
    profit = 0
    back_action = None
    back_time = datetime.datetime.now().time()

    while True:
        try:
            df = market.fetch_ohlc('5min', today, price_type="BID")
            df_ask = market.fetch_ohlc('5min', today, price_type="ASK")
            spread = df_ask["close"].iloc[-1] - df["close"].iloc[-1]

            osc, _ = market.calc_macd(df["close"])
            rsi = market.calc_rsi(df["close"], 3)
            slope_rsi = market.calc_slope(rsi, 2)
            sma = market.calc_sma(df["close"], 3)
            slope_sma = market.calc_slope(sma, 2)
        except Exception as e:
            print("Data fetch error:", e)
            time.sleep(10)
            continue

        # 損益計算
        if back_action == "BUY":
            close_price = df_ask["close"].iloc[-1]
            profit = close_price - order_price
        elif back_action == "SELL":
            close_price = df["close"].iloc[-1]
            profit = order_price - close_price
        # 時刻変化算出
        if back_time != df["datetime"].iloc[-1].time():
            back_time = df["datetime"].iloc[-1].time()
        else:
            continue

        action = trader.judge_order(spread, osc, rsi, slope_rsi, slope_sma, profit)
        if action in ["BUY", "SELL"]:
            trader.send_order(action)
            back_action = action
            order_price = df["close"].iloc[-1]
            profit = 0
            print(f"{df['datetime'].iloc[-1].time()} action : {action} order_price : {order_price}")
        elif action == "CLOSE":
            trader.close_position()
            total = total + profit
            print(f"{df['datetime'].iloc[-1].time()} action : {action} close_price : {close_price}")
            print("profit :", profit)
        elif action == "WAIT":
            trader.open_positions()
        else:
            print("No trade")

        # 18:00以降、または日次損益が閾値を超えたらポジションをクローズ
        now = datetime.datetime.now().time()
        print(now)
        if now >= datetime.time(18, 0, 0) and (action == "CLOSE" or action == None):
            print("day_total :", total)
            trader.close_position()
            break

        time.sleep(10)

if __name__ == '__main__':
    main()