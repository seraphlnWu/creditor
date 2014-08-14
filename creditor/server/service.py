# coding=utf8

from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from twisted.application import service
from functools import wraps


class APIServiceBase(service.Service):
    ''' '''

    def __init__(self):
        ''' '''
        self.cursors = {}
        self.connections = {}
        self.next_cursorid = 1
        self.next_connectionid = 1

    def new_connection(self):
        ''' '''
        connid = self.next_connectionid
        self.next_connectionid += 1
        self.connections[connid] = set()
        return connid

    def close_connection(self, conn_id):
        ''' '''
        if conn_id in self.connections:
            for curid in self.connections[conn_id]:
                if curid in self.cursors:
                    del self.cursors[curid]
            del self.connections[conn_id]

    def cmd_ping(self, conn_id):
        ''' '''
        return succeed(None)

    def cmd_close_cursors(self, conn_id, cursors):
        ''' '''
        conn_cur = self.connections.get(conn_id, set())
        for curid in cursors:
            if curid in self.cursors:
                del self.cursors[curid]
            conn_cur.discard(curid)
        return succeed(None)

    def cmd_quit(self, conn_id):
        ''' '''
        return succeed(None)

    def cmd_cursorid(self, conn_id):
        ''' '''
        curid = self.next_cursorid
        self.next_cursorid += 1
        self.cursors[curid] = []
        self.connections.get(conn_id, set()).add(curid)
        return succeed({'cursor_id': curid})

    def cmd_close_cursor(self, conn_id, cursorid):
        ''' '''
        if cursorid in self.cursors:
            del self.cursors[cursorid]

        self.connections.get(conn_id, set()).discard(cursorid)
        return succeed(None)

    def proc_request(self, conn_id, name, *args, **kwargs):
        ''' '''
        raise NotImplementedError("You should implement this function")

    def __getattr__(self, name):
        ''' '''
        if name.startswith('_'):
            raise AttributeError("")

        @wraps(self.proc_request)
        def new_func(conn_id, *args, **kwargs):
            return self.proc_request(conn_id, name, *args, **kwargs)

        return new_func


class APIServiceMain(APIServiceBase):
    ''' '''

    def __init__(self, mainnode):
        ''' '''
        APIServiceBase.__init__(self)
        self.mainnode = mainnode

    @inlineCallbacks
    def proc_request(self, conn_id, name, *args, **kwargs):
        ''' '''
        print self.mainnode
        rv = yield self.mainnode.request(name, *args, **kwargs)
        returnValue(rv)
