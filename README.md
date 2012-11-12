async-mysql
===========

async connector to mysql and sphinx-search for tornado, it uses thread pool.

Excample:
===========

import tornado.ioloop
from tornado import gen
from async_mysql import AsyncMysql

ioloop = tornado.ioloop.IOLoop.instance()

db = AsyncMysql(host='127.0.0.1', port=3307, db='loveit_rt', pool_size=5)

@gen.engine
def go():
    result, error = yield db.tquery('select * from loveit_rt limit %s, %s', [0,5])
    print result, error
    
    ioloop.stop()
    db.stop()

ioloop.add_callback(go)
ioloop.start()

