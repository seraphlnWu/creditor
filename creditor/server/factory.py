# coding=utf8

from twisted.internet import protocol

from zope.interface import Interface, implements
from observer.server.protocol import APIServerProtocol


class IAPIFactory(Interface):
    ''' '''

    def remoteCall(method, *args, **kwargs):
        ''' return a deferred returning a string. '''
        pass

    def buildProtocol(addr):
        ''' return a protocol returning a string. '''
        pass

    def closeConnection(connectionId):
        ''' called when the connection with connectionId was lost '''
        pass


class APIFactoryFromService(protocol.ServerFactory):
    ''' '''

    implements(IAPIFactory)

    protocol = APIServerProtocol

    def __init__(self, service):
        ''' '''
        self.service = service
        self.seq = 0

    def remoteCall(self, conn_id, method, *args, **kwargs):
        ''' '''
        if method is None:
            return defer.succeed([])

        m = getattr(self.service, method.encode("utf-8"))
        return m(conn_id, *args, **kwargs)

    def buildProtocol(self, addr):
        ''' '''
        p = protocol.ServerFactory.buildProtocol(self, addr)
        p.conn_id = self.service.new_connection()

        return p

    def closeConnection(self, conn_id):
        ''' '''
        self.service.close_connection(conn_id)
