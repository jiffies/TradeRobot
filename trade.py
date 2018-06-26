# -*- coding: utf-8 -*-
import time

import datetime
import sqlalchemy

from exc import InsufficientAccountError
from fcoin import Fcoin
import os

from handle import save_order, get_fees
from helper import float_to_str


class FcoinRobot():
    def __init__(self, client, base_currency, quote_currency, unit,
                 wait_time=15, decimal=2, limit=True):
        self.client = client
        self.symbol = base_currency + quote_currency
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_balance = 0.0
        self.quote_balance = 0.0
        self.unit = unit
        self.decimal = decimal

        self.fill_fees = 0.0
        self.get_balance()
        self.get_asset()
        self.wait_time = wait_time
        self.start_time = datetime.datetime.now()
        self.round = 0
        self.limit = limit

    def get_asset(self):
        self.price = self.get_trade_price()
        self.quote_unit = round(self.unit * self.price)
        self.asset = self.price * self.base_balance + self.quote_balance
        print("您的初始资产为:{} {}".format(self.asset, self.quote_currency))

    def get_balance(self):
        r = self.client.get_balance()

        for pair in r.get("data"):
            if pair.get("currency") == self.base_currency:
                self.base_balance = float(pair.get("available"))
            if pair.get("currency") == self.quote_currency:
                self.quote_balance = float(pair.get("available"))
        if not self.base_balance or not self.quote_balance:
            raise Exception("初始化账户失败!")
        print("当前{}账户可用余额:{}, 当前{}账户可用余额:{}".format(self.base_currency,
                                                    self.base_balance,
                                                    self.quote_currency,
                                                    self.quote_balance))

    def get_trade_price(self):
        r = self.client.get_market_ticker(self.symbol)

        data = r.get("data")
        current_price = data.get("ticker")[0]
        buy = data.get("ticker")[2]
        sell = data.get("ticker")[4]
        high24 = data.get("ticker")[7]
        self.price_protect(current_price, high24)
        best_price = (buy + sell) / 2
        print("24小时最高价为{}, 买一:{}, 卖一:{}, 当前价格为{}, 最佳价格为:{}".format(high24, buy,
                                                                   sell,
                                                                   current_price,
                                                                   best_price))

        return round(best_price, self.decimal)

    def refresh_unit(self):
        # self.base_balance -= self.unit * 0.001
        # print("{}账户余额: {}".format(self.base_currency, self.base_balance))
        if self.unit >= self.base_balance * 0.95:
            self.unit = round(self.base_balance * 0.9, 2)
            self.quote_unit = round(self.unit * self.price)
            print(
                "更新unit为{}, quote_unit为:{}".format(self.unit, self.quote_unit))

    def place_order(self, limit=True):
        if not limit:
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            sell = self.client.create_order(symbol=self.symbol, side="sell",
                                            type="market",
                                            amount=self.unit)
            print("{} {} 成功下市价卖单:{}, 数量:{}".format(self.round, time,
                                                   sell.get("data"),
                                                   self.unit))

            self.sleep(1)
            buy = self.client.create_order(symbol=self.symbol, side="buy",
                                           type="market",
                                           amount=self.quote_unit)
            print(
                "{} {} 成功下市价买单:{}, 数量:{}".format(self.round, time,
                                                 buy.get("data"),
                                                 self.quote_unit))

            self.buy_order_id = buy.get("data")
            self.finish_buy = False
            self.sell_order_id = sell.get("data")
            self.finish_sell = False
        else:
            price = float_to_str(self.get_trade_price())
            sell = self.client.create_order(symbol=self.symbol, side="sell",
                                            type="limit",
                                            price=price, amount=self.unit)
            print("成功下卖单:{}, 价格:{}, 数量:{}".format(sell.get("data"), price,
                                                  self.unit))
            self.sleep(1)
            buy = self.client.create_order(symbol=self.symbol, side="buy",
                                           type="limit",
                                           price=price, amount=self.unit)
            print(
                "成功下买单:{}, 价格:{}, 数量:{}".format(buy.get("data"), price,
                                                self.unit))

            self.buy_order_id = buy.get("data")
            self.finish_buy = False
            self.sell_order_id = sell.get("data")
            self.finish_sell = False

    def is_order_filled(self, order):
        return order.get("state") == "filled"

    def get_fill_fees(self):
        now = datetime.datetime.now()
        buy = get_fees(self.symbol, "buy", start=self.start_time, end=now)
        sell = get_fees(self.symbol, "sell", start=self.start_time, end=now)
        price = self.get_trade_price()
        total = price * buy + sell
        print("当前手续费总和: {}".format(total))

    def finish_order(self, data):
        try:
            save_order(data)
        except sqlalchemy.exc.IntegrityError:
            print("{} id冲突！订单: {}完成".format(self.round, data.get("id")))
            return
        if data.get("side") == "buy":
            self.finish_buy = True
        elif data.get("side") == "sell":
            self.finish_sell = True
        print("{} 订单: {}完成".format(self.round, data.get("id")))

    def order_complete(self):
        if not self.finish_buy:
            buy = self.client.get_order(self.buy_order_id)
            if self.is_order_filled(buy.get("data")):
                self.finish_order(buy.get("data"))
            else:
                print("{} 买单未完成".format(self.round))
        self.sleep(1)
        if not self.finish_sell:
            sell = self.client.get_order(self.sell_order_id)
            if self.is_order_filled(sell.get("data")):
                self.finish_order(sell.get("data"))
            else:
                print("{} 卖单未完成".format(self.round))

    def price_protect(self, current_price, high24):
        if current_price / high24 < 0.65:
            print("24小时最高价为{}, 当前价格为{}".format(high24, current_price))
            raise Exception("当前价格异常！请检查")

    def sleep(self, second):
        time.sleep(second)

    def start(self):
        if self.limit:
            while 1:
                if self.round % 20 == 0 and round != 0:
                    self.sleep(10)
                    self.get_balance()
                self.refresh_unit()
                try:
                    self.place_order(limit=self.limit)
                    start_time = time.time()
                    while not self.finish_sell or not self.finish_buy:
                        self.order_complete()
                        now = time.time()
                        # 如果10秒还有订单未成交，则撤销订单
                        if round(now - start_time) > 10:
                            if not self.finish_buy:
                                self.cancel_buy = False
                                self.client.cancel_order(self.buy_order_id)
                                print("取消{}买单".format(self.round))
                            if not self.finish_sell:
                                self.cancel_sell = False
                                self.client.cancel_order(self.sell_order_id)
                                print("取消{}卖单".format(self.round))
                            self.sleep(5)
                            break

                except InsufficientAccountError:
                    self.get_balance()
                    amount = round(self.quote_balance / 2)
                    self.client.create_order(side="buy", amount=amount,
                                             type="market", symbol=self.symbol)
                    print("{}不足，购买{} {}".format(self.base_currency, amount,
                                                self.quote_currency))
                    self.sleep(10)
                    self.get_balance()
                    self.refresh_unit()
                self.sleep(1)
                self.round += 1

        else:

            while 1:
                if self.round % 20 == 0 and round != 0:
                    self.sleep(10)
                    self.get_balance()
                self.refresh_unit()
                try:
                    self.place_order(limit=self.limit)
                except InsufficientAccountError:
                    self.get_balance()
                    amount = round(self.quote_balance * 0.9, 1)
                    self.client.create_order(side="buy", amount=amount,
                                             type="market", symbol=self.symbol)
                    print("{}不足，购买{} {}".format(self.base_currency, amount,
                                                self.quote_currency))
                    self.sleep(10)
                    self.get_balance()
                    self.refresh_unit()
                self.sleep(1)
                self.round += 1
                # while not self.finish_sell or not self.finish_buy:
                #     self.order_complete()


if __name__ == "__main__":
    fclient = Fcoin(use_proxy=False)

    key = os.environ.get("FCOIN_KEY")
    secret = os.environ.get("FCOIN_SECRET")
    fclient.auth([(key, secret)])
    robot = FcoinRobot(fclient, 'eth', 'usdt', unit=4, decimal=2, limit=False)
    robot.sleep(5)
    robot.start()
