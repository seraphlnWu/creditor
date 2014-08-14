# coding=utf8

'''
    节点基类

    包含向主节点注册节点，请求任务等操作
'''

import sys

import socket
import twisted.spread.banana
from twisted.spread import pb
from twisted.internet.defer import (
    inlineCallbacks,
    returnValue,
    Deferred,
    succeed,
)

from twisted.internet import reactor
from twisted.application import service

from observer.utils import wait
from observer import log
from observer.utils import TLSClientContextFactory  #FIXME not used now!
from observer.utils.twisted_utils import ReconnectingPBClientFactory
from observer.node import BANANA_SIZE_LIMIT


twisted.spread.banana.SIZE_LIMIT = BANANA_SIZE_LIMIT


class PBClientFactory(ReconnectingPBClientFactory):
    ''' '''

    def __init__(self, rootCallback):
        ''' '''
        ReconnectingPBClientFactory.__init__(self)
        self._rootCallback = rootCallback
        self.maxDelay = 60

    def gotRootObject(self, root):  # called by connect
        ''' '''
        self._rootCallback(root)


class ClientServiceBase(service.Service):
    '''
        1. 向central节点注册
        2. connectController连接控制节点并启动超时检查
        3. 如果超时那么回到1
        4. gotController取得控制节点后调用registerController向控制节点注册本节点
        5. 如果注册失败回到1
        6. 完成注册
    '''

    controller_name = 'observer.sina.weibo.active_spider'
    servicename = None
    version_major = 1
    version_minor = 0

    def __init__(self, *args, **kwargs):
        ''' '''
        cfg = kwargs['cfg']

        self.cfg = cfg

        self.controller_timeout = cfg.controller_timeout
        self.count = 0

        self.node = None            #FIXME I need give the node as a good name
        self.port = cfg.host_port   # not used
        self.central_node = None

        self.host_name = cfg.host_name
        self.clientid = None
        self.controller = None
        self.controllerTimer = None
        self.controller_factory = None
        self.ready = False
        self._requests = []

        self.controllerip = 'localhost'
        self.controllerport = 6001

        self.max_slots = 10
        self.clients = {}

    def cancelControllerTimeout(self):
        ''' '''
        if self.controllerTimer is not None:
            self.controllerTimer.cancel()
            self.controllerTimer = None

    def _clearLocal(self):
        ''' '''
        self.central_node = None
        self.clientid = None
        self.controller = None

    @inlineCallbacks
    def registerController(self, controllernode):
        '''
            register to controller. 

            first, call *register* in controller,
            then:
            if the procedure was running successfully,
                we will return the message in data.
            if there happened a exception,
                we will return a None.
        '''
        message = None
        try:
            data = yield controllernode.callRemote(
                'register',
                self.servicename,
                self.version_major,
                self.version_minor,
                self.host_name,
                self.node,
            )
            message, clientid = data
            self.clientid = clientid
            self.controller = controllernode
            self.ready = True
        except:
            log.error("Error when register to controller.")
            log.exception()
            self._clearController()

        returnValue(message)

    def _clearController(self):
        ''' '''
        self.clientid = None
        self.controller = None

    @inlineCallbacks
    def unregister(self):
        ''' '''
        try:
            yield self.controller.callRemote('unregister', self.clientid)
        except:
            pass
        self._clearController()

    @inlineCallbacks
    def callController(self, methodname, *args, **kwargs):
        ''' '''
        while True:
            controller = self.getController()
            try:
                result = yield controller.result.callRemote(
                    methodname,
                    *args,
                    **kwargs
                )
                returnValue(result)
            except pb.DeadReferenceError:
                self._clearController()
                continue
            except pb.PBConnectionLost:
                self._clearController()
                continue
            except Exception as msg:
                pass

    def controllerUsers(self, *args, **kwargs):
        ''' get users from controller '''
        return self.callController('users', self.clientid)

    def controllerRequest(self, methodname, *args, **kwargs):
        ''' '''
        return self.callController(
            'request',
            self.clientid,
            methodname,
            *args,
            **kwargs
        )

    def controllerPull(self):
        ''' '''
        return self.callController('pull', self.clientid)

    def controllerFail(self, methodname, *args, **kwargs):
        return self.callController(methodname, *args, **kwargs)

    def controllerPush(self, methodname, *args, **kwargs):
        ''' '''
        return self.callController(methodname, *args, **kwargs)

    def controllerReturn(self, requestid, result):
        ''' '''
        return self.callController('return', self.clientid, requestid, result)

    @inlineCallbacks
    def procLoop(self):
        ''' main function '''
        while True:
            req_id, method, args, kwargs = yield self.controllerPull()
            try:
                m = getattr(self, method)
                result = yield m(*args, **kwargs)
                yield self.controllerReturn(req_id, {'result': result})
            except:
                log.exception()
                exctype, value, traceback = sys.exc_info()
                yield self.controllerReturn(
                    req_id,
                    {'error': {
                        'type': exctype,
                        'value': value,
                        'traceback': traceback,
                    }},
                )

    @inlineCallbacks
    def gotController(self, root):
        ''' register a client to controller '''

        # first clear local environment
        # then register to controller
        self._clearController()
        message = yield self.registerController(root)

        # if the message is succeed, pop a request record, and active it.
        # else, call disconnect to the controller.
        if message == 'succeed':
            while self._requests:
                d = self._requests.pop(0)
                d.callback(root)
        else:
            log.error("Got error when register to controller " + str(message))
            self.controller_factory.disconnect()

    def connectController(self):
        ''' '''
        self.controller_factory = PBClientFactory(self.gotController)
        reactor.connectTCP(
            self.cfg.main_node_host,
            5036,
            self.controller_factory,
        )

        root = yield self.getController()
        returnValue(root)

    def getController(self):
        '''
            if there is a controller, return it.
            else: return a new Deferred instance.
        '''
        if self.controller is not None:
            return succeed(self.controller)
        else:
            d = Deferred()
            self._requests.append(d)
            return d

    @inlineCallbacks
    def registerCentralNode(self, centralnode):
        ''' '''
        try:
            data = yield centralnode.callRemote(
                'register',
                self.servicename,
                socket.gethostname(),
                self.node,
            )
            (clientid, (controllerip, controllerport),  message) = data
            self.clientid = clientid
            self.controllerip = controllerip
            self.controllerport = controllerport
            self.central_node = centralnode

        except Exception as msg:
            log.error("Error when register to central.")
            log.exception()
            self._clearLocal()
            returnValue(None)
            return

        returnValue(message)

    @inlineCallbacks
    def gotCentralNode(self, root):
        ''' '''
        self._clearController()

        message = yield self.registerCentralNode(root)
        if message == 'succeed':
            if self.controller_name is None:
                self.controller = self.central_node
            else:
                self.connectController()
        elif message is not None:
            log.error("Error when register to central node " + message)
            self.central_factory.disconnect()

    @inlineCallbacks
    def connectCentralNode(self):
        ''' '''
        self.central_factory = PBClientFactory(self.gotController)
        '''
        reactor.connectTCP(
            self.cfg.main_node_host,
            self.cfg.main_node_port,
            self.central_factory,
        )
        '''
        reactor.connectTCP(
            self.cfg.main_node_host,
            self.cfg.main_node_port,
            self.central_factory,
        )

        root = yield self.getController()
        returnValue(root)

    @inlineCallbacks
    def startService(self):
        ''' '''
        # why root?
        #root = yield self.connectController()
        root = yield self.connectCentralNode()
        #self.procLoop()
        '''
        for i in range(self.max_slots):
            self.procLoop()
        '''

    @inlineCallbacks
    def stopService(self):
        ''' '''
        if self.controller is not None:
            yield self.unregister()


class Client(pb.Referenceable):
    ''' '''

    def __init__(self, service):
        ''' '''
        self.service = service
        service.node = self

    def __getattr__(self, name):
        ''' '''
        if name.startswith('remote_'):
            return getattr(self.service, name)
        raise AttributeError(
            "'%s' has no attribute '%s'" % (self.__class__.__name__, name)
        )
