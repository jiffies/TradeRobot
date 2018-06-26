# -*- coding: utf-8 -*-
class FcoinError(Exception):
    pass


class InsufficientAccountError(FcoinError):
    code = 1016


class RequestLimitError(FcoinError):
    code = 429