# -*- coding: utf-8 -*-
import hmac
import hashlib
import random

import requests
import sys
import time
import base64
import json
from collections import OrderedDict

from exc import InsufficientAccountError


class Fcoin():
    def __init__(self, base_url='https://api.fcoin.com/v2/', use_proxy=False):
        self.base_url = base_url
        # self.proxy_pool = requests.get(
        #     "http://127.0.0.1:8000?protocol=1").json()
        self.proxy_pool = [{"port": "24573", "ip": "49.85.5.253"},
                           {"port": "47426", "ip": "121.224.119.187"},
                           {"port": "31721", "ip": "114.101.133.22"},
                           {"port": "24549", "ip": "1.197.59.64"},
                           {"port": "36120", "ip": "171.14.210.223"},
                           {"port": "36581", "ip": "182.122.47.82"},
                           {"port": "34424", "ip": "115.203.180.154"},
                           {"port": "36267", "ip": "125.112.204.149"},
                           {"port": "40131", "ip": "221.14.120.216"},
                           {"port": "29490", "ip": "114.99.24.38"},
                           {"port": "37900", "ip": "122.230.245.23"},
                           {"port": "35282", "ip": "180.116.215.200"},
                           {"port": "46363", "ip": "223.241.78.250"},
                           {"port": "29859", "ip": "219.131.226.29"},
                           {"port": "37915", "ip": "115.59.178.167"},
                           {"port": "35803", "ip": "182.84.78.237"},
                           {"port": "34381", "ip": "223.240.249.4"},
                           {"port": "30461", "ip": "122.246.48.164"},
                           {"port": "42001", "ip": "122.246.55.197"},
                           {"port": "33339", "ip": "114.99.4.209"}]
        self.proxy_index = 0
        self.use_proxy = use_proxy

    def sign_proxy(self):
        secret = "0d1236e893b6513d64f84965c6912a36"
        orderno = "DT201806182150556uEO6Wxs"
        timestamp = int(time.time())
        txt = "orderno={},secret={},timestamp={}".format(orderno, secret,
                                                         timestamp)
        txt = txt.encode()
        md5_string = hashlib.md5(txt).hexdigest()
        sign = md5_string.upper()
        auth = "sign=" + sign + "&" + "orderno=" + orderno + "&" + \
               "timestamp=" + str(timestamp)
        # print(auth)
        return auth

    def auth(self, key_pairs):
        self.key_pairs = [
            {"key": bytes(pair[0], 'utf-8'), "secret": bytes(pair[1], 'utf-8')}
            for pair in key_pairs]
        self.key_index = 0

    def refresh_proxy_pool(self):
        self.proxy_pool = requests.get(
            "http://127.0.0.1:8000?protocol=1").json()
        self.proxy_index = random.randint(0, len(self.proxy_pool))

    def choose_proxy(self):
        if not self.use_proxy:
            return {}
        proxy = self.proxy_pool[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxy_pool)

        proxies = {
            "https": "https://{}:{}".format(proxy["ip"], proxy["port"])
        }
        return proxies

    def public_request(self, method, api_url, **payload):
        """request public url"""
        r_url = self.base_url + api_url

        try:
            r = requests.request(method, r_url, params=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        if r.status_code == 200:
            return r.json()

    def choose_key(self):
        pair = self.key_pairs[self.key_index]
        self.key_index = (self.key_index + 1) % len(self.key_pairs)
        return pair

    def get_signed(self, sig_str, secret):
        """signed params use sha512"""
        try:
            self.key_pairs
        except AttributeError:
            raise Exception('请先登录！')
        sig_str = base64.b64encode(sig_str)
        signature = base64.b64encode(
            hmac.new(secret, sig_str, digestmod=hashlib.sha1).digest())
        return signature

    def signed_request(self, method, api_url, **payload):
        """request a signed url"""

        param = ''
        if payload:
            sort_pay = sorted(payload.items())
            # sort_pay.sort()
            for k in sort_pay:
                param += '&' + str(k[0]) + '=' + str(k[1])
            param = param.lstrip('&')

        account_insufficient_error_count= 0

        while 1:
            timestamp = str(int(time.time() * 1000))
            full_url = self.base_url + api_url

            if method == 'GET':
                if param:
                    full_url = full_url + '?' + param
                sig_str = method + full_url + timestamp
            elif method == 'POST':
                sig_str = method + full_url + timestamp + param

            pair = self.choose_key()
            # print("使用key{}".format(pair.get("key")))
            signature = self.get_signed(bytes(sig_str, 'utf-8'),
                                        pair.get("secret"))
            headers = {
                'FC-ACCESS-KEY': pair.get("key"),
                'FC-ACCESS-SIGNATURE': signature,
                'FC-ACCESS-TIMESTAMP': timestamp,
                "Proxy-Authorization": self.sign_proxy()
            }
            # proxies = self.choose_proxy()
            ip = "dynamic.xiongmaodaili.com"
            port = "8088"

            ip_port = ip + ":" + port
            if self.use_proxy:
                proxies = {"http": "http://" + ip_port,
                           "https": "https://" + ip_port}
                verify = False
            else:
                proxies = {}
                verify = True

            # print("使用代理: {}".format(proxies.get("https")))

            try:
                r = requests.request(method, full_url, headers=headers,
                                     json=payload, proxies=proxies, timeout=3,
                                     verify=verify, allow_redirects=False)

                r.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(err)
                print(r.text)
                status = r.json().get("status")
                # account balance insufficient
                if status == 1016:
                    account_insufficient_error_count += 1
                print("API限制，休息2秒")
                time.sleep(2)
                if account_insufficient_error_count == 10:
                    raise InsufficientAccountError()
            except (
                    requests.exceptions.Timeout,
                    requests.exceptions.ProxyError) as e:
                print(e)
            else:
                break

        if r.status_code == 200 and self.effect_return(r.json()):
            return r.json()
        else:
            raise Exception("{}请求返回异常:{}".format(api_url, r.__dict__))

    def effect_return(self, result):
        return result.get("status") == 0

    def get_server_time(self):
        """Get server time"""
        return self.public_request('GET', '/public/server-time')['data']

    def get_currencies(self):
        """get all currencies"""
        return self.public_request('GET', '/public/currencies')['data']

    def get_symbols(self):
        """get all symbols"""
        return self.public_request('GET', '/public/symbols')['data']

    def get_market_ticker(self, symbol):
        """get market ticker"""
        return self.public_request('GET', 'market/ticker/{symbol}'.format(
            symbol=symbol))

    def get_market_depth(self, level, symbol):
        """get market depth"""
        return self.public_request('GET',
                                   'market/depth/{level}/{symbol}'.format(
                                       level=level, symbol=symbol))

    def get_trades(self, symbol):
        """get detail trade"""
        return self.public_request('GET', 'market/trades/{symbol}'.format(
            symbol=symbol))

    def get_balance(self):
        """get user balance"""
        return self.signed_request('GET', 'accounts/balance')

    def list_orders(self, **payload):
        """get orders"""
        return self.signed_request('GET', 'orders', **payload)

    def create_order(self, **payload):
        """create order"""
        return self.signed_request('POST', 'orders', **payload)

    def buy(self, symbol, price, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='buy', type='limit',
                                 price=str(price), amount=amount)

    def sell(self, symbol, price, amount):
        """sell someting"""
        return self.create_order(symbol=symbol, side='sell', type='limit',
                                 price=str(price), amount=amount)

    def get_order(self, order_id):
        """get specfic order"""
        return self.signed_request('GET', 'orders/{order_id}'.format(
            order_id=order_id))

    def cancel_order(self, order_id):
        """cancel specfic order"""
        return self.signed_request('POST',
                                   'orders/{order_id}/submit-cancel'.format(
                                       order_id=order_id))

    def order_result(self, order_id):
        """check order result"""
        return self.signed_request('GET',
                                   'orders/{order_id}/match-results'.format(
                                       order_id=order_id))

    def get_candle(self, resolution, symbol, **payload):
        """get candle data"""
        return self.public_request('GET',
                                   'market/candles/{resolution}/{'
                                   'symbol}'.format(
                                       resolution=resolution, symbol=symbol),
                                   **payload)
