# coding=utf8
#
# Insight Minr Active Spider Client Node
# CopyRight BestMiner Inc.
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
from observer.platform.taobao.utils import getAgent
from observer.platform.taobao.config import SUFFIX
from observer.node.client import ClientServiceBase
from observer import log


class NodeService(ClientServiceBase):
    ''' client节点 '''

    servicename = 'observer.taobao.active_spider'

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
            reqid, tid = yield self.callController('nextRequest', 'extract')
            log.info('Got tid %s from server' % tid)

            try:
                result = yield self.search(agent, tid)
                log.debug('Got data %s' % repr(result))
            except InfiniteLoginError:
                log.exception()
                yield self.callController("fail", tid=tid)
                result = None
                needbreak = True
            except:
                log.exception()
                result = None
            self.callController('sendResult', reqid, tid, result)
            if needbreak:
                break


    @inlineCallbacks
    def getContent(self, agent, uid, token):
        ''' get the target webpage '''
        url = "%s%s" % (uid, SUFFIX)
        log.debug('Getting data with url: %s' % url)
        result = yield request(agent, url)
        returnValue(result)

    @inlineCallbacks
    def search(self, agent, tid, token):
        ''' 获取商铺信息列表 '''
        result = None
        try:
            data = yield self.getContent(agent, tid, token)
            result = json.loads(data).get('ids')
        except Exception as msg:
            log.debug("Got Something Wrong with tid: %s Error: %s" % (tid, repr(msg)))

        returnValue(json.dumps(result))
