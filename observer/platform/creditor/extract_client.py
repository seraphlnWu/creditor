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
import lxml.etree
from urllib2.urlparse import urljoin

from twisted.internet.defer import inlineCallbacks, returnValue

from observer.utils.http import request, TimedAgentPool, InfiniteLoginError
from observer.utils import wait
from observer.platform.creditor.utils import getAgent
from observer.node.client import ClientServiceBase
from observer.lib import log
from observer.lib.tasks import BaseTask


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
            result = None
            if agent.remove:
                self.agent_pool.removeAgent(agent)
                break

            reqid, task = yield self.callController('nextRequest', 'extract')
            log.info(repr(task))

            try:
                result = yield self.search(agent, task)
                log.debug('Got data %s' % repr(result))
            except InfiniteLoginError:
                log.exception()
                yield self.callController("fail", task=task)
                needbreak = True
            except:
                log.exception()
            self.callController('sendResult', reqid, task, json.dumps(result))
            if needbreak:
                break


    @inlineCallbacks
    def getContent(self, agent, task):
        ''' download the target page '''
        task = json.loads(task)
        tbody = task.tbody

        req_url = urljoin(tbody.get('prefix'), tbody.get('suffix'))
        url = req_url % (tbody.get('ccode'), tbody.get('page'))
        log.debug('Getting data with url: %s' % url)
        result = yield request(agent, url)
        returnValue(result)

    @staticmethod
    def parse_pages(el):
        ''' '''
        try:
            mmc = el.xpath("./div[@class='page_header clearfix']")[0]
            result = filter(lambda x: x.isdigit(), mmc.xpath('./div[@class="l_content"]/a/text()'))[-1]
        except IndexError:
            result = -1

        return result

    @staticmethod
    def parse_shop_url(el):
        try:
            href = el.xpath("./td/a/@href")[0]
        except IndexError:
            href = ""

        return href

    @staticmethod
    def parse_items(el):
        ''' '''
        items = el.xpath("//div[@class='page_item']")
        infos = map(lambda x: x.xpath("./table/tbody/tr/td[2]/table[@class='shopinfo']/tr"), items)
        hrefs = filter(lambda x: x, map(lambda x: NodeService.parse_shop_url(x[0]), infos))

        return hrefs

    @inlineCallbacks
    def search(self, agent, task):
        ''' 获取商铺信息列表 '''
        pages, hrefs = -1, []
        try:
            data = yield self.getContent(agent, task)
            el = lxml.etree.HTML(data)
            mc = el.xpath("//div[@class='r_sub_box']/div[@class='middle_content']/div[@class='page_content clearfix']")[0]
            pages = NodeService.parse_pages(mc)
            hrefs = NodeService.parse_items(mc)
        except Exception as msg:
            log.debug("Got Something Wrong with url: %s Error: %s" % (url, repr(msg)))

        returnValue((pages, json.dumps(hrefs)))
