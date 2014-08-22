# coding=utf8
#
# Active Spider Controller Node
# CopyRight seraphln.
#

'''
    1. Manage the task queue
    2. Manage the clients

    TODO:
        1. abstract the redis
        2. varity the task type

'''

import time
from twisted.internet import reactor, defer
from observer.lib import log
from observer.lib.tasks import BaseTask

from observer.node.controller import ControllerServiceBase
from observer.platform.creditor.config import SEARCH_TIMEOUT, TASK_QUEUE
from observer.platform.creditor.utils import check_duplicate, save_extract_ids
from observer.platform.creditor.models import save_statuses, save_tasks
from observer.platform.creditor.base_redis import RedisOp

ttype_mapper = {
    'extract': 'extract_queue',
    'user': 'task_queue',
}


class ControllerService(ControllerServiceBase):
    ''' controller作为中心节点存在，目前负责调度以及管理 '''

    servicename = 'observer.creditor.active_spider'

    def __init__(self, *args, **kwargs):
        ''' '''
        ControllerServiceBase.__init__(self, *args, **kwargs)

        self.taskid = 0
        self.search_defers = {}
        self.redis = RedisOp()


    def startService(self):
        ''' 启动任务 '''
        ControllerServiceBase.startService(self)

        # 启动前得准备
        self.get_prepared()

    def add_test_task(self):
        ''' '''
        tid = self.new_task_id()
        tbody = {
            'page': 1,        
            'ccode': '0010',
            'prefix': 'http://pos.cmbchina.com',
            'suffix': '/Search.aspx?citycode=%s&class=&subclass=&regionid=&ccid=&keyword=&pageno=%s'
        }
        task = BaseTask(tid, tbody)
        self.redis.push_list_data('extract_queue', json.dumps(value))

    def get_prepared(self):
        ''' 爬虫中心节点启动之前的准备工作 '''

        # 打开redis连接
        self.redis.open_connection()
        self.add_test_task()

    def stopService(self):
        '''
            stop this service and write data info files
            for the next call
        '''
        pass

    def gotResult(self, data, tid, ttype):
        '''
            获取数据。任务分2种。
            1. 商铺信息，需要抓取商铺的商品列表
            2. 商品信息，需要抓取商品的基本信息
        '''
        # TODO refactor this
        if data:
            if ttype == 'extract':
                page, hrefs = json.loads(data)
                tids = check_duplicate(self.redis, data)
                save_tasks(self.redis, tids)
            else:
                save_items(data)
        else:
            log.debug('Got an invalid tid: %s when taking task: %s' % (tid, ttype))

    def sendResult(self, reqid, skid, result):
        ''' '''
        # 如果reqid不在search defers中，直接返回
        if reqid not in self.search_defers:
            return

        defer_info = self.search_defers[reqid]
        defer_info['timeout'].cancel()
        d = defer_info['defer']

        if result is None:
            d.errback(Exception("Search error"))
        else:
            d.callback(result)
        del self.search_defers[reqid]

    def nextRequest(self, ttype):
        ''' 子节点访问的方法；获取一个任务给子节点 '''
        while 1:
            now = time.time()

            try:
                _, task = self.redis.query_list_data(ttype_mapper[ttype])
            except TypeError:
                log.error("There is no task in task queue")
                _, task = None, None

            reqid = self.newRequestId()
            d = defer.Deferred()
            d.addCallback(self.gotResult,
                          task, ttype).addErrback(self.gotError, task)
            timeout = reactor.callLater(SEARCH_TIMEOUT, self.cancelSearch, reqid)
            self.search_defers[reqid] = {'timeout': timeout, 'defer': d}
            return (reqid, task)

    def cancelSearch(self, rid):
        ''' 当子节点执行任务出现异常时，调用该方法取消掉正在执行的任务 '''
        if rid in self.search_defers:
            defer_info = self.search_defers[rid]
            defer_info['defer'].errback(Exception("Timeout when waiting"))
            del self.search_defers[rid]

    def gotError(self, fail, tid):
        ''' 当出现异常时，将任务重新写入到Redis队列 '''
        log.exception(fail)
        self.redis.push_list_data(TASK_QUEUE, tid, direct='right')

    def clientFail(self, *args, **kwargs):
        ''' called when client failed '''
        clientid = kwargs.get('clientid')
        log.info("%s Client Failed, reason: %s" % (clientid,
                                                   kwargs.get('reason', '')))

