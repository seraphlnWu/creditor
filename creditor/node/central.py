# coding=utf8

'''
    central node

    负责各个节点的认证，并把字节点分配到对应的控制节点上

    TODO: 使用protal/realm/avatar 完成证书的确认和身份认证
'''
import heapq
from uuid import uuid4

from twisted.spread import pb
from twisted.internet.defer import (
    inlineCallbacks,
    returnValue,
    Deferred,
    succeed,
)

from twisted.internet import defer, reactor
from twisted.application import service
import twisted.spread.banana

from observer.node import BANANA_SIZE_LIMIT
from observer import log


twisted.spread.banana.SIZE_LIMIT = BANANA_SIZE_LIMIT


class CentralService(service.Service):
    '''
        中心节点，任何一个节点都会先访问此节点完成注册。
        然后由中心节点分配到相应的controller节点。
    '''

    def __init__(self, cfg):
        ''' '''
        self.services = {}
        self.nodecontrollermapping = {}
        self.controller_versions = {}    # should configed in configs
        self.controllers = {}
        self.controller_monitor = None
        self.clients = {}

    def startService(self):
        ''' start the service '''
        self.monitorController()

    def stopService(self):
        ''' stop the service '''
        if self.controller_monitor is not None:
            self.controller_monitor.cancel()
            self.controller_monitor = None

    @inlineCallbacks
    def monitorController(self):
        '''
            监控所有的controller节点。

            TODO: 在监控节点添加各种的监控脚本，争取能体现在页面上 :)
        '''
        self.controller_monitor = None
        dl = []
        for controller in self.controllers.itervalues():
            d = controller['client'].callRemote('status')
            d.addCallbacks(
                self.gotControllerStatus,
                self.gotControllersError,
                (controller, ),
                None,
                (controller, ),
                None,
            )
            dl.append(d)
        if dl:
            yield defer.DeferredList(dl)
        self.controller_monitor = reactor.callLater(
            30.0,
            self.monitorController,
        )

    def gotControllerStatus(self, status, controller):
        ''' 正常监控controller的状态 '''
        count = status['count']
        if count != controller.count:
            self.updateControllerFromService(controller, count)

    def gotControllerError(self, failure, controller):
        ''' 监控controller状态出异常时的处理 '''
        failure.trap(pb.DeadReferenceError, pb.PBConnectionLost)
        self.unregisterController(controller['id'])

    def newClientId(self):
        ''' 生成一个新的唯一的uuid '''
        return uuid4().int

    def getService(self, name):
        ''' 获取name对应的controller集合信息 '''
        r = {}
        if name not in self.services:
            r = {
                'controllers': [],
                'defers': [],
            }

            self.services[name] = r
        else:
            r = self.services[name]

        return r

    def getController(self, name):
        '''
            获取一个名为name的主控节点，并把其计数+1。

            如果有多个，那么使用叶子节点最少的一个
        '''
        service = self.getService(name)
        controllers = service['controllers']
        if controllers:
            count, controllerid = heapq.heappop(controllers)
            heapq.heappush(controllers, (count+1, controllerid))
            controller = controllers[controllerid]
            controller['count'] += 1
            return succeed(controller)
        else:
            d = Deferred()
            service['defers'].append(d)
            return d

    @inlineCallbacks
    def registerClient2Controller(self, clientid, controllername):
        '''
            把叶子节点注册到对应的主控节点下面，并通知对应的主控节点

            TODO: 需要考虑是否在注册的时候添加认证
        '''
        while True:
            controller = yield self.getController(controllername)
            try:
                yield controller['client'].callRemote('preregister', clientid)
            except pb.DeadReferenceError:
                self.unregisterController(controller['id'])
            except pb.PBConnectionLost:
                self.unregisterController(controller['id'])
            else:
                returnValue(controller)
                return

    def registerController(
        self,
        servicename,
        nodename,
        version_major,
        version_minor,
        clientcount,
        port,
        client,
    ):
        ''' 注册控制节点 '''
        cid = str(self.newClientId())

        # 如果版本不匹配，结束注册
        if servicename in self.controller_versions:
            versions = self.controller_versions[servicename]
            if (version_major, version_minor) != versions:
                message = "Wrong versions: %s excepted: %s" % (
                    repr((version_major, version_minor)),
                    repr(versions),
                )
                log.error(message)
                return((None, (None, None), message))
        else:
            self.controller_versions[servicename] = (
                version_major,
                version_minor,
            )

        controllerinfo = {
            'id': cid,
            'service': servicename,
            'nodename': nodename,
            'client': client,
            'ip': client.broker.transport.getPeer().host,
            'count': clientcount,
            'port': port,
        }

        self.clients[cid] = controllerinfo
        self.controllers[cid] = controllerinfo
        count = 0
        service = self.getService(servicename)
        if service['defers']:
            count = clientcount + len(service['defers'])
            for d in service['defers']:
                d.callback(controllerinfo)
            heapq.heappush(service['controllers'], (count, cid))
            controllerinfo['count'] = count

        client.notifyOnDisconnect(lambda c: self.unregisterController(cid))
        log.info("Added controller: %s at: %s with id: %s" % (
            servicename,
            nodename,
            cid,
        ))
        return((cid, 'succeed'))

    @inlineCallbacks
    def register(self, controllername, nodename, client):
        '''
            注册节点。
            返回控制节点的ip和端口，请求节点需要连接控制节点完成注册。
        '''
        cid = self.newClientId()
        controller = yield self.registerClient2Controller(cid, controllername)
        controllerip = controller['ip']
        controllerport = controller['port']
        log.info("Added client at: %s with id: %s to: %s at: %s with id: %s" % (
            nodename,
            str(cid),
            controller['service'],
            controller['nodename'],
            str(controller['id'])),
        )
        returnValue((cid, (controllerip, controllerport), 'succeed'))

    def removeControllerFromService(self, controller):
        ''' '''
        controllerid = controller['id']
        service = self.getService(controller['service'])
        controllers = service['controllers']
        for i, controller in enumerate(controllers):
            if controller[1] == controllerid:
                del controllers[i]
                if not controllers:
                    del self.controller_versions[controller['service']]
                heapq.heapify(controllers)
                break
        else:
            log.warning("Removing controller from service with an unknown id: " + str(controllerid))

    def updateControllerFromService(self, controller, count):
        ''' '''
        controllerid = controller['id']
        service = self.getService(controller['service'])
        controllers = service['controllers']
        for i, controller in enumerate(controllers):
            if controller[1] == controllerid:
                controllers[i] = (count, controllerid)
                heapq.heapify(controllers)
                break
        else:
            log.warning("Updating controller from service with an unknown id: " + str(controllerid))

    def unregisterController(self, clientid):
        ''' '''
        if clientid not in self.controllers:
            log.warning("Unregister an unknown controller with id: " + str(clientid))
            return False
        controller = self.controllers[clientid]
        self.removeControllerFromService(controller)
        del self.clients[clientid]
        log.info("Removed controller: " + str(clientid))
        return True


class CentralNode(pb.Root):
    ''' '''

    def __init__(self, service):
        ''' '''
        self.service = service

    def remote_registerController(
        self,
        servicename,
        nodename,
        version_major,
        version_minor,
        clientcount,
        port,
        client,
    ):
        return self.service.registerController(
            servicename,
            nodename,
            version_major,
            version_minor,
            clientcount,
            port,
            client
        )

    def remote_register(self, controllername, nodename, client):
        ''' '''
        return self.service.register(controllername, nodename, client)

    def remote_unregisterController(self, clientid):
        ''' '''
        return self.service.unregisterController(clientid)
