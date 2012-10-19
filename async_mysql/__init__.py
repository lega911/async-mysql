# coding: utf8
'''

Connector to mysql or sphinxsearch with threadpool for web-tornado
    Oleg Nechaev <lega911@gmail.com>

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
'''

import threading
import MySQLdb
import Queue
import tornado.ioloop
from tornado import gen
from functools import partial
import time

class AsyncMysql():
    def __init__(self, pool_size=10, host='127.0.0.1', port=3306, db=None, user=None, password=None, ioloop=None, max_idle_time=6*3600):
        self.max_idle_time = max_idle_time
        self._threads = []
        self._working = True
        self._tasks = Queue.Queue()
        self.ioloop = ioloop
        # connection dict
        self._connection = cn = {}
        cn['host'] = host
        cn['port'] = port
        if db: cn['db'] = db
        if user: cn['user'] = user
        if password: cn['passwd'] = password
        # create threads
        for i in xrange(pool_size):
            t = Worker(self)
            t.start()
            self._threads.append(t)
    def stop(self):
        self._working = False
        self._tasks.put(['stop'])
        map(lambda t: t.join(), self._threads)
    def execute(self, query, argv=None, callback=None):
        assert callback
        self._tasks.put(['execute', query, argv, callback])
    def query(self, query, argv=None, callback=None):
        assert callback
        self._tasks.put(['query', query, argv, callback])
    def texecute(self, query, argv=None):
        return gen.Task(self.execute, query, argv)
    def tquery(self, query, argv=None):
        return gen.Task(self.query, query, argv)
    def send_result(self, task, result, error):
        callback = partial(task[3], (result, error))
        ioloop = self.ioloop or tornado.ioloop.IOLoop.instance()
        ioloop.add_callback(callback)

class Worker(threading.Thread):
    def __init__(self, cnt):
        self._controller = cnt
        self._db = None
        super(Worker, self).__init__()
        self._time_for_reconnect = time.time() + cnt.max_idle_time
    def get_cursor(self):
        # need reconnect?
        cnt = self._controller
        t = time.time()
        if t > self._time_for_reconnect:
            self._time_for_reconnect = time.time() + cnt.max_idle_time
            if self._db:
                self._db.close()
        elif self._db:
            return self._db.cursor()
        self._db = MySQLdb.connect(use_unicode=True, charset='utf8', **self._controller._connection)
        self._db.autocommit(True)
        return self._db.cursor()
    def close_db(self):
        if self._db:
            self._db.close()
            self._db = None
    def run(self):
        cnt = self._controller
        
        while cnt._working:
            result = None
            error = None
            cursor = None
            try:
                task = cnt._tasks.get(True)
                command = task[0]
                if command == 'stop':
                    cnt._tasks.put(['stop'])
                    break
                
                query = task[1]
                argv = task[2] or []
                
                cursor = self.get_cursor()
                if command == 'query':
                    cursor.execute(query, argv)
                    result = cursor.fetchall()
                else:
                    cursor.execute(query, argv)
                
            except Exception as e:
                error = e
            finally:
                if cursor: cursor.close()
            
            cnt.send_result(task, result, error)
        self.close_db()
