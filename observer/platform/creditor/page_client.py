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
import cPickle
import urllib2

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

            reqid, task = yield self.callController('nextRequest', 'data')
            log.info('Got Task %s with reqid: %s' % (repr(task), reqid))

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
        task = cPickle.loads(task)
        #task = json.loads(task)
        tbody = task.tbody

        url = tbody.get('task')
        log.debug('Getting data with url: %s' % url)

        result = yield request(agent, url)
        returnValue((result, tbody.get('prefix')))

    @inlineCallbacks
    def search(self, agent, task):
        ''' 获取商铺信息列表 '''
        result = {}
        try:
            data, url = yield self.getContent(agent, task)
            el = lxml.etree.HTML(data)
            #mc = el.xpath("//div[@class='r_sub_box']/div[@class='middle_content']/div[@class='page_content clearfix']")[0]
            mc = el.xpath("//div[@class='r_sub_box']/div[@class='content_detail']")
            try:
                basic_info = NodeService.parse_basic_info(mc[0])
            except IndexError:
                basic_info = {}
            try:
                intro_info = NodeService.parse_intro_info(mc[1])
            except IndexError:
                intro_info = {}
            try:
                extra_info = NodeService.parse_extra_info(mc[2])
                for u in extra_info['extra']:
                    u['link'] = urllib2.urlparse.urljoin(url, u['link'])
            except IndexError:
                extra_info = {}

            result.update(basic_info)
            result.update(intro_info)
            result.update(extra_info)
        except Exception as msg:
            log.debug("Got Something Wrong with Task: %s Error: %s" % (repr(task), repr(msg)))

        returnValue(result)


    @staticmethod
    def parse_basic_info(el):
        result = {}
        try:
            result['pic'] = el.xpath('//div[@id="item"]/a/img/@src')[0]
            result['title'] = el.xpath("./div[@class='r_content']/div[@class='title']/text()")[0].encode('latin1')
        except IndexError:
            pass

        trs = el.xpath("./div[@class='r_content']/div[@class='list']/table/tr")

        keys = ['avg', 'tel', 'address', 'date', 'payload', 'best_seller']

        for i, tr in enumerate(trs):
            try:
                key = keys[i]
                if key in ['tel', 'address', 'payload', 'best_seller']:
                    result[key] = tr.xpath('./td')[1].xpath('./text()')[0].encode('latin1')
                    continue
                if key == 'date':
                    result[key] = tr.xpath('./td')[1].xpath('./text()')
                    continue
                result[key] = tr.xpath('./td/span/text()')[0].encode('latin1')
            except IndexError:
                pass

        return result

    @staticmethod
    def parse_intro_info(el):
        result = {}
        trs = el.xpath('./div[@class="list no_margintop"]/table/tr')

        keys = ['company_intro', 'preferential', 'card_detail', 'parking', 'buss']

        for i, tr in enumerate(trs):
            try:
                key = keys[i]
                if key == 'buss':
                    result[key] = tr.xpath('./td/div[@class="left"]/text()')[0].encode('latin1')
                    continue
                result[key] = tr.xpath('./td')[1].xpath('./text()')[0].encode('latin1')
            except IndexError:
                pass

        return result

    @staticmethod
    def parse_extra_info(el):
        hs = []
        hrefs = el.xpath('./div[@class="other"]/a')
        for href in hrefs:
            try:
                hs.append({'link': href.xpath('./@href')[0].encode('latin1'), 'name': href.xpath('./text()')[0].encode('latin1')})
            except IndexError:
                pass

        return {'extra': hs}
