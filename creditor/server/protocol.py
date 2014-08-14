# coding=utf8

import zlib

from twisted.protocols import basic
from heapq import heappop, heappush

from observer.utils import json_dumps, json_loads, log


class APIServerProtocol(basic.Int32StringReceiver):
    ''' '''

    MAX_LENGTH = 10 * 1024 * 1024
    COMPRESS_LEVEL = 9

    def __init__(self):
        ''' '''
        self.seq = 0
        self.waitingseq = 0
        self.pending_msgs = []

    def connectionMade(self):
        ''' '''
        self.seq = 0
        self.waitingseq = 0
        self.pending_msgs = []

    def connectionLost(self, reason):
        ''' '''
        self.factory.closeConnection(self.conn_id)

    def sendMsg(self, fseq, seq, s):
        ''' '''
        if seq > self.waitingseq:
            heappush(self.pending_msgs, (seq, fseq, s))
            return
        while seq <= self.waitingseq:
            if seq < self.waitingseq:
                log.warn("warnging: %s is smaller than %s" % (
                    seq,
                    self.waitingseq,
                ))
            self.sendString(zlib.compress(s, self.COMPRESS_LEVEL))
            self.waitingseq += 1
            if not self.pending_msgs:
                break
            if self.pending_msgs[0][0] > self.waitingseq:
                break
            seq, fseq, s = heappop(self.pending_msgs)

    def catchError(self, err, fseq, seq):
        ''' '''
        log.exception(err)

        code = -1
        msg = err.getErrorMessage()
        self.sendMsg(
            fseq,
            seq,
            json_dumps({
                'c': code,
                'error': {
                    'msg': msg,
                    'errno': getattr(err.value, 'errno', 2000),
                },
            }),
        )

    def writeValue(self, value, fseq, seq):
        ''' '''
        d = {
            'c': 0,
            'r': value,
        }

        s = json_dumps(d)
        log.info('response: %d, %d, %s' % (fseq, seq, repr(s)))
        self.sendMsg(fseq, seq, s)

    def stringReceived(self, data):
        ''' '''
        data = json_loads(zlib.decompress(data))
        fseq = self.factory.seq
        seq = self.seq
        log.info('request: %d, %d, %s' % (fseq, seq, repr(data)))
        d = self.factory.remoteCall(
            self.conn_id,
            data.get('m', None),
            *data.get('a', []),
            **data.get('k', {})
        )

        self.factory.seq += 1
        self.seq += 1
        d.addCallback(
            self.writeValue,
            fseq,
            seq,
        ).addErrback(self.catchError, fseq, seq)
