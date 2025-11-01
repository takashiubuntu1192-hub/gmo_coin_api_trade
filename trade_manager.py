import requests
import hmac
import hashlib
import time
import json
from datetime import datetime

class TradeManager:
    """注文判定とAPI注文実行"""

    def __init__(self, api_key, secret_key, order_size):
        self.api_key = api_key
        self.secret_key = secret_key
        self.order_size = order_size
        self.position = None
        self.position_id = None
        self.position_time = None
        self.close_side = None

    def judge_order(self, spread, osc, rsi, slope_rsi, slope_sma, profit=0):
        """シンプルな売買判定例"""
        if self.position == None and spread < 0.0041:
            if osc.iloc[-1] > 0.003 and slope_rsi > 0 and slope_sma > 0 and rsi.tail(6).min() < 30:
                self.position = "BUY"
                self.position_id = None  # 初期化
                return "BUY"
            elif osc.iloc[-1] < -0.003 and slope_rsi < 0 and slope_sma < 0 and rsi.tail(6).max() > 60:
                self.position = "SELL"
                self.position_id = None  # 初期化
                return "SELL"
            else:
                return None
        elif self.position == "BUY":
            if self.position_id == None:
                return "WAIT"
            elif osc.iloc[-1] < -0.001 or (rsi.iloc[-1] > 58 and profit > 0.02):
                self.close_side = "SELL"
                self.position = None
                return "CLOSE"
            else:
                return "WAIT"
        elif self.position == "SELL":
            if self.position_id == None:
                return "WAIT"
            elif osc.iloc[-1] > 0.001 or (rsi.iloc[-1] < 32 and profit > 0.02):
                self.close_side = "BUY"
                self.position = None
                return "CLOSE"
            else:
                return "WAIT"
        else:
            return None

    def send_order(self, side, max_retry=3):
        """APIで注文を送信（ダミー例）"""
        print(f"Send order: {side} {self.order_size}")
        # 実際のAPI送信処理をここに記述
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        method    = 'POST'
        endPoint  = 'https://forex-api.coin.z.com/private'
        path      = '/v1/order'
        reqBody = {
            "symbol": "USD_JPY",
            "side": side,
            "size": self.order_size,
            "executionType":"MARKET",
        }

        text = timestamp + method + path + json.dumps(reqBody)
        sign = hmac.new(bytes(self.secret_key.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()

        headers = {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign
        }


        try:
            for retry in range(max_retry):
                res = requests.post(endPoint + path, headers=headers, data=json.dumps(reqBody))
                response_string = json.dumps(res.json(), indent=2)
                # 文字列の 'dump' をJSONとしてパースし、Pythonの辞書にする
                dump_dict = json.loads(response_string) # ここで変数名を dump_dict に変更しました
                # dump_dict は辞書なので、get() メソッドが使える
                status = dump_dict.get("status")
                if status == 0:
                    response_price_str = dump_dict.get("data")[0].get("price")
                    response_time_str = dump_dict.get("data")[0].get("timestamp")
                    response_time_str = datetime.fromisoformat(response_time_str.replace('Z', '+00:00'))
                    response_time_str = response_time_str.replace(microsecond=0)
                    self.position_time = response_time_str
                    print(f"Order sent at {response_time_str}")
                    print(f"Order price at {response_price_str}")
                    break
                else:
                    print(f"close_order retry {retry+1}/{max_retry} (status={status})")
                    time.sleep(2)  # 少し待ってリトライ
        except Exception as e:
            print(f"send_orderでエラーが発生しました: {e}")
        # ...

    def close_position(self, max_retry=3):
        """ポジションをクローズ（ダミー例）"""
        print("Close position")
        # 実際のAPI送信処理をここに記述
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        method    = 'POST'
        endPoint  = 'https://forex-api.coin.z.com/private'
        path      = '/v1/closeOrder'
        reqBody = {
            "symbol": "USD_JPY",
            "side": self.close_side,
            "executionType": "MARKET",
            "settlePosition": [
                {
                    "positionId": self.position_id,
                    "size": self.order_size
                }
            ]
        }

        text = timestamp + method + path + json.dumps(reqBody)
        sign = hmac.new(bytes(self.secret_key.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()

        headers = {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign
        }


        try:
            for retry in range(max_retry):
                res = requests.post(endPoint + path, headers=headers, data=json.dumps(reqBody))
                response_string = json.dumps(res.json(), indent=2)
                # 文字列の 'dump' をJSONとしてパースし、Pythonの辞書にする
                dump_dict = json.loads(response_string) # ここで変数名を dump_dict に変更しました
                status = dump_dict.get("status")
                if status == 0:
                    # dump_dict は辞書なので、get() メソッドが使える
                    response_price_str = dump_dict.get("data")[0].get("price")
                    response_time_str = dump_dict.get("data")[0].get("timestamp")
                    response_time_str = datetime.fromisoformat(response_time_str.replace('Z', '+00:00'))
                    response_time_str = response_time_str.replace(microsecond=0)
                    print(f"Close sent at {response_time_str}")
                    print(f"Close price at {response_price_str}")
                    break
                else:
                    print(f"close_order retry {retry+1}/{max_retry} (status={status})")
                    time.sleep(2)  # 少し待ってリトライ

        except Exception as e:
            print(f"send_closeでエラーが発生しました: {e}")
        # ...

    def open_positions(self):
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        method    = 'GET'
        endPoint  = 'https://forex-api.coin.z.com/private'
        path      = '/v1/openPositions'

        text = timestamp + method + path
        sign = hmac.new(bytes(self.secret_key.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
        parameters = {
            "symbol": "USD_JPY",
            "count": 10
        }

        headers = {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign
        }

        res = requests.get(endPoint + path, headers=headers, params=parameters)
        response_string = json.dumps(res.json(), indent=2)

        try:
            # 文字列の 'dump' をJSONとしてパースし、Pythonの辞書にする
            dump_dict = json.loads(response_string) # ここで変数名を dump_dict に変更しました
            position_list = dump_dict.get("data", {}).get("list", [])
            for pos in position_list:
                response_time_str = pos.get("timestamp")
                response_time = datetime.fromisoformat(response_time_str.replace('Z', '+00:00'))
                response_time = response_time.replace(microsecond=0)
                if response_time == self.position_time:
                    response_dt = pos.get("positionId")
                    self.position_id = response_dt
                    print(f"Found position ID: {self.position_id} for time {self.position_time}")
                    break
                
        except Exception as e:
            print(f"open_positionsでエラーが発生しました: {e}")
            # エラー時もプログラムが止まらないようにする

    def debug_open_positions(self):
        self.position_id = 12345
