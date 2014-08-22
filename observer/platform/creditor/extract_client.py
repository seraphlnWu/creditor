# coding=utf8
#
# Active Spider Client Node
# CopyRight seraphln.
#

'''
    从controller节点获取任务数据
'''

import os
import json
import time
import socket

from twisted.internet.defer import inlineCallbacks, returnValue

from observer.utils.http import request, TimedAgentPool, InfiniteLoginError
from observer.utils import wait
from observer.platform.creditor.utils import getAgent
from observer.node.client import ClientServiceBase
from observer.lib import log


class NodeService(ClientServiceBase):
    ''' client节点 '''

    servicename = 'observer.creditor.active_spider'

    def __init__(self, *args, **kwargs):
        ''' '''

        ClientServiceBase.__init__(self, *args, **kwargs)
        cfg = kwargs['cfg']
        self.name = socket.gethostname() + cfg.prefix    # node name

        self.proxy = cfg.http_proxy     # not used
        self.user_agent = cfg.http_agent
        self.max_agent = cfg.max_agent
        self.agent_pool = TimedAgentPool()
        self.last_clear = 0
        self.ready = True

    def addAgent(self, seq):
        ''' 添加一个新的agent到agent_pool '''
        agent = getAgent(self.proxy, self.user_agent)
        agent.remove = False
        agent.seq = seq
        self.agent_pool.initAgent(agent)
        self.searchLoop(agent)

    @inlineCallbacks
    def startService(self):
        ''' start the fetch service '''
        os.environ['TZ'] = 'PRC'
        time.tzset()
        yield ClientServiceBase.startService(self)
        self.fillAgents()

    @inlineCallbacks
    def fillAgents(self):
        ''' '''
        while 1:
            seq = 0
            while len(self.agent_pool.agents) < self.max_agent:
                seq += 1
                self.addAgent(seq)
            yield wait(10.)

    @inlineCallbacks
    def searchLoop(self, agent):
        ''' '''
        needbreak = False
        while 1:
            if agent.remove:
                self.agent_pool.removeAgent(agent)
                break
            reqid, url = yield self.callController('nextRequest', 'extract')
            log.info('Got url %s from server' % url)

            try:
                result = yield self.search(agent, url)
                log.debug('Got data %s' % repr(result))
            except InfiniteLoginError:
                log.exception()
                yield self.callController("fail", url=url)
                result = None
                needbreak = True
            except:
                log.exception()
                result = None
            self.callController('sendResult', reqid, url, result)
            if needbreak:
                break


    @inlineCallbacks
    def getContent(self, agent, url):
        ''' get the target webpage '''
        #url = "%s%s" % (uid, SUFFIX)
        log.debug('Getting data with url: %s' % url)
        result = yield request(agent, url)
        returnValue(result)

    @inlineCallbacks
    def search(self, agent, url):
        ''' 获取商铺信息列表 '''
        result = None
        try:
            data = yield self.getContent(agent, url)
            import ipdb;ipdb.set_trace()
            result = json.loads(data).get('ids')
        except Exception as msg:
            log.debug("Got Something Wrong with url: %s Error: %s" % (url, repr(msg)))

        returnValue(json.dumps(result))
