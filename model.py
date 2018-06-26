# -*- coding: utf-8 -*-
from sqlalchemy import (
    Column, String, Integer, BigInteger, Numeric, DateTime,
    func
)

from db import Base, BaseMixin, Session


class Order(Base, BaseMixin):
    __tablename__ = 'order'

    id = Column('id', Integer, primary_key=True)
    symbol = Column(String, default='')
    order_id = Column(String, default='')
    side = Column(String, default='')
    state = Column(String, default='')
    price = Column(Numeric(13, 10), default=0.0000000000)
    amount = Column(Numeric(13, 10), default=0.0000000000)
    filled_amount = Column(Numeric(13, 10), default=0.0000000000)
    fill_fees = Column(Numeric(13, 10), default=0.0000000000)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
