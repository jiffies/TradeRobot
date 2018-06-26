# -*- coding: utf-8 -*-
from sqlalchemy import func

from db import DBSession
from model import Order


def save_order(order_data):
    order = Order(
        order_id=order_data.get("id"),
        side=order_data.get("side"),
        state=order_data.get("state"),
        price=float(order_data.get("price")),
        symbol=order_data.get("symbol"),
        amount=float(order_data.get("amount")),
        filled_amount=float(order_data.get("filled_amount")),
        fill_fees=float(order_data.get("fill_fees"))
    )
    with DBSession() as session:
        session.add(order)


def get_fees(symbol, side, start, end):
    with DBSession() as session:
        query = session.query(func.sum(Order.fill_fees)). \
            filter(Order.symbol == symbol). \
            filter(Order.side == side)
        if start and end:
            query = query.filter(Order.created_at >= start,
                                 Order.created_at < end)
        return float(query.scalar())