# -*- coding: utf-8 -*-
import sqlite3
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager

Base = declarative_base()
engine = create_engine("mysql+pymysql://root:root@localhost:3306/fcoin",
                       encoding="utf-8")
Session = sessionmaker(bind=engine)


@contextmanager
def DBSession():
    try:
        session = Session()
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class BaseMixin(object):
    @classmethod
    def get(cls, pk):
        """Get an instance from db by primary key.
        Returns `None` if not found.
        """
        return DBSession().query(cls).get(pk)

    @classmethod
    def get_or_raise(cls, pk, exc=Exception("数据库错误")):
        """Get an instance from db by primary key.
        Returns `None` if not found.
        """
        row = DBSession().query(cls).get(pk)
        if row is None:
            raise Exception("{}记录不存在".format(cls.__name__))
        return row

    @classmethod
    def mget(cls, pks):
        """Get multiple instances from db by a chunk of primary keys.
        """
        if not pks:
            return []
        return DBSession().query(cls) \
            .filter(cls.id.in_(pks)) \
            .all()

    @classmethod
    def add(cls, *args, **kwargs):
        """Create a new instance from arguments, add it to current session and
        flush to db end.
        """
        session = DBSession()
        ins = cls(*args, **kwargs)
        session.add(ins)
        session.flush()  # important
        return ins

    @classmethod
    def add_and_expunge(cls, *args, **kwargs):
        """Call `add()` and then expunge this instance from session.
        """
        ins = cls.add(*args, **kwargs)
        return ins.expunge()

    @classmethod
    def delete(cls, pk):
        """Delete a instance from db by primary key.
        Returns `False` on not found, otherwise `True`.
        """
        ins = cls.get(pk)
        if ins is None:
            return False
        DBSession().delete(ins)
        return True

    @classmethod
    def mget_with_filter(cls, **kargs):
        query = DBSession().query(cls)
        for k, v in kargs.items():
            query = query.filter(getattr(cls, k) == v)
        return query.all()
